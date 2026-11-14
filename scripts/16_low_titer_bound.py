#!/usr/bin/env python3
"""
Milestone 6, step 5: a bound on the effect of US titer limits for group O platelets.

In the US scenario (scripts 07 and 10), group O units go to non-O patients as
the last step before an emergency purchase, and every O unit may be used that
way. Many US services allow this only for low-titer group O units (or after
volume reduction), and the share of O units that are low titer varies by
supplier. That share is not public for any hospital, so instead of guessing
it we run the two ends:
  * "every O unit allowed"  (script 10's assumption, upper end of O use)
  * "no O unit allowed"     (O units only for O patients: worst case)
The real effect of a titer limit lies between these two.

2018 Aachen demand, all three US changes, German calendar and daily
deliveries, same 30 seeds, matched to 31 short days.
Educational / advisory only. Still German demand, not a US hospital.
Run: PYTHONPATH=scripts .venv/bin/python scripts/16_low_titer_bound.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m6"
YEAR = 2018
MODELS = ["dow4", "hgbr"]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s10 = _load("s10", "10_us_one_change.py")
_orig_list = L.us_donor_list


def no_o_list(recipient, protected):
    return [(d, t) for d, t in _orig_list(recipient, protected) if t != "abo_o_last"]


def interp_at(res_model, key, target):
    """Interpolate an extra result array (e.g. a substitution count) at the matched cushion."""
    SD, X = res_model["shortage_days"], res_model[key]
    out = []
    for s in range(SD.shape[0]):
        idx = np.where(SD[s] <= target)[0]
        if not len(idx):
            out.append(np.nan); continue
        j = idx[0]
        if j == 0 or SD[s, j - 1] == SD[s, j]:
            out.append(X[s, j])
        else:
            f = (SD[s, j - 1] - target) / (SD[s, j - 1] - SD[s, j])
            out.append(X[s, j - 1] + f * (X[s, j] - X[s, j - 1]))
    return np.array(out)


def main() -> None:
    df, y, _ = L.load_series()
    _, ev0, ev1 = L.year_window(YEAR)
    hosp = L.hospital_actual(df, ev0, ev1)
    feat = L.m2.hgbr_feature_table(y)
    base = L.m2.baseline_forecasts(y)
    fcs = {"dow4": base["dow4"], "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 1}-12-31"))}
    fcs_s = {"dow4": base["dow4"], "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 2}-12-31"))}
    sigma = L.sigma_for_year(y, fcs_s, YEAR)
    win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcs.items()}
    cfg = s10.SCEN["All three US changes (German calendar)"]
    rows = []
    old_ow = L.m2.order_window
    for cal in ("German calendar", "daily deliveries"):
        L.m2.order_window = old_ow if cal == "German calendar" else (lambda day: 2)
        for rule, fn in (("every O unit allowed", _orig_list), ("no O unit allowed", no_o_list)):
            L.us_donor_list = fn
            try:
                res = L.run_config(cfg, y, win, sigma, MODELS, year=YEAR)
            finally:
                L.us_donor_list = _orig_list
            for k in MODELS:
                m = M.match_at(res[k], hosp["shortage_days"], hosp["demand"])
                o_units = interp_at(res[k], "subs_abo_o_last", hosp["shortage_days"])
                rows.append({"calendar": cal, "o_to_non_o": rule, "model": k,
                             "waste_pct_mean": m["waste_pct"].mean(), "waste_p05": M.p5(m["waste_pct"]),
                             "waste_p95": M.p95(m["waste_pct"]),
                             "emergency_units_mean": m["short_units"].mean(),
                             "wasted_plus_emergency_mean": m["lost_units"].mean(),
                             "o_units_to_non_o_mean": float(np.nanmean(o_units)),
                             "o_units_to_non_o_pct_of_use": 100 * float(np.nanmean(o_units)) / hosp["demand"]})
            print(cal, rule, "done")
    L.m2.order_window = old_ow
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "16_low_titer_bound.csv", index=False)
    # Check: the "every O allowed" German-calendar row equals script 10's all-three row.
    s10res = pd.read_csv(P / "results/m5/10_us_one_change.csv")
    ref = s10res[(s10res.scenario == "All three US changes (German calendar)") & (s10res.model == "hgbr")]["waste_pct_mean"].iloc[0]
    mine = out[(out.calendar == "German calendar") & (out.o_to_non_o == "every O unit allowed") & (out.model == "hgbr")]["waste_pct_mean"].iloc[0]
    assert abs(ref - mine) < 1e-9, (ref, mine)
    t = "=== Low-titer bound, 2018, all three US changes, 31 short days ===\n" + out.round(2).to_string(index=False)
    print(t)
    (OUT / "16_run_log.txt").write_text(t + "\n")


if __name__ == "__main__":
    main()
