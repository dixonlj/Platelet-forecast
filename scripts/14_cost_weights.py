#!/usr/bin/env python3
"""
Milestone 6, step 3: a cost-weighted outcome.

The paper counts wasted and emergency units with equal weight. Real costs
differ: an emergency unit usually costs a unit price plus courier and staff
time, and a delayed transfusion has a clinical cost that money does not
capture. Unit prices are not in the public data, so we do not pick one weight.
Instead we vary w = (cost of one emergency unit) / (cost of one wasted unit)
over 0, 0.5, 1, 2, 3, 5 and 10 and score

    weighted lost units = wasted units + w x emergency units.

Two views, both with the same 30 paired seeds as script 08/13:
  A. "matched": every model at the hospital's own short days (as in the paper).
  B. "best cushion": for each model, seed and w, the cushion k with the lowest
     weighted lost units in the test year. This is an oracle choice (it uses
     the test year), applied equally to every model, so it shows the best each
     forecast could do under that weight, not what a hospital would achieve.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/14_cost_weights.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m6"
WEIGHTS = [0, 0.5, 1, 2, 3, 5, 10]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s12 = _load("s12", "12_sarima.py")
MODELS = ["dow4", "hgbr", "chronos", "sarima", "lasso", "rnn"]


def main() -> None:
    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c) for c in range(2010, 2018)}
    rows = []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1].reindex(y.index)}
        fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "chronos": chron, "sarima": sar[Y - 2].reindex(y.index)}
        sigma = L.sigma_for_year(y, fcS, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcY.items()}
        o_prev = y.loc[pd.Timestamp(f"{Y - 2}-12-31"):pd.Timestamp(f"{Y - 1}-12-30")].index
        act2 = L.m2.actual_window_sum(y, 2)
        for a in ("lasso", "rnn"):
            win[a] = (authors[f"{a}2"], authors[f"{a}4"])
            sigma[a] = L.m2.mae(act2[o_prev], authors[f"{a}2"][o_prev])
        res = L.run_config(L.m3.BASE, y, win, sigma, MODELS, year=Y)
        for k in MODELS:
            m = M.match_at(res[k], hosp["shortage_days"], hosp["demand"])
            WU = res[k]["waste_pct"] * hosp["demand"] / 100
            SU = res[k]["short_units"]
            for w in WEIGHTS:
                matched = m["waste_units"] + w * m["short_units"]
                best = np.nanmin(WU + w * SU, axis=1)
                for s in range(len(best)):
                    rows.append({"year": Y, "model": k, "w": w, "seed": 1000 + s,
                                 "matched": matched.iloc[s], "best_cushion": best[s]})
        print(Y, "done")
    ps = pd.DataFrame(rows)
    ps.to_csv(OUT / "14_cost_per_seed.csv", index=False)
    yr = ps.groupby(["year", "model", "w"])[["matched", "best_cushion"]].mean().reset_index()
    yr.to_csv(OUT / "14_cost_by_year.csv", index=False)
    summ = []
    for view in ("matched", "best_cushion"):
        for w in WEIGHTS:
            g = yr[yr.w == w].pivot(index="year", columns="model", values=view)
            best_by_year = g.idxmin(axis=1)
            for k in MODELS:
                summ.append({"view": view, "w": w, "model": k, "mean_per_year": g[k].mean(),
                             "gap_vs_dow4_per_year": (g[k] - g["dow4"]).mean(),
                             "years_better_than_dow4": int((g[k] < g["dow4"]).sum()) if k != "dow4" else np.nan,
                             "years_lowest_of_all": int((best_by_year == k).sum())})
    sm = pd.DataFrame(summ)
    sm.to_csv(OUT / "14_cost_summary.csv", index=False)
    txt = ["=== Milestone 6: cost-weighted outcome (w = emergency unit cost / wasted unit cost) ==="]
    for view in ("matched", "best_cushion"):
        txt.append(f"-- view: {view} --")
        txt.append(sm[sm.view == view].pivot(index="w", columns="model", values="years_better_than_dow4").to_string())
        txt.append("gap vs weekday average (units per year, negative = better):")
        txt.append(sm[sm.view == view].pivot(index="w", columns="model", values="gap_vs_dow4_per_year").round(1).to_string())
        txt.append("years lowest of all six:")
        txt.append(sm[sm.view == view].pivot(index="w", columns="model", values="years_lowest_of_all").to_string())
    t = "\n".join(txt)
    print(t)
    (OUT / "14_run_log.txt").write_text(t + "\n")


if __name__ == "__main__":
    main()
