#!/usr/bin/env python3
"""
Milestone 9, step 2 (draft v6): gradient boosting on DETRENDED data.

Why: the independent review (C4) noted that the gradient-boosting model of
script 02 forecast too low at every horizon (bias +0.9, +1.8 and +3.7 units at
1, 2 and 4 days) because tree models cannot predict values above the range they
were trained on, and platelet use rose over 2008-2018.

The fix, fixed BEFORE any test year was scored and not tuned afterwards:
  level L_i  = mean use over the 28 days up to and including the origin day i
  target     = use on day i+h  minus  L_i
  features   = the same calendar features as script 02 (horizon, target weekday,
               month, holiday flags) and the same lag features, each expressed
               relative to the level: lag1-L, lag7-L, lag14-L, roll7-L
  forecast   = L_i + predicted difference
Same HistGradientBoostingRegressor settings as script 02 (not tuned), same
expanding window (train on years before the test year), same cushion unit
(2-day miss in the year before, from a model trained up to Y-2), same 30
paired seeds and the same simulation and matching as scripts 08/13.

Outputs (results/m9/):
  27_accuracy_by_horizon.csv   MAE and bias at 1, 2 and 4 days, per year
  27_dm_tests.csv              Diebold-Mariano vs the weekday average and vs the
                               original GB, per year and horizon, Holm within
                               each family of 7 years; plus the 1-day vs-weekday
                               tests re-corrected with Holm across all 42 1-day
                               tests (the 35 of draft v5 plus these 7)
  27_multiyear_inventory.csv   waste, emergency, lost units at the hospital's
                               short days and at 20 and 50 short days
  27_year_level_tests.csv      sign / Wilcoxon / t CI vs the weekday average,
                               with Holm across the new model's tests
  27_gb_detrended_forecasts_<Y>.csv  cached forecasts (trained to 31 Dec Y)
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=2 PYTHONPATH=scripts .venv/bin/python scripts/27_gb_detrended.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m9"
MODELS = ["dow4", "hgbr", "gbdt", "chronos", "sarima"]
FEATS = ["h", "dow", "month", "holiday", "origin_holiday", "lag1_rel", "lag7_rel", "lag14_rel", "roll7_rel"]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s12 = _load("s12", "12_sarima.py")
s20 = _load("s20", "20_horizon_accuracy_and_stats.py")


def detrended_table(y: pd.Series) -> pd.DataFrame:
    f = L.m2.hgbr_feature_table(y)
    lev = f["roll28"]
    for c in ("lag1", "lag7", "lag14", "roll7"):
        f[f"{c}_rel"] = f[c] - lev
    f["level"] = lev
    f["target_rel"] = f["target"] - lev
    return f


def gbdt_forecasts(feat: pd.DataFrame, train_end: pd.Timestamp) -> pd.DataFrame:
    """Fit on rows whose target date is <= train_end; predict every origin (origin x h)."""
    cache = OUT / f"27_gb_detrended_forecasts_{train_end.year}.csv"
    if cache.exists():
        d = pd.read_csv(cache, index_col=0, parse_dates=True)
        d.columns = [int(c) for c in d.columns]
        return d
    ok = feat[FEATS + ["level"]].notna().all(axis=1)
    tr = feat[ok & feat["target"].notna() & (feat["target_date"] <= train_end)]
    model = HistGradientBoostingRegressor(**L.m2.HGBR_PARAMS, categorical_features=[FEATS.index("dow")])
    model.fit(tr[FEATS], tr["target_rel"])
    pred = pd.Series(np.nan, index=feat.index)
    pred[ok] = model.predict(feat.loc[ok, FEATS]) + feat.loc[ok, "level"]
    out = feat.assign(pred=pred).pivot(index="origin", columns="h", values="pred")
    out.to_csv(cache)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat_old = L.m2.hgbr_feature_table(y)
    feat = detrended_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat_old, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    gd = {Y: gbdt_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2010, 2018)}
    act = {1: y.shift(-1), 2: L.m2.actual_window_sum(y, 2), 4: L.m2.actual_window_sum(y, 4)}

    # ---- accuracy and DM tests
    acc, errs = [], {}
    for Y in M.YEARS:
        orig = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        fc = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "gbdt": gd[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
        for n in (1, 2, 4):
            for m in MODELS:
                f = fc[m].loc[orig, 1] if n == 1 else L.m2.window_sum(fc[m], n).reindex(orig)
                e = (act[n][orig] - f).values
                errs[(Y, n, m)] = e
                acc.append({"year": Y, "horizon_days": n, "model": m, "n_origins": int((~np.isnan(e)).sum()),
                            "mae": float(np.nanmean(np.abs(e))), "mean_error_actual_minus_fc": float(np.nanmean(e))})
    acc = pd.DataFrame(acc)
    acc.to_csv(OUT / "27_accuracy_by_horizon.csv", index=False)
    # check: original GB / others reproduce script 20
    ref = pd.read_csv(P / "results/m8/20_accuracy_by_horizon.csv")
    chk = acc.merge(ref, on=["year", "horizon_days", "model"], suffixes=("", "_ref"))
    acc_maxdiff = float(np.abs(chk["mae"] - chk["mae_ref"]).max())

    dm = []
    for n in (1, 2, 4):
        for other in ("dow4", "hgbr"):
            for Y in M.YEARS:
                e1, e0 = errs[(Y, n, "gbdt")], errs[(Y, n, other)]
                ok = ~np.isnan(e1) & ~np.isnan(e0)
                dbar, st, p = s08.dm_test(e1[ok], e0[ok])
                dm.append({"horizon_days": n, "comparison": f"gbdt vs {other}", "year": Y,
                           "mean_abs_err_diff": dbar, "dm_p": p})
            e1 = np.concatenate([errs[(Y, n, "gbdt")] for Y in M.YEARS])
            e0 = np.concatenate([errs[(Y, n, other)] for Y in M.YEARS])
            ok = ~np.isnan(e1) & ~np.isnan(e0)
            dbar, st, p = s08.dm_test(e1[ok], e0[ok])
            dm.append({"horizon_days": n, "comparison": f"gbdt vs {other}", "year": "pooled 2012-2018",
                       "mean_abs_err_diff": dbar, "dm_p": p})
    dm = pd.DataFrame(dm)
    dm["holm_p_within_7_years"] = np.nan
    for (n, c), g in dm[dm.year != "pooled 2012-2018"].groupby(["horizon_days", "comparison"]):
        dm.loc[g.index, "holm_p_within_7_years"] = s20.holm(g["dm_p"].values)
    # 1-day family of draft v5 (35 tests) plus the 7 new gbdt-vs-weekday tests
    old = pd.read_csv(P / "results/m8/20_dm_1day_holm.csv")
    fam = pd.concat([old[["year", "model", "dm_p"]],
                     dm[(dm.horizon_days == 1) & (dm.comparison == "gbdt vs dow4") & (dm.year != "pooled 2012-2018")]
                     .assign(model="DM_gbdt_vs_dow4")[["year", "model", "dm_p"]]], ignore_index=True)
    fam["holm_p_42"] = s20.holm(fam["dm_p"].values)
    fam.to_csv(OUT / "27_dm_1day_holm42.csv", index=False)
    dm.to_csv(OUT / "27_dm_tests.csv", index=False)

    # ---- inventory, 7 years
    rows = []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "gbdt": gd[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
        fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "gbdt": gd[Y - 2], "chronos": chron, "sarima": sar[Y - 2]}
        sigma = L.sigma_for_year(y, fcS, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcY.items()}
        res = L.run_config(L.m3.BASE, y, win, sigma, MODELS, year=Y)
        for tname, target in (("hospital", hosp["shortage_days"]), ("fixed20", 20), ("fixed50", 50)):
            mt = {k: M.match_at(res[k], target, hosp["demand"]) for k in MODELS}
            for k in MODELS:
                m = mt[k]
                rows.append({"year": Y, "target": tname, "target_short_days": target, "model": k,
                             "sigma": sigma[k], "waste_pct_mean": m["waste_pct"].mean(),
                             "waste_units_mean": m["waste_units"].mean(),
                             "emergency_units_mean": m["short_units"].mean(),
                             "wasted_plus_emergency_mean": m["lost_units"].mean(),
                             "k_mean": m["k"].mean(), "n_seeds": int(m["waste_pct"].notna().sum()),
                             "demand": hosp["demand"]})
        print(Y, "done", flush=True)
    inv = pd.DataFrame(rows)
    inv.to_csv(OUT / "27_multiyear_inventory.csv", index=False)
    ref = pd.concat([pd.read_csv(P / "results/m5/08_multiyear_inventory.csv"),
                     pd.read_csv(P / "results/m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
    chk = inv.merge(ref[["year", "target", "model", "waste_pct_mean"]], on=["year", "target", "model"], suffixes=("", "_ref"))
    inv_maxdiff = float(np.abs(chk["waste_pct_mean"] - chk["waste_pct_mean_ref"]).max())

    tests = []
    for tname, g in inv.groupby("target", sort=False):
        for outcome, col in (("Waste (points)", "waste_pct_mean"), ("Wasted + emergency units a year", "wasted_plus_emergency_mean"),
                             ("Emergency units a year", "emergency_units_mean")):
            pv = g.pivot(index="year", columns="model", values=col)
            for m in ("gbdt", "hgbr"):
                tests.append({"target": tname, "outcome": outcome, "model": m, "vs": "dow4",
                              **s20.year_tests((pv[m] - pv["dow4"]).values)})
            tests.append({"target": tname, "outcome": outcome, "model": "gbdt", "vs": "hgbr",
                          **s20.year_tests((pv["gbdt"] - pv["hgbr"]).values)})
    tests = pd.DataFrame(tests)
    # Holm across the new model's vs-weekday-average tests on waste and lost units (3 targets x 2 outcomes)
    sel = (tests.model == "gbdt") & (tests.vs == "dow4") & tests.outcome.isin(["Waste (points)", "Wasted + emergency units a year"])
    tests["holm_sign_p"] = np.nan
    tests.loc[sel, "holm_sign_p"] = s20.holm(tests.loc[sel, "sign_p"].values)
    tests["holm_wilcoxon_p"] = np.nan
    tests.loc[sel, "holm_wilcoxon_p"] = s20.holm(tests.loc[sel, "wilcoxon_p"].values)
    tests.to_csv(OUT / "27_year_level_tests.csv", index=False)

    lines = ["=== Milestone 9 step 2: gradient boosting on detrended data (gbdt) ===",
             f"check: accuracy of existing models vs script 20, max |MAE diff| = {acc_maxdiff:.2e}",
             f"check: inventory of existing models vs scripts 08/13, max |waste diff| = {inv_maxdiff:.2e}"]
    for n in (1, 2, 4):
        g = acc[acc.horizon_days == n]
        lines += [f"{n}-day MAE:", g.pivot(index="year", columns="model", values="mae")[MODELS].round(3).to_string(),
                  f"mean: {g.groupby('model').mae.mean().round(3).to_dict()}",
                  f"{n}-day bias (actual - forecast):",
                  g.pivot(index="year", columns="model", values="mean_error_actual_minus_fc")[MODELS].round(2).to_string(),
                  f"mean: {g.groupby('model').mean_error_actual_minus_fc.mean().round(2).to_dict()}"]
    lines += ["DM tests:", dm.round(4).to_string(index=False),
              "1-day Holm across 42:", fam[fam.model == "DM_gbdt_vs_dow4"].round(4).to_string(index=False)]
    for tname in ("hospital", "fixed20", "fixed50"):
        g = inv[inv.target == tname]
        for col in ("waste_pct_mean", "emergency_units_mean", "wasted_plus_emergency_mean"):
            pv = g.pivot(index="year", columns="model", values=col)[MODELS]
            lines += [f"{tname} {col}:", pv.round(2).to_string(), f"mean: {pv.mean().round(2).to_dict()}"]
    lines += ["Year-level tests:", tests.round(4).to_string(index=False)]

    # ---- diagnostic: bias by order type over the scored inventory days (8 Jan-18 Dec).
    # Thursday's order covers Friday-Monday (4 days); Sunday-Wednesday orders cover 2 days.
    ob = []
    for Y in M.YEARS:
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "gbdt": gd[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
        orig = y.loc[pd.Timestamp(f"{Y}-01-08"):pd.Timestamp(f"{Y}-12-18")].index
        for m, f in fcY.items():
            for n, label, mask in ((4, "Thursday order (Fri-Mon, 4 days)", orig.day_of_week == 3),
                                   (2, "Sun-Wed orders (2 days)", np.isin(orig.day_of_week, [6, 0, 1, 2]))):
                o = orig[mask]
                e = act[n][o] - L.m2.window_sum(f, n)[o]
                ob.append({"year": Y, "model": m, "order_type": label, "n_orders": int(e.notna().sum()),
                           "bias_actual_minus_fc": float(e.mean()), "mae": float(e.abs().mean())})
    ob = pd.DataFrame(ob)
    ob.to_csv(OUT / "27_bias_by_order_type.csv", index=False)
    lines += ["Bias by order type (scored days; positive = forecast too low), 7-year mean:",
              ob.groupby(["order_type", "model"])[["bias_actual_minus_fc", "mae"]].mean().round(2).to_string()]
    txt = "\n".join(lines)
    print(txt)
    (OUT / "27_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
