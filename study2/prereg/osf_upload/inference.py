"""
Shared inference and model-fitting rules for Study 2 (pre-registration v3).

Used by nhsbt_analysis.py (and, in an older form, by the Brazil exploratory
script). This module never opens the NHSBT workbook.

Main changes from v2 (see changes_v2_to_v3.md):
- Forecasts are paired by TARGET MONTH, never by list position (N2 / R1).
- Circular moving-block bootstrap, so every month has equal weight (N11).
- Newey-West variance uses Bartlett weights (O-a). Identical at lag 0.
- Holm returns adjusted p-values as well as reject yes/no (O-b).
- The primary verdict applies the 7 units/day smallest meaningful
  difference as a separate "practically meaningful" label (N8).
- Fit failure rule matches the plan exactly, warnings are returned for
  logging, and SARIMA / state-space convergence is read from
  mle_retvals['converged'] (N5-N7).
- ETS and SARIMA are fitted ONCE per origin and forecast all horizons, so
  fallbacks are counted per origin (N12).
"""

from __future__ import annotations

import warnings
from math import isfinite

import numpy as np
from scipy.stats import t as student_t
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing as StateSpaceETS
from statsmodels.tsa.statespace.sarimax import SARIMAX

SEED = 20261118
N_BOOT = 10000
SMALLEST_MEANINGFUL_DIFF = 7.0  # platelet units per day (planning judgement, scale only)


# ---------------------------------------------------------------------------
# Pairing by target month
# ---------------------------------------------------------------------------

def align_by_target(fc_a: dict, fc_b: dict, actuals: dict, targets=None):
    """
    Join two methods' forecasts on target month.

    fc_a, fc_b: {target_month: forecast}; actuals: {target_month: actual}.
    targets: optional iterable restricting the scored target months; by
    default the pool is every month either method forecast. Only months where BOTH methods have a finite forecast and the actual is
    finite are kept. Returns (months_sorted, err_a, err_b, info) where
    err_* are absolute errors in time order, and info counts what was dropped.
    """
    pool = (set(fc_a) | set(fc_b)) if targets is None else set(targets)
    pool &= set(actuals)
    cand_a = {k for k in pool if k in fc_a}
    cand_b = {k for k in pool if k in fc_b}
    keep = sorted(
        k for k in cand_a & cand_b
        if np.isfinite(fc_a[k]) and np.isfinite(fc_b[k]) and np.isfinite(actuals[k])
    )
    y = np.array([actuals[k] for k in keep], dtype=float)
    ea = np.abs(y - np.array([fc_a[k] for k in keep], dtype=float))
    eb = np.abs(y - np.array([fc_b[k] for k in keep], dtype=float))
    info = {
        "n_pool": len(pool),
        "n_paired": len(keep),
        "n_dropped": len(pool) - len(keep),
        "missing_a": sorted(pool - cand_a),
        "missing_b": sorted(pool - cand_b),
    }
    return keep, ea, eb, info


def single_errors(fc: dict, actuals: dict, targets=None):
    """Absolute errors for one method, in time order, finite values only."""
    pool = set(actuals) if targets is None else set(targets) & set(actuals)
    keep = sorted(k for k in pool if k in fc and np.isfinite(fc[k]) and np.isfinite(actuals[k]))
    y = np.array([actuals[k] for k in keep], dtype=float)
    f = np.array([fc[k] for k in keep], dtype=float)
    return keep, y, f


# ---------------------------------------------------------------------------
# Circular moving-block bootstrap
# ---------------------------------------------------------------------------

def block_length(horizon: int) -> int:
    """3 months at the 1-month horizon; h + 2 months at horizon h."""
    if horizon <= 1:
        return 3
    return int(horizon) + 2


