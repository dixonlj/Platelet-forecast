#!/usr/bin/env python3
"""
Milestone 6, step 4: how much does the assumed shelf life on arrival matter?

The public data do not record how old units were on arrival. The base case
assumes 70% of units arrive with 4 usable days and 30% with 3. Here the share
arriving with only 3 days is swept from 0% to 100% (the rest have 4 days):

  A. Reality check (script 09's hospital-like standing order, 2012-2018):
     which share brings simulated waste to the hospital's recorded waste,
     on average and in each year?
  B. Forecast comparison (script 13's four models, 2012-2018): does the
     ranking of the forecasts change with the life mix?

Same 30 paired seeds; every model matched to the hospital's short days.
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/15_life_on_arrival_sweep.py
"""
from __future__ import annotations

import importlib.util
from copy import deepcopy

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m6"
SHARES_A = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
SHARES_B = [0.0, 0.3, 0.6, 1.0]
MODELS = ["dow4", "hgbr", "chronos", "sarima"]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s09 = _load("s09", "09_reality_check.py")
s12 = _load("s12", "12_sarima.py")


def cfg_share(s3: float) -> dict:
    c = deepcopy(L.m3.BASE)
    life = {}
    if s3 < 1:
        life[4] = round(1 - s3, 6)
    if s3 > 0:
        life[3] = round(s3, 6)
    c["life_on_arrival"] = life
    return c


def main() -> None:
    df, y, _ = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c) for c in range(2010, 2018)}
    stand = s09.standing_order_fc(y)
    rows_a, rows_b = [], []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        # A. standing order
        fa = {"standing": stand}
        sig_a = L.sigma_for_year(y, fa, Y)
        win_a = {"standing": (L.m2.window_sum(stand, 2), L.m2.window_sum(stand, 4))}
        for s3 in SHARES_A:
            res = L.run_config(cfg_share(s3), y, win_a, sig_a, ["standing"], year=Y)
            m = M.match_at(res["standing"], hosp["shortage_days"], hosp["demand"])
            rows_a.append({"year": Y, "share_3day": s3, "sim_waste_pct": m["waste_pct"].mean(),
                           "sim_emergency_units": m["short_units"].mean(),
                           "hosp_waste_pct": hosp["waste_pct"], "hosp_emergency_units": hosp["short_units"]})
        # B. forecast comparison
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1].reindex(y.index)}
        fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "chronos": chron, "sarima": sar[Y - 2].reindex(y.index)}
        sigma = L.sigma_for_year(y, fcS, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcY.items()}
        for s3 in SHARES_B:
            res = L.run_config(cfg_share(s3), y, win, sigma, MODELS, year=Y)
            for k in MODELS:
                m = M.match_at(res[k], hosp["shortage_days"], hosp["demand"])
                rows_b.append({"year": Y, "share_3day": s3, "model": k, "waste_pct": m["waste_pct"].mean(),
                               "emergency_units": m["short_units"].mean(),
                               "lost_units": m["lost_units"].mean()})
        print(Y, "done")
    a = pd.DataFrame(rows_a)
    b = pd.DataFrame(rows_b)
    a.to_csv(OUT / "15_reality_life_sweep.csv", index=False)
    b.to_csv(OUT / "15_models_life_sweep.csv", index=False)

    am = a.groupby("share_3day")[["sim_waste_pct", "hosp_waste_pct", "sim_emergency_units", "hosp_emergency_units"]].mean()
    # Share that matches the mean recorded waste (linear interpolation; waste rises with the share).
    x, v = am.index.values, am["sim_waste_pct"].values
    target = am["hosp_waste_pct"].iloc[0]
    match_mean = float(np.interp(target, v, x)) if v.min() <= target <= v.max() else np.nan
    per_year = []
    for Y, g in a.groupby("year"):
        g = g.sort_values("share_3day")
        t = g["hosp_waste_pct"].iloc[0]
        vv = g["sim_waste_pct"].values
        if t < vv.min():
            sh = "below 0% (recorded waste lower than any mix)"
        elif t > vv.max():
            sh = "above 100% (needs units younger than 3 days)"
        else:
            sh = f"{100 * float(np.interp(t, vv, g['share_3day'].values)):.0f}%"
        per_year.append({"year": Y, "hosp_waste_pct": t, "sim_waste_0pct": vv[0], "sim_waste_100pct": vv[-1],
                         "matching_share_3day": sh})
    py = pd.DataFrame(per_year)
    py.to_csv(OUT / "15_matching_share_by_year.csv", index=False)

    lines = ["=== Milestone 6: life-on-arrival sweep ===",
             "A. Standing order, mean over 2012-2018:", am.round(2).to_string(),
             f"Share of 3-day units that matches the mean recorded waste ({target:.2f}%): "
             f"{100 * match_mean:.0f}%",
             py.round(2).to_string(index=False), "", "B. Forecast comparison:"]
    for s3, g in b.groupby("share_3day"):
        w = g.pivot(index="year", columns="model", values="waste_pct")
        l = g.pivot(index="year", columns="model", values="lost_units")
        lines.append(f"share 3-day {s3:.0%}: mean waste {w.mean().round(2).to_dict()}; "
                     f"GB<WA {int((w.hgbr < w.dow4).sum())}/7, SARIMA<WA {int((w.sarima < w.dow4).sum())}/7, "
                     f"CB<WA {int((w.chronos < w.dow4).sum())}/7; lost units mean {l.mean().round(0).to_dict()}; "
                     f"lost GB<WA {int((l.hgbr < l.dow4).sum())}/7, SARIMA<WA {int((l.sarima < l.dow4).sum())}/7, "
                     f"CB<WA {int((l.chronos < l.dow4).sum())}/7")
    t = "\n".join(lines)
    print(t)
    (OUT / "15_run_log.txt").write_text(t + "\n")


if __name__ == "__main__":
    main()
