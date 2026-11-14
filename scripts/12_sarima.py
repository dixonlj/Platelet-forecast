#!/usr/bin/env python3
"""
Milestone 6, step 1: a classical statistical baseline (seasonal ARIMA).

For each training cut-off c = 31 Dec of 2010..2017, a SARIMA model with a
weekly season (period 7) is fitted only on days up to c (expanding window,
like gradient boosting). The order is picked by AIC from a small fixed grid.
The fitted parameters are then held fixed and the Kalman filter is run
forward, so the forecast from each origin day uses only data known that day.
The 1-4 day forecasts are cached to results/m6/12_sarima_forecasts_<c>.csv.

Forecasts for test year Y come from the cut-off Y-1; the safety unit for Y uses
the cut-off Y-2 on Y-1 origins, exactly as for gradient boosting (script 08).

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/12_sarima.py
"""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

import lib_m4 as L

OUT = L.PROJECT_ROOT / "results/m6"
GRID = [((1, 0, 1), (1, 1, 1, 7)), ((2, 0, 1), (1, 1, 1, 7)),
        ((0, 1, 1), (0, 1, 1, 7)), ((1, 1, 1), (0, 1, 1, 7))]


def fit_cutoff(y: pd.Series, cutoff: pd.Timestamp):
    train = y.loc[:cutoff].values.astype(float)
    best = None
    rows = []
    for order, sorder in GRID:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = SARIMAX(train, order=order, seasonal_order=sorder).fit(disp=False, maxiter=200)
        rows.append({"cutoff": cutoff.date(), "order": str(order), "seasonal": str(sorder),
                     "aic": r.aic, "converged": bool(r.mle_retvals.get("converged", True))})
        if best is None or r.aic < best[0].aic:
            best = (r, order, sorder)
    return best, rows


def forecasts_from_every_origin(res, y_full: np.ndarray, h_max: int = 4) -> np.ndarray:
    """Filter the whole series with fixed parameters; forecast 1..h_max from each origin."""
    ra = res.apply(y_full)
    Z = ra.model["design"][:, :, 0] if ra.model["design"].ndim == 3 else ra.model["design"]
    T = ra.model["transition"][:, :, 0] if ra.model["transition"].ndim == 3 else ra.model["transition"]
    c = np.ravel(ra.model["state_intercept"][:, 0] if ra.model["state_intercept"].ndim == 2 else ra.model["state_intercept"])
    d = float(np.ravel(ra.model["obs_intercept"])[0])
    a_pred = ra.predicted_state  # (k_states, nobs+1): a_{i|i-1}
    n = len(y_full)
    out = np.full((n, h_max), np.nan)
    A = a_pred[:, 1:n + 1]  # column t = a_{t+1|t}
    for h in range(h_max):
        out[:, h] = (Z @ A).ravel() + d
        A = T @ A + c[:, None]
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _, y, _ = L.load_series()
    log, sel = [], []
    for c in range(2010, 2018):
        cutoff = pd.Timestamp(f"{c}-12-31")
        t0 = time.time()
        (res, order, sorder), rows = fit_cutoff(y, cutoff)
        log += rows
        end = pd.Timestamp(f"{c + 1}-12-31")
        yf = y.loc[:end]
        fc = forecasts_from_every_origin(res, yf.values.astype(float))
        df = pd.DataFrame(np.clip(fc, 0, None), index=yf.index, columns=[1, 2, 3, 4])
        # Keep origins from 1 December of the cut-off year (simulation warm-up) onward.
        df = df.loc[pd.Timestamp(f"{c}-12-01"):]
        # Check the fast state-space forecast against statsmodels' own forecast for two origins.
        for o in (cutoff, pd.Timestamp(f"{c + 1}-06-15")):
            i = yf.index.get_loc(o)
            ref = res.apply(yf.values[: i + 1].astype(float)).forecast(4)
            assert np.allclose(np.clip(ref, 0, None), df.loc[o].values, atol=1e-6), (o, ref, df.loc[o].values)
        df.to_csv(OUT / f"12_sarima_forecasts_{c}.csv")
        sel.append({"cutoff": cutoff.date(), "order": str(order), "seasonal": str(sorder), "aic": res.aic,
                    "fit_seconds": round(time.time() - t0, 1)})
        print(f"cut-off {c}: SARIMA{order}x{sorder} AIC {res.aic:.1f} ({time.time() - t0:.0f}s)")
    pd.DataFrame(log).to_csv(OUT / "12_sarima_grid_aic.csv", index=False)
    pd.DataFrame(sel).to_csv(OUT / "12_sarima_selected.csv", index=False)


def load_sarima(c: int) -> pd.DataFrame:
    d = pd.read_csv(OUT / f"12_sarima_forecasts_{c}.csv", index_col=0, parse_dates=True)
    d.columns = [int(x) for x in d.columns]
    return d


if __name__ == "__main__":
    main()