def circular_block_indices(n: int, length: int, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """
    Circular moving-block bootstrap indices, shape (n_boot, n).
    Blocks start anywhere in 0..n-1 and wrap around the end, so every month
    is equally likely to be drawn.
    """
    if n <= 0:
        return np.empty((n_boot, 0), dtype=int)
    L = max(1, min(int(length), n))
    n_blocks = int(np.ceil(n / L))
    starts = rng.integers(0, n, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]) % n
    return idx.reshape(n_boot, n_blocks * L)[:, :n]


def bootstrap_mean_ci(x: np.ndarray, horizon: int, n_boot: int = N_BOOT, seed: int = SEED):
    """Point mean and percentile 95% CI of x under the circular block bootstrap."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = circular_block_indices(len(x), block_length(horizon), n_boot, rng)
    stats = x[idx].mean(axis=1)
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(x.mean()), float(lo), float(hi)


def mae_ci_keyed(fc: dict, actuals: dict, horizon: int, targets=None, **kw):
    """MAE with 95% CI for one method, keyed by target month. Returns (mae, lo, hi, n)."""
    keep, y, f = single_errors(fc, actuals, targets)
    m, lo, hi = bootstrap_mean_ci(np.abs(y - f), horizon, **kw)
    return m, lo, hi, len(keep)


def mae_diff_ci_keyed(fc_a: dict, fc_b: dict, actuals: dict, horizon: int, targets=None, **kw):
    """
    Paired MAE(a) - MAE(b) on the SAME target months (joined by month).
    The same resampled months are used for both methods.
    Returns (diff, lo, hi, info).
    """
    keep, ea, eb, info = align_by_target(fc_a, fc_b, actuals, targets)
    d, lo, hi = bootstrap_mean_ci(ea - eb, horizon, **kw)
    return d, lo, hi, info


# ---------------------------------------------------------------------------
# Diebold-Mariano with HLN correction
# ---------------------------------------------------------------------------

def dm_hln_from_differential(d, horizon: int = 1, lags: int | None = None):
    """
    Diebold-Mariano test on a loss differential d (time ordered), two-sided.

    Variance: Newey-West with Bartlett weights and max(h-1, 0) lags by default
    (lag 0 at a 1-month horizon). `lags` can be set for the pre-specified
    descriptive lag-2 check. Harvey-Leybourne-Newbold (1997) small-sample
    correction, compared with t on n-1 degrees of freedom.
    A zero or negative variance -> computable False, p = nan.
    """
    d = np.asarray(d, dtype=float)
    n = int(len(d))
    out = dict(n=n, dm=float("nan"), dm_hln=float("nan"), p_value=float("nan"), computable=False)
    if n < 3:
        return out
    dbar = float(d.mean())
    q = max(int(horizon) - 1, 0) if lags is None else int(lags)
    var = float(np.mean((d - dbar) ** 2))
    for lag in range(1, q + 1):
        w = 1.0 - lag / (q + 1.0)  # Bartlett
        gamma = float(np.mean((d[lag:] - dbar) * (d[:-lag] - dbar)))
        var += 2.0 * w * gamma
    if not isfinite(var) or var <= 0:
        return out
    se = (var / n) ** 0.5
    if not isfinite(se) or se == 0:
        return out
    dm = dbar / se
    h = int(horizon)
    adj = (n + 1 - 2 * h + h * (h - 1) / n) / n
    if adj <= 0:
        return out
    dm_hln = dm * (adj ** 0.5)
    p = float(2.0 * student_t.sf(abs(dm_hln), df=n - 1))
    out.update(dm=float(dm), dm_hln=float(dm_hln), p_value=p, computable=True)
    return out


def dm_hln_keyed(fc_a: dict, fc_b: dict, actuals: dict, horizon: int, targets=None, lags=None):
    """DM-HLN on absolute-error loss, a minus b, joined by target month."""
    keep, ea, eb, info = align_by_target(fc_a, fc_b, actuals, targets)
    out = dm_hln_from_differential(ea - eb, horizon, lags=lags)
    out["pairing"] = info
    return out


# ---------------------------------------------------------------------------
# Legacy positional helpers (Brazil exploratory script). They now REFUSE to
# pair lists of different lengths instead of silently truncating.
# ---------------------------------------------------------------------------

def _finite_pairs(pairs):
    arr = np.asarray(pairs, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2 or len(arr) == 0:
        return np.empty((0, 2))
    return arr[np.isfinite(arr).all(axis=1)]


def mae(pairs) -> float:
    arr = _finite_pairs(pairs)
    return float("nan") if len(arr) == 0 else float(np.mean(np.abs(arr[:, 0] - arr[:, 1])))


def block_bootstrap_mae(pairs, horizon: int, n_boot: int = N_BOOT, seed: int = SEED):
    arr = _finite_pairs(pairs)
    return bootstrap_mean_ci(np.abs(arr[:, 0] - arr[:, 1]), horizon, n_boot=n_boot, seed=seed)


def _check_same_length(a, b):
    if len(a) != len(b):
        raise ValueError(
            "Positional pairing refused: the two forecast lists have different lengths "
            f"({len(a)} vs {len(b)}), so list positions are not the same months. "
            "Use the *_keyed functions, which join on target month."
        )


def block_bootstrap_mae_diff(pairs_a, pairs_b, horizon: int, n_boot: int = N_BOOT, seed: int = SEED):
    _check_same_length(pairs_a, pairs_b)
    a = np.asarray(pairs_a, dtype=float)
    b = np.asarray(pairs_b, dtype=float)
    mask = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    d = np.abs(a[mask, 0] - a[mask, 1]) - np.abs(b[mask, 0] - b[mask, 1])
    return bootstrap_mean_ci(d, horizon, n_boot=n_boot, seed=seed)


def diebold_mariano_hln(pairs_a, pairs_b, horizon: int = 1):
    _check_same_length(pairs_a, pairs_b)
    a = np.asarray(pairs_a, dtype=float)
    b = np.asarray(pairs_b, dtype=float)
    mask = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    d = np.abs(a[mask, 0] - a[mask, 1]) - np.abs(b[mask, 0] - b[mask, 1])
    return dm_hln_from_differential(d, horizon)


# ---------------------------------------------------------------------------
# Holm and verdicts
# ---------------------------------------------------------------------------

def holm_adjust(pvalues: dict, alpha: float = 0.05) -> dict:
    """
    Holm step-down. Non-computable (nan/None) p-values are treated as 1 and
    can never be rejected. Returns, per name: raw p, Holm-adjusted p,
    threshold, reject.
    """
    items = []
    for name, p in pvalues.items():
        p_use = 1.0 if (p is None or not isfinite(p)) else float(p)
        items.append((p_use, name, p))
    items.sort(key=lambda x: (x[0], x[1]))
    m = len(items)
    results = {}
    still_rejecting = True
    running_max = 0.0
    for i, (p_use, name, p_raw) in enumerate(items):
        thresh = alpha / (m - i)
        running_max = max(running_max, min(1.0, (m - i) * p_use))
        raw_ok = p_raw is not None and isfinite(p_raw)
        reject = still_rejecting and raw_ok and (p_use <= thresh)
        if not reject:
            still_rejecting = False
        results[name] = {
            "p": float(p_raw) if raw_ok else float("nan"),
            "p_holm": running_max,
            "threshold": thresh,
            "reject": bool(reject),
        }
    return results


def ci_excludes_zero(lo, hi) -> bool:
    return isfinite(lo) and isfinite(hi) and (hi < 0 or lo > 0)


def primary_verdict(diff, lo, hi, holm_reject: bool, computable: bool) -> str:
    """
    Confirmatory direction. A method is 'better' (or 'worse') than seasonal
    naive only if the Holm-corrected DM rejects AND the circular block-bootstrap
    CI for MAE(method) - MAE(naive) excludes zero AND both point the same way
    (the CI side fixes the direction; the DM sign is the same as the mean
    differential, which is the bootstrap point estimate).
    """
    if (not computable) or (not holm_reject) or (not ci_excludes_zero(lo, hi)):
        return "couldn't tell them apart"
    if hi < 0:
        return "lower MAE than seasonal naive (Holm-corrected test and interval agree)"
    return "higher MAE than seasonal naive (Holm-corrected test and interval agree; seasonal naive was better)"


def practical_label(verdict: str, diff, lo, hi, smd: float = SMALLEST_MEANINGFUL_DIFF) -> str:
    """
    Pre-specified practical-importance label, applied only after primary_verdict.
    - Not declared better/worse -> 'no claim'.
    - Declared, |diff| >= smd, and the whole interval is at least smd away from
      zero -> 'practically meaningful (at least 7 units/day)'.
    - Declared, |diff| >= smd, but the interval includes smaller differences
      -> 'meets 7 units/day at the point estimate, but the gain may be smaller than what matters'.
    - Declared but |diff| < smd -> 'below the 7 units/day smallest meaningful difference'.
    """
    if verdict.startswith("couldn't"):
        return "no claim"
    size = abs(diff)
    near_edge = hi if diff < 0 else lo  # interval end closest to zero
    if size >= smd and abs(near_edge) >= smd:
        return f"practically meaningful (at least {smd:g} units/day)"
    if size >= smd:
        return f"meets {smd:g} units/day at the point estimate, but the difference may be smaller than what matters"
    return f"below the {smd:g} units/day smallest meaningful difference; not practically meaningful"


def descriptive_verdict(diff, lo, hi, p, computable: bool) -> str:
    """Descriptive only: no 'better' or 'significant' wording."""
    if (not computable) or (p is None or not isfinite(p) or p >= 0.05) or (not ci_excludes_zero(lo, hi)):
        return "descriptive only; couldn't tell them apart"
    return "descriptive only; interval and unadjusted test point the same way, no confirmatory claim"


# ---------------------------------------------------------------------------
# Fit failure rule (identical wording in plan v3, 'Failure rule')
# ---------------------------------------------------------------------------

def warning_is_failure(category, message: str) -> bool:
    """
    A captured warning counts as a fit failure if:
      (a) its category is statsmodels ConvergenceWarning (or a subclass), or
      (b) its message contains 'converge' (case-insensitive), or
      (c) its message contains both 'failed to' and 'optim' (case-insensitive).
    """
    msg = str(message).lower()
    try:
        if issubclass(category, ConvergenceWarning):
            return True
    except TypeError:
        pass
    if "converge" in msg:
        return True
    if "failed to" in msg and "optim" in msg:
        return True
    return False


def _capture(caught, label):
    return [
        {"spec": label, "category": w.category.__name__, "message": str(w.message),
         "counts_as_failure": warning_is_failure(w.category, str(w.message))}
        for w in caught
    ]


def fit_ets_primary(train, horizon: int):
    """
    Primary ETS: no trend, additive season (period 12), initial values
    estimated, SSE fit (holtwinters.ExponentialSmoothing.fit(optimized=True)).
    Fitted once; returns forecasts for steps 1..horizon.
    Failure = exception, OR a failure warning (warning_is_failure), OR a
    non-finite forecast. Returns (fc or None, logs).
    """
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = ExponentialSmoothing(
                np.asarray(train, dtype=float),
                trend=None, seasonal="add", seasonal_periods=12,
                initialization_method="estimated",
            )
            fit = model.fit(optimized=True, remove_bias=False)
            fc = np.asarray(fit.forecast(horizon), dtype=float)
        logs = _capture(caught, "ets_holtwinters")
    except Exception as exc:  # noqa: BLE001
        return None, [{"spec": "ets_holtwinters", "category": "Exception", "message": repr(exc), "counts_as_failure": True}]
    failed = any(l["counts_as_failure"] for l in logs) or not np.all(np.isfinite(fc))
    if not np.all(np.isfinite(fc)):
        logs.append({"spec": "ets_holtwinters", "category": "NonFiniteForecast", "message": "", "counts_as_failure": True})
    return (None if failed else fc), logs


def fit_ets_statespace_missing(train, horizon: int):
    """
    COVID-sensitivity ETS only: the state-space ETS (no trend, additive
    season of period 12), which accepts missing months (NaN).
    Same failure rule, plus mle_retvals['converged'] is False.
    """
    label = "ets_statespace"
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = StateSpaceETS(
                np.asarray(train, dtype=float), trend=False, seasonal=12,
                damped_trend=False, initialization_method="estimated",
            )
            fit = model.fit(disp=False)
            fc = np.asarray(fit.forecast(horizon), dtype=float)
        logs = _capture(caught, label)
    except Exception as exc:  # noqa: BLE001
        return None, [{"spec": label, "category": "Exception", "message": repr(exc), "counts_as_failure": True}]
    ret = getattr(fit, "mle_retvals", None)
    if isinstance(ret, dict) and ret.get("converged") is False:
        logs.append({"spec": label, "category": "mle_retvals", "message": "converged=False", "counts_as_failure": True})
    if not np.all(np.isfinite(fc)):
        logs.append({"spec": label, "category": "NonFiniteForecast", "message": "", "counts_as_failure": True})
    failed = any(l["counts_as_failure"] for l in logs)
    return (None if failed else fc), logs


SARIMA_SPECS = (
    ("primary", (0, 1, 1), (0, 1, 1, 12), None),
    ("fallback", (1, 0, 1), (1, 0, 1, 12), "c"),
)


def fit_sarima_primary(train, horizon: int):
    """
    Primary (0,1,1)(0,1,1,12), no constant. If it fails at an origin, the
    only fallback is (1,0,1)(1,0,1,12) with a constant (trend='c').
    Fitted once per origin; returns forecasts for steps 1..horizon.
    Accepts NaN (missing) observations.
    Failure = exception, OR a failure warning (warning_is_failure), OR
    mle_retvals['converged'] is False, OR a non-finite forecast.
    Returns (fc or None, label, spec, logs). label in {'primary','fallback','failed'}.
    """
    all_logs = []
    for label, order, seasonal, trend in SARIMA_SPECS:
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model = SARIMAX(
                    np.asarray(train, dtype=float), order=order, seasonal_order=seasonal,
                    trend=trend, enforce_stationarity=False, enforce_invertibility=False,
                )
                fit = model.fit(disp=False, maxiter=200)
                fc = np.asarray(fit.forecast(horizon), dtype=float)
            logs = _capture(caught, f"sarima_{label}")
        except Exception as exc:  # noqa: BLE001
            all_logs.append({"spec": f"sarima_{label}", "category": "Exception", "message": repr(exc), "counts_as_failure": True})
            continue
        ret = getattr(fit, "mle_retvals", None)
        if isinstance(ret, dict) and ret.get("converged") is False:
            logs.append({"spec": f"sarima_{label}", "category": "mle_retvals", "message": "converged=False", "counts_as_failure": True})
        if not np.all(np.isfinite(fc)):
            logs.append({"spec": f"sarima_{label}", "category": "NonFiniteForecast", "message": "", "counts_as_failure": True})
        all_logs.extend(logs)
        if not any(l["counts_as_failure"] for l in logs):
            return fc, label, (order, seasonal, trend), all_logs
    return None, "failed", None, all_logs


def fit_sarima_on_array(train, horizon: int):
    """Same SARIMA primary/fallback rule; NaN observations are allowed."""
    return fit_sarima_primary(train, horizon)


def seasonal_naive_forecast(history, h: int) -> float:
    """yhat_{t+h} = y_{t+h-12}; history is y_1..y_t (units per day)."""
    idx = len(history) - 12 + (h - 1)
    if idx < 0 or idx >= len(history):
        return float("nan")
    return float(history[idx])
