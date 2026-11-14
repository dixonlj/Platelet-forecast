#!/usr/bin/env python3
"""
Milestone 9, step 4 (draft v6): numbers the referee asked for, from existing results (no new simulation).
  29_lost_decomposition.csv  per-year split of each forecast's lost-unit gap (vs the weekday average)
                             into wasted units and emergency units, at the hospital's short days
  29_target_tests.csv        year-level tests vs the weekday average at the hospital's short days,
                             at 20 and at 50 short days (waste and lost units), all forecasts
  29_power.csv               spread of the 7 yearly waste gaps and the smallest gap a paired t-test
                             on 7 years would detect with 80% power (two-sided 5%)
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/29_v6_numbers.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
from scipy import stats

import lib_m4 as L

P = L.PROJECT_ROOT
OUT = P / "results/m9"
spec = importlib.util.spec_from_file_location("s20", P / "scripts/20_horizon_accuracy_and_stats.py")
s20 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s20)
MODELS = ["hgbr", "gbdt", "chronos", "sarima", "lasso", "rnn"]


def load() -> pd.DataFrame:
    a = pd.read_csv(OUT / "27_multiyear_inventory.csv")
    b = pd.read_csv(P / "results/m5/08_multiyear_inventory.csv").query("model in ['lasso', 'rnn']")
    b = b[["year", "target", "target_short_days", "model", "waste_pct_mean", "waste_units_mean",
           "emergency_units_mean", "wasted_plus_emergency_mean", "demand"]]
    return pd.concat([a, b], ignore_index=True)


def main() -> None:
    inv = load()
    rows = []
    h = inv[inv.target == "hospital"]
    wu = h.pivot(index="year", columns="model", values="waste_units_mean")
    eu = h.pivot(index="year", columns="model", values="emergency_units_mean")
    for m in MODELS:
        dw, de = wu[m] - wu.dow4, eu[m] - eu.dow4
        for Y in wu.index:
            rows.append({"model": m, "year": Y, "waste_unit_gap": dw[Y], "emergency_unit_gap": de[Y],
                         "lost_unit_gap": dw[Y] + de[Y]})
        rows.append({"model": m, "year": "mean", "waste_unit_gap": dw.mean(), "emergency_unit_gap": de.mean(),
                     "lost_unit_gap": dw.mean() + de.mean(),
                     "share_of_lost_gap_from_waste": dw.mean() / (dw.mean() + de.mean()),
                     "years_fewer_waste_units": int((dw < 0).sum()), "years_fewer_emergency_units": int((de < 0).sum())})
    dec = pd.DataFrame(rows); dec.to_csv(OUT / "29_lost_decomposition.csv", index=False)

    tests = []
    for t, g in inv.groupby("target", sort=False):
        for outcome, col in (("Waste (points)", "waste_pct_mean"), ("Wasted + emergency units a year", "wasted_plus_emergency_mean")):
            pv = g.pivot(index="year", columns="model", values=col)
            for m in MODELS:
                tests.append({"target": t, "short_days": "recorded (21-42)" if t == "hospital" else t.replace("fixed", ""),
                              "outcome": outcome, "model": m, "mean_model": pv[m].mean(), "mean_weekday_average": pv.dow4.mean(),
                              **s20.year_tests((pv[m] - pv.dow4).values)})
    tests = pd.DataFrame(tests); tests.to_csv(OUT / "29_target_tests.csv", index=False)

    pw = []
    w = h.pivot(index="year", columns="model", values="waste_pct_mean")
    tc, tp = stats.t.ppf(0.975, 6), stats.t.ppf(0.80, 6)
    for m in MODELS:
        d = (w[m] - w.dow4).values
        sd = d.std(ddof=1)
        pw.append({"model": m, "sd_of_yearly_waste_gap": sd, "ci_half_width": tc * sd / np.sqrt(7),
                   "approx_min_detectable_gap_80pct": (tc + tp) * sd / np.sqrt(7)})
    pw = pd.DataFrame(pw); pw.to_csv(OUT / "29_power.csv", index=False)
    txt = "\n".join(["=== Milestone 9 step 4: decomposition, target tests, power ===",
                     dec[dec.year == "mean"].round(3).to_string(index=False),
                     dec[dec.model.isin(["chronos", "sarima"])].round(1).to_string(index=False),
                     tests.round(4).to_string(index=False), pw.round(3).to_string(index=False)])
    print(txt); (OUT / "29_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
