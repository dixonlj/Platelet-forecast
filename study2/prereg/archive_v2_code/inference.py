"""
Shared inference and model-fitting rules for Study 2.

Used by the Brazil exploratory script and by the (as yet un-run) NHSBT
analysis script. Do not import or load the NHSBT workbook from here.
"""

from __future__ import annotations

import warnings
from collections import Counter
from math import isfinite

import numpy as np
from scipy.stats import t as student_t
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

SEED = 20261118
N_BOOT = 10000

# Block length: 3 months at the 1-month horizon; h + 2 months at horizon h.
def block_length(horizon: int) -> int:
    if horizon <= 1:
        return 3
    return int(horizon) + 2


def moving_block_indices(n: int, length: int, rng: np.random.Generator) -> np.ndarray:
    """Non-circular overlapping moving-block bootstrap indices of length n."""
    if n <= 0:
        return np.array([], dtype=int)
    L = max(1, min(int(length), n))
    n_starts = n - L + 1
    n_blocks = int(np.ceil(n / L))
    starts = rng.integers(0, n_starts, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + L) for s in starts])
    return idx[:n]


def _finite_pairs(pairs):
    arr = np.asarray(pairs, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2 or len(arr) == 0:
        return np.empty((0, 2))
    mask = np.isfinite(arr).all(axis=1)
    return arr[mask]


def mae(pairs) -> float:
    arr = _finite_pairs(pairs)
    if len(arr) == 0:
        return float("nan")
    return float(np.mean(np.abs(arr[:, 0] - arr[:, 1])))


def block_bootstrap_mae(pairs, horizon: int, n_boot: int = N_BOOT, seed: int = SEED):
    """Point MAE and 95% moving-block bootstrap CI. Returns (mae, lo, hi)."""
    arr = _finite_pairs(pairs)
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    point = float(np.mean(np.abs(arr[:, 0] - arr[:, 1])))
    rng = np.random.default_rng(seed)
    L = block_length(horizon)
    stats = np.empty(n_boot)
    n = len(arr)
    abs_err = np.abs(arr[:, 0] - arr[:, 1])
    for i in range(n_boot):
        idx = moving_block_indices(n, L, rng)
        stats[i] = abs_err[idx].mean()
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return point, float(lo), float(hi)


def block_bootstrap_mae_diff(pairs_a, pairs_b, horizon: int, n_boot: int = N_BOOT, seed: int = SEED):
    """Paired difference MAE(a) - MAE(b), same resampled target months."""
    a = np.asarray(pairs_a, dtype=float)
    b = np.asarray(pairs_b, dtype=float)
    n_use = min(len(a), len(b))
    a, b = a[:n_use], b[:n_use]
    mask = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    a, b = a[mask], b[mask]
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    err_a = np.abs(a[:, 0] - a[:, 1])
    err_b = np.abs(b[:, 0] - b[:, 1])
    point = float(err_a.mean() - err_b.mean())
    rng = np.random.default_rng(seed)
    L = block_length(horizon)
    stats = np.empty(n_boot)
    n = len(a)
    for i in range(n_boot):
        idx = moving_block_indices(n, L, rng)
        stats[i] = err_a[idx].mean() - err_b[idx].mean()
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return point, float(lo), float(hi)


def diebold_mariano_hln(pairs_a, pairs_b, horizon: int = 1):
    """
    Diebold–Mariano test on absolute-error loss, two-sided.

    Newey–West variance with max(h-1, 0) lags (lag 0 at a 1-month horizon).
    Harvey–Leybourne–Newbold (1997) small-sample correction, compared with
    a t distribution on n-1 degrees of freedom.

    Returns dict with n, dm, dm_hln, p_value, computable.
    If the variance estimate is zero or negative, computable is False
    and p_value is nan (treat as 'could not tell apart').
    """
    a = np.asarray(pairs_a, dtype=float)
    b = np.asarray(pairs_b, dtype=float)
    n_use = min(len(a), len(b))
    a, b = a[:n_use], b[:n_use]
    mask = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    d = np.abs(a[mask, 0] - a[mask, 1]) - np.abs(b[mask, 0] - b[mask, 1])
    n = int(len(d))
    out = dict(n=n, dm=float("nan"), dm_hln=float("nan"), p_value=float("nan"), computable=False)
    if n < 3:
        return out
    dbar = float(d.mean())
    # Newey–West, lags = h-1
    lags = max(int(horizon) - 1, 0)
    gamma0 = float(np.mean((d - dbar) ** 2))
    var = gamma0
    for lag in range(1, lags + 1):
        gamma = float(np.mean((d[lag:] - dbar) * (d[:-lag] - dbar)))
        var += 2.0 * gamma
    if not isfinite(var) or var <= 0:
        return out
    se = (var / n) ** 0.5
    if not isfinite(se) or se == 0:
        return out
    dm = dbar / se
    h = int(horizon)
    # Harvey, Leybourne and Newbold (1997), International Journal of Forecasting
    adj = (n + 1 - 2 * h + h * (h - 1) / n) / n
    if adj <= 0:
        return out
    dm_hln = dm * (adj ** 0.5)
    p = float(2.0 * student_t.sf(abs(dm_hln), df=n - 1))
    out.update(dm=float(dm), dm_hln=float(dm_hln), p_value=p, computable=True)
    return out


def holm_adjust(pvalues: dict, alpha: float = 0.05) -> dict:
    """Holm step-down adjustment. Non-computable p-values are treated as 1."""
    items = []
    for name, p in pvalues.items():
        p_use = 1.0 if (p is None or not isfinite(p)) else float(p)
        items.append((p_use, name, p))
    items.sort(key=lambda x: (x[0], x[1]))
    m = len(items)
    results = {}
    still_rejecting = True
    for i, (p_use, name, p_raw) in enumerate(items):
        thresh = alpha / (m - i)
        reject = still_rejecting and isfinite(p_use) and (p_use <= thresh) and (p_raw is not None and isfinite(p_raw))
        if not reject:
            still_rejecting = False
        results[name] = {
            "p": p_raw if p_raw is not None else float("nan"),
            "p_for_holm": p_use,
            "threshold": thresh,
            "reject": reject,
        }
    return results


def ci_excludes_zero(lo, hi) -> bool:
    return isfinite(lo) and isfinite(hi) and (hi < 0 or lo > 0)


def primary_verdict(diff, lo, hi, holm_reject: bool, computable: bool) -> str:
    """Winner only if Holm-corrected DM rejects AND the block-bootstrap CI excludes 0."""
    if (not computable) or (not holm_reject) or (not ci_excludes_zero(lo, hi)):
        return "couldn't tell them apart"
    if diff < 0:
        return "lower MAE than seasonal naive (Holm-corrected test and interval agree)"
    return "higher MAE than seasonal naive (Holm-corrected test and interval agree; seasonal naive was better)"


def descriptive_verdict(diff, lo, hi, p, computable: bool) -> str:
    """Descriptive only: no 'better' or 'significant' wording."""
    if (not computable) or (p is None or not isfinite(p) or p >= 0.05) or (not ci_excludes_zero(lo, hi)):
        return "descriptive only; couldn't tell them apart"
    return "descriptive only; interval and unadjusted test point the same way, no confirmatory claim"


def _warnings_show_convergence(caught) -> bool:
    for w in caught:
        msg = str(w.message).lower()
        if issubclass(w.category, ConvergenceWarning):
            return True
        if "converge" in msg or "convergence" in msg:
            return True
        if "failed to" in msg and "optim" in msg:
            return True
    return False


def fit_ets_primary(train, horizon: int):
    """
    ETS as pre-specified: no trend (level + additive season only),
    additive season of period 12, initial values estimated,
    fitted by minimising the sum of squared errors
    (statsmodels.tsa.holtwinters.ExponentialSmoothing.fit(optimized=True)).

    Failure = exception, OR a convergence warning, OR a non-finite forecast.
    On failure, return None (that origin is omitted for ETS; no fallback form).
    Warnings are returned so they can be logged, not silenced.
    """
    logged = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = ExponentialSmoothing(
                np.asarray(train, dtype=float),
                trend=None,
                seasonal="add",
                seasonal_periods=12,
                initialization_method="estimated",
            )
            fit = model.fit(optimized=True, remove_bias=False)
            fc = np.asarray(fit.forecast(horizon), dtype=float)
            logged = [(w.category.__name__, str(w.message)) for w in caught]
            failed = _warnings_show_convergence(caught) or (not np.all(np.isfinite(fc)))
    except Exception as exc:  # noqa: BLE001
        return None, [("Exception", repr(exc))]
    if failed:
        return None, logged
    return fc, logged


def fit_sarima_primary(train, horizon: int):
    """
    Primary order (0,1,1)(0,1,1,12) with no constant.
    Fallback, used only at a failed origin: (1,0,1)(1,0,1,12) with a constant
    (trend='c'), because that specification has no differencing and would
    otherwise forecast toward zero.

    Failure = exception, OR a statsmodels ConvergenceWarning (or a warning
    whose message mentions convergence), OR a non-finite forecast, OR
    mle_retvals['success'] is False when that dict is present.

    The fallback, if used, applies only to that origin. Warnings are logged,
    not silenced.
    """
    specs = [
        ("primary", (0, 1, 1), (0, 1, 1, 12), None),
        ("fallback", (1, 0, 1), (1, 0, 1, 12), "c"),
    ]
    all_logs = []
    for label, order, seasonal, trend in specs:
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model = SARIMAX(
                    np.asarray(train, dtype=float),
                    order=order,
                    seasonal_order=seasonal,
                    trend=trend,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                fit = model.fit(disp=False, maxiter=200)
                fc = np.asarray(fit.forecast(horizon), dtype=float)
                logs = [(label, w.category.__name__, str(w.message)) for w in caught]
                all_logs.extend(logs)
                failed = _warnings_show_convergence(caught) or (not np.all(np.isfinite(fc)))
                ret = getattr(fit, "mle_retvals", None)
                if isinstance(ret, dict) and ret.get("success") is False:
                    failed = True
                    all_logs.append((label, "mle_retvals", "success=False"))
        except Exception as exc:  # noqa: BLE001
            all_logs.append((label, "Exception", repr(exc)))
            continue
        if not failed:
            return fc, label, (order, seasonal, trend), all_logs
    return None, "failed", None, all_logs


def seasonal_naive_forecast(history, h: int) -> float:
    """yhat_{t+h} = y_{t+h-12}, history is y_1..y_t (units per day)."""
    idx = len(history) - 12 + (h - 1)
    if idx < 0 or idx >= len(history):
        return float("nan")
    return float(history[idx])


def fit_sarima_on_array(train, horizon: int):
    """Same SARIMA primary/fallback rule, allowing NaN (missing) observations."""
    return fit_sarima_primary(train, horizon)
