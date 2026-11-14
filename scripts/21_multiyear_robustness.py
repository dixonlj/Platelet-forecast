#!/usr/bin/env python3
"""
Milestone 8, step 3: is the 7-year forecast comparison robust to the other
simulation assumptions? (Second internal review, M6.)

Reruns the 2012-2018 comparison of scripts 08/13 (all forecasts matched to the
hospital's recorded short days, 30 paired seeds) under one change at a time:
  a. no blood groups (pooled stock)
  b. patient episodes averaging 2 units (lumpier demand by group)
  c. heavy delivery shortfalls (25% of delivery days, 30-80% filled)
  d. 43% of units arriving with 3 usable days (the share that reproduced the
     hospital's average recorded waste in script 15), instead of 30%
Reports per year and model: waste %, emergency units, wasted + emergency units,
and "years better than the weekday average" with the mean yearly gap.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python scripts/21_multiyear_robustness.py
"""
from __future__ import annotations

import importlib.util
from copy import deepcopy

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m8"
MODELS = ["dow4", "hgbr", "chronos", "sarima", "lasso", "rnn"]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s12 = _load("s12", "12_sarima.py")
s19 = _load("s19", "19_prior_year_cushion.py")


def scenarios() -> dict:
    b = L.m3.BASE
    out = {"Base case (as in the main analysis)": {}}
    out["No blood groups (pooled stock)"] = {"pooled": True}
    out["Patient episodes, mean 2 units"] = {"demand_split": "episodes", "episode_mean_units": 2.0}
    out["Heavy shortfalls (25% of days, 30-80% filled)"] = {"shortfall_day_prob": 0.25, "shortfall_fill_range": (0.3, 0.8)}
    out["43% arrive with 3 days (calibrated share)"] = {"life_on_arrival": {4: 0.57, 3: 0.43}}
    return {k: {**deepcopy(b), **v} for k, v in out.items()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2010, 2018)}
    act2 = L.m2.actual_window_sum(y, 2)
    rows = []
    for name, cfg in scenarios().items():
        for Y in M.YEARS:
            prev = Y - 1
            fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "chronos": chron, "sarima": sar[Y - 2]}
            fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
            sigma = L.sigma_for_year(y, fcS, Y)
            o_prev = y.loc[pd.Timestamp(f"{prev - 1}-12-31"):pd.Timestamp(f"{prev}-12-30")].index
            for a in ("lasso", "rnn"):
                sigma[a] = L.m2.mae(act2[o_prev], authors[f"{a}2"][o_prev])
            _, e0, e1 = L.year_window(Y)
            hosp = L.hospital_actual(df, e0, e1)
            res = L.run_config(cfg, y, s19.windows(fcY, authors), sigma, MODELS, year=Y)
            mt = {m: M.match_at(res[m], hosp["shortage_days"], hosp["demand"]) for m in MODELS}
            for m in MODELS:
                rows.append({"scenario": name, "year": Y, "model": m,
                             "waste_pct_mean": mt[m]["waste_pct"].mean(),
                             "emergency_units_mean": mt[m]["short_units"].mean(),
                             "wasted_plus_emergency_mean": mt[m]["lost_units"].mean(),
                             "n_seeds_matched": int(mt[m]["waste_pct"].notna().sum())})
            print(name, Y, "done", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_multiyear_robustness.csv", index=False)

    # Check: the base case must reproduce scripts 08/13.
    ref = pd.concat([pd.read_csv(P / "results/m5/08_multiyear_inventory.csv"),
                     pd.read_csv(P / "results/m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
    ref = ref[ref.target == "hospital"][["year", "model", "waste_pct_mean"]]
    chk = out[out.scenario.str.startswith("Base")].merge(ref, on=["year", "model"], suffixes=("", "_ref"))
    maxdiff = float(np.abs(chk["waste_pct_mean"] - chk["waste_pct_mean_ref"]).max())

    summ = []
    for name, g in out.groupby("scenario", sort=False):
        w = g.pivot(index="year", columns="model", values="waste_pct_mean")
        l = g.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
        for m in MODELS:
            summ.append({"scenario": name, "model": m, "mean_waste_pct": w[m].mean(),
                         "mean_lost_units": l[m].mean(),
                         "years_less_waste_than_wa": int((w[m] < w.dow4).sum()) if m != "dow4" else np.nan,
                         "mean_waste_gap_pts": (w[m] - w.dow4).mean() if m != "dow4" else np.nan,
                         "years_fewer_lost_than_wa": int((l[m] < l.dow4).sum()) if m != "dow4" else np.nan,
                         "mean_lost_gap_units": (l[m] - l.dow4).mean() if m != "dow4" else np.nan,
                         "min_seeds_matched": int(g[g.model == m].n_seeds_matched.min())})
    summ = pd.DataFrame(summ)
    summ.to_csv(OUT / "21_robustness_summary.csv", index=False)
    txt = "\n".join(["=== Milestone 8 step 3: 7-year comparison under other assumptions ===",
                     f"base-case check vs scripts 08/13: max |waste diff| = {maxdiff:.2e} ({len(chk)} rows)",
                     summ.round(2).to_string(index=False)])
    print(txt)
    (OUT / "21_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
