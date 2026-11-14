#!/usr/bin/env python3
"""
Milestone 6, step 2: add the SARIMA baseline (script 12) to the multi-year
inventory test of script 08, with the same 30 paired seeds and the same
matching rule. The weekday average, gradient boosting and Chronos-Bolt are
re-run alongside so the paired comparison is like-for-like; the script checks
that their numbers equal script 08's.

Also writes 1-day accuracy and Diebold-Mariano tests of SARIMA vs the weekday
average and vs gradient boosting.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/13_multiyear_sarima.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m6"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s12 = _load("s12", "12_sarima.py")
MODELS = ["dow4", "hgbr", "chronos", "sarima"]


def main() -> None:
    df, y, _ = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c) for c in range(2010, 2018)}
    act1 = y.shift(-1)
    rows, per_seed, acc = [], [], []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1].reindex(y.index)}
        fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "chronos": chron, "sarima": sar[Y - 2].reindex(y.index)}
        sigma = L.sigma_for_year(y, fcS, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcY.items()}
        orig = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        err = {k: (act1[orig] - fcY[k].loc[orig, 1]).values for k in MODELS}
        for k in MODELS:
            acc.append({"year": Y, "model": k, "mae_1d": float(np.nanmean(np.abs(err[k])))})
        for other in ("dow4", "hgbr", "chronos"):
            dbar, st, p = s08.dm_test(err["sarima"], err[other])
            acc.append({"year": Y, "model": f"DM_sarima_vs_{other}", "mae_1d": dbar, "dm_stat": st, "dm_p": p})
        res = L.run_config(L.m3.BASE, y, win, sigma, MODELS, year=Y)
        for tname, target in (("hospital", hosp["shortage_days"]), ("fixed20", 20), ("fixed50", 50)):
            mt = {k: M.match_at(res[k], target, hosp["demand"]) for k in MODELS}
            for k in MODELS:
                m = mt[k]
                d = m["waste_pct"] - mt["dow4"]["waste_pct"]
                dl = m["lost_units"] - mt["dow4"]["lost_units"]
                rows.append({"year": Y, "target": tname, "target_short_days": target, "model": k,
                             "sigma": sigma[k], "waste_pct_mean": m["waste_pct"].mean(),
                             "waste_pct_p05": M.p5(m["waste_pct"]), "waste_pct_p95": M.p95(m["waste_pct"]),
                             "emergency_units_mean": m["short_units"].mean(),
                             "wasted_plus_emergency_mean": m["lost_units"].mean(),
                             "waste_gap_vs_dow4": d.mean(), "seeds_less_waste_than_dow4": int((d < 0).sum()),
                             "lost_gap_vs_dow4": dl.mean(), "seeds_fewer_lost_than_dow4": int((dl < 0).sum()),
                             "n_seeds": int(m["waste_pct"].notna().sum()), "demand": hosp["demand"]})
                if tname == "hospital":
                    for s, r in m.iterrows():
                        per_seed.append({"year": Y, "model": k, "seed": 1000 + s, **r.drop("seed").to_dict()})
        print(Y, "done")
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "13_multiyear_inventory.csv", index=False)
    ps = pd.DataFrame(per_seed)
    ps.to_csv(OUT / "13_per_seed.csv", index=False)
    accd = pd.DataFrame(acc)
    accd.to_csv(OUT / "13_accuracy_by_year.csv", index=False)

    # Consistency check against script 08 (same seeds, same forecasts).
    old = pd.read_csv(P / "results/m5/08_per_seed.csv")
    chk = ps[ps.model != "sarima"].merge(old, on=["year", "model", "seed"], suffixes=("", "_08"))
    max_diff = float(np.nanmax(np.abs(chk["waste_pct"] - chk["waste_pct_08"])))
    assert len(chk) == 7 * 3 * 30 and max_diff < 1e-6, (len(chk), max_diff)

    h = out[out.target == "hospital"]
    piv = h.pivot(index="year", columns="model", values="waste_pct_mean")
    pivl = h.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
    pive = h.pivot(index="year", columns="model", values="emergency_units_mean")
    mae = accd[accd.model.isin(MODELS)].pivot(index="year", columns="model", values="mae_1d")
    dm = accd[accd.model.str.startswith("DM_")].pivot(index="year", columns="model", values="dm_p")
    lines = ["=== Milestone 6: SARIMA added to the multi-year test (hospital short days, 30 seeds) ===",
             f"check vs script 08: {len(chk)} rows, max |waste diff| = {max_diff:.2e}",
             "Waste % mean:", piv.round(2).to_string(), f"mean: {piv.mean().round(2).to_dict()}",
             "Emergency units mean:", pive.round(0).to_string(), f"mean: {pive.mean().round(1).to_dict()}",
             "Wasted + emergency units mean:", pivl.round(0).to_string(), f"mean: {pivl.mean().round(1).to_dict()}",
             "1-day MAE:", mae.round(3).to_string(), f"mean: {mae.mean().round(3).to_dict()}",
             "DM p-values (negative mean diff = SARIMA more accurate):", dm.round(4).to_string()]
    for tname in ("hospital", "fixed20", "fixed50"):
        g = out[out.target == tname].pivot(index="year", columns="model", values="waste_pct_mean")
        lines.append(f"{tname}: SARIMA wastes less than WA in {int((g.sarima < g.dow4).sum())}/7 years; "
                     f"less than GB in {int((g.sarima < g.hgbr).sum())}/7; mean {g.mean().round(2).to_dict()}")
    lines.append(f"SARIMA fewer wasted+emergency than WA in {int((pivl.sarima < pivl.dow4).sum())}/7 years; "
                 f"mean gap {(pivl.sarima - pivl.dow4).mean():.1f} units/yr")
    txt = "\n".join(lines)
    print(txt)
    (OUT / "13_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
