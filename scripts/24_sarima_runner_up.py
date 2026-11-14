#!/usr/bin/env python3
"""
Milestone 8, step 4: does the choice between the two near-tied SARIMA orders matter?

At every cut-off the two best AIC candidates, (1,0,1)(1,1,1)7 and (2,0,1)(1,1,1)7,
are within about 2 AIC points (results/m6/12_sarima_grid_aic.csv). This script
fits the runner-up order on the same training data (up to 31 Dec of Y-1),
filters it forward with fixed parameters exactly as script 12 does, and compares
1-, 2- and 4-day MAE in each test year 2012-2018 with the selected order.
Accuracy only (no inventory run).

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python scripts/24_sarima_runner_up.py
"""
from __future__ import annotations

import ast
import importlib.util
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

import lib_m4 as L

P = L.PROJECT_ROOT
OUT = P / "results/m8"
spec = importlib.util.spec_from_file_location("s12", P / "scripts" / "12_sarima.py")
s12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s12)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _, y, _ = L.load_series()
    grid = pd.read_csv(P / "results/m6/12_sarima_grid_aic.csv")
    act = {1: y.shift(-1), 2: L.m2.actual_window_sum(y, 2), 4: L.m2.actual_window_sum(y, 4)}
    rows = []
    for c in range(2011, 2018):
        Y = c + 1
        g = grid[grid.cutoff == f"{c}-12-31"].sort_values("aic")
        sel, run = g.iloc[0], g.iloc[1]
        train = y.loc[:pd.Timestamp(f"{c}-12-31")].values.astype(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = SARIMAX(train, order=ast.literal_eval(run.order),
                          seasonal_order=ast.literal_eval(run.seasonal)).fit(disp=False, maxiter=200)
        yf = y.loc[:pd.Timestamp(f"{Y}-12-31")]
        fc_run = pd.DataFrame(np.clip(s12.forecasts_from_every_origin(res, yf.values.astype(float)), 0, None),
                              index=yf.index, columns=[1, 2, 3, 4])
        fc_sel = s12.load_sarima(c)
        orig = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        for n in (1, 2, 4):
            out = {}
            for name, fc in (("selected", fc_sel), ("runner_up", fc_run)):
                f = fc.loc[orig, 1] if n == 1 else L.m2.window_sum(fc, n).reindex(orig)
                out[name] = float(np.nanmean(np.abs(act[n][orig] - f)))
            rows.append({"test_year": Y, "horizon_days": n, "selected_order": sel.order,
                         "runner_up_order": run.order, "aic_gap": run.aic - sel.aic,
                         "mae_selected": out["selected"], "mae_runner_up": out["runner_up"],
                         "difference": out["runner_up"] - out["selected"]})
        print(Y, "done", flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "24_sarima_runner_up.csv", index=False)
    s = d.groupby("horizon_days")[["mae_selected", "mae_runner_up", "difference"]].mean()
    s["max_abs_difference"] = d.groupby("horizon_days").difference.apply(lambda x: x.abs().max())
    txt = ("=== SARIMA runner-up order: test-year MAE (2012-2018) ===\n" + d.round(4).to_string(index=False)
           + "\n\nMeans by horizon:\n" + s.round(4).to_string())
    print(txt)
    (OUT / "24_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
