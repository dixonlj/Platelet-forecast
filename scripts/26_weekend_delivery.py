#!/usr/bin/env python3
"""
Milestone 9, step 1 (draft v6): does the delivery calendar change the answer?

The independent review (C1) noted that the simulation gives too few emergency
units per short day (about 5 against about 8.8 recorded) and too many short
days on Mondays, and that the delivery calendar was the one key mechanism not
varied in the 7-year comparison. Here the whole 2012-2018 comparison of
scripts 08/13 is rerun under five delivery calendars. Lead time stays 2 days
(an evening order arrives on the morning two days later). Each order tops
stock up to cover the days from tomorrow until the day before the delivery
after next one, plus the cushion.

  base      deliveries Tue-Sat (documented Aachen calendar: Thursday's order
            arrives Saturday and covers Friday-Monday)
  weekdays  deliveries Mon-Fri only (no weekend delivery)
  mon_sat   deliveries Mon-Sat (Saturday plus a Monday delivery)
  tue_sun   deliveries Tue-Sun (Saturday and Sunday; = Thursday and Friday orders)
  daily     deliveries every day

Models: weekday average, gradient boosting, detrended gradient boosting
(script 27), Chronos-Bolt, SARIMA, and the hospital-like standing order of the
reality check (script 09). The source authors' LASSO/RNN are left out because
they exist only as 2- and 4-day totals and some calendars need 3-day totals.
Every model is matched to each year's recorded short days (and 20 short days),
30 paired seeds, as in the main analysis. Also reported: simulated emergency
units per short day, the Monday share of short days and the weekday pattern
of waste, against the hospital's record.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=2 PYTHONPATH=scripts .venv/bin/python scripts/26_weekend_delivery.py
"""
from __future__ import annotations

import importlib.util
import sys

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m9"
MODELS = ["dow4", "hgbr", "gbdt", "chronos", "sarima", "standing"]
CALENDARS = {"base": {1, 2, 3, 4, 5}, "weekdays": {0, 1, 2, 3, 4}, "mon_sat": {0, 1, 2, 3, 4, 5},
             "tue_sun": {1, 2, 3, 4, 5, 6}, "daily": set(range(7))}
LABELS = {"base": "Tue-Sat (base)", "weekdays": "Mon-Fri, no weekend", "mon_sat": "Mon-Sat",
          "tue_sun": "Tue-Sun", "daily": "Every day"}


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s09 = _load("s09", "09_reality_check.py")
s12 = _load("s12", "12_sarima.py")
s20 = _load("s20", "20_horizon_accuracy_and_stats.py")
s27 = _load("s27", "27_gb_detrended.py")


def make_window_fn(arrive: set):
    """Return day -> number of days the evening order covers (0 = no order)."""
    table = {}
    for dow in range(7):
        a = (dow + L.m2.LEAD_DAYS) % 7
        if a not in arrive:
            table[dow] = 0
            continue
        gap = next(g for g in range(1, 8) if (a + g) % 7 in arrive)
        table[dow] = 1 + gap
    return (lambda day: table[day.dayofweek]), table


def interp_dow(res_m: dict, key: str, target: float) -> np.ndarray:
    """Per-seed weekday array (7,) at the matched point, same interpolation as lib_m5.match_at."""
    SD, A = res_m["shortage_days"], res_m[key]
    out = []
    for s in range(SD.shape[0]):
        idx = np.where(SD[s] <= target)[0]
        if not len(idx):
            out.append(np.full(7, np.nan)); continue
        j = idx[0]
        if j == 0 or SD[s, j - 1] == SD[s, j]:
            out.append(A[s, j])
        else:
            f = (SD[s, j - 1] - target) / (SD[s, j - 1] - SD[s, j])
            out.append(A[s, j - 1] + f * (A[s, j] - A[s, j - 1]))
    return np.nanmean(np.array(out), axis=0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fn_base, tab = make_window_fn(CALENDARS["base"])
    for d in range(7):   # the generic rule must reproduce the documented calendar
        assert tab[d] == L.m2.order_window(pd.Timestamp("2018-01-01") + pd.Timedelta(days=d)), d
    df, y, _ = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    featd = s27.detrended_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    gd = {Y: s27.gbdt_forecasts(featd, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2010, 2018)}
    stand = s09.standing_order_fc(y)
    cals = sys.argv[1:] or list(CALENDARS)
    rows, dows = [], []
    for cal in cals:
        fn, tab = make_window_fn(CALENDARS[cal])
        for Y in M.YEARS:
            _, ev0, ev1 = L.year_window(Y)
            hosp = L.hospital_actual(df, ev0, ev1)
            fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "gbdt": gd[Y - 1], "chronos": chron,
                   "sarima": sar[Y - 1], "standing": stand}
            fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "gbdt": gd[Y - 2], "chronos": chron,
                   "sarima": sar[Y - 2], "standing": stand}
            sigma = L.sigma_for_year(y, fcS, Y)
            win = {}
            for k, fc in fcY.items():
                w2, w3, w4 = (L.m2.window_sum(fc, n) for n in (2, 3, 4))
                d2, d3, d4 = (L.m2.window_sum(base["dow4"], n) for n in (2, 3, 4))
                win[k] = (w2.fillna(d2), w4.fillna(d4), w3.fillna(d3))   # warm-up gaps only
            res = L.run_config(L.m3.BASE, y, win, sigma, MODELS, year=Y, order_window_fn=fn)
            for tname, target in (("hospital", hosp["shortage_days"]), ("fixed20", 20)):
                for k in MODELS:
                    m = M.match_at(res[k], target, hosp["demand"])
                    sd_at = []
                    for s in range(res[k]["shortage_days"].shape[0]):
                        idx = np.where(res[k]["shortage_days"][s] <= target)[0]
                        sd_at.append(res[k]["shortage_days"][s, 0] if len(idx) and idx[0] == 0 else np.nan)
                    rows.append({"calendar": cal, "year": Y, "target": tname, "target_short_days": target,
                                 "model": k, "waste_pct_mean": m["waste_pct"].mean(),
                                 "waste_units_mean": m["waste_units"].mean(),
                                 "emergency_units_mean": m["short_units"].mean(),
                                 "wasted_plus_emergency_mean": m["lost_units"].mean(),
                                 "emergency_per_short_day": m["short_units"].mean() / target,
                                 "monday_share_of_short_days": m["monday_share"].mean(),
                                 "k_mean": m["k"].mean(), "n_seeds": int(m["waste_pct"].notna().sum()),
                                 "n_seeds_below_target_at_k0": int(np.sum(~np.isnan(sd_at))),
                                 "hospital_waste_pct": hosp["waste_pct"],
                                 "hospital_emergency_units": hosp["short_units"], "demand": hosp["demand"]})
                    if tname == "hospital":
                        w = interp_dow(res[k], "waste_by_dow", target)
                        su = interp_dow(res[k], "short_by_dow", target)
                        sdd = interp_dow(res[k], "short_days_by_dow", target)
                        for dw in range(7):
                            dows.append({"calendar": cal, "year": Y, "model": k, "dow": dw,
                                         "waste_units": w[dw], "emergency_units": su[dw], "short_days": sdd[dw]})
            print(cal, Y, "done", flush=True)
    out = pd.DataFrame(rows)
    tag = "" if not sys.argv[1:] else "_" + "_".join(cals)
    out.to_csv(OUT / f"26_weekend_delivery{tag}.csv", index=False)
    pd.DataFrame(dows).to_csv(OUT / f"26_weekend_by_weekday{tag}.csv", index=False)


def summarise() -> None:
    """Combine per-calendar files (if run in parallel) and write summary + log."""
    files = sorted(OUT.glob("26_weekend_delivery_*.csv"))
    out = pd.concat([pd.read_csv(f) for f in files]) if files else pd.read_csv(OUT / "26_weekend_delivery.csv")
    dfiles = sorted(OUT.glob("26_weekend_by_weekday_*.csv"))
    dows = pd.concat([pd.read_csv(f) for f in dfiles]) if dfiles else pd.read_csv(OUT / "26_weekend_by_weekday.csv")
    out.to_csv(OUT / "26_weekend_delivery.csv", index=False)
    dows.to_csv(OUT / "26_weekend_by_weekday.csv", index=False)
    df, y, _ = L.load_series()

    # Check: the base calendar must reproduce scripts 08/13/27.
    ref = pd.read_csv(OUT / "27_multiyear_inventory.csv")
    chk = out[out.calendar == "base"].merge(ref[["year", "target", "model", "waste_pct_mean"]],
                                            on=["year", "target", "model"], suffixes=("", "_ref"))
    maxdiff = float(np.abs(chk["waste_pct_mean"] - chk["waste_pct_mean_ref"]).max())
    ref9 = pd.read_csv(P / "results/m5/09_reality_check.csv").query("policy == 'standing' and life_scenario.str.startswith('base')")
    c9 = out[(out.calendar == "base") & (out.target == "hospital") & (out.model == "standing")].merge(ref9, on="year")
    maxdiff9 = float(np.abs(c9["waste_pct_mean"] - c9["sim_waste_pct"]).max())

    # Recorded figures in the same windows
    rec = []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        d = df.loc[ev0:ev1]
        rec.append({"year": Y, "short_days": int((d.purchase > 0).sum()), "emergency_units": int(d.purchase.sum()),
                    "monday_short_days": int(((d.purchase > 0) & (d.index.dayofweek == 0)).sum()),
                    "waste_units": int(d.waste.sum())})
    rec = pd.DataFrame(rec)
    allw = pd.concat([df.loc[L.year_window(Y)[1]:L.year_window(Y)[2]] for Y in M.YEARS])
    rec_waste_dow = allw.groupby(allw.index.dayofweek).waste.sum() / allw.waste.sum()
    rec_eps = rec.emergency_units.sum() / rec.short_days.sum()
    rec_mon = rec.monday_short_days.sum() / rec.short_days.sum()

    summ = []
    for (cal, tname), g in out.groupby(["calendar", "target"], sort=False):
        w = g.pivot(index="year", columns="model", values="waste_pct_mean")
        l = g.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
        e = g.pivot(index="year", columns="model", values="emergency_units_mean")
        mo = g.pivot(index="year", columns="model", values="monday_share_of_short_days")
        sdays = g.groupby("year").target_short_days.first()
        for m in MODELS:
            r = {"calendar": cal, "target": tname, "model": m, "mean_waste_pct": w[m].mean(),
                 "mean_lost_units": l[m].mean(), "mean_emergency_units": e[m].mean(),
                 "emergency_per_short_day": e[m].sum() / sdays.sum(),
                 "monday_share_of_short_days": (mo[m] * sdays).sum() / sdays.sum(),
                 "min_seeds_matched": int(g[g.model == m].n_seeds.min()),
                 "seeds_below_target_at_k0": int(g[g.model == m].n_seeds_below_target_at_k0.sum())}
            if m not in ("dow4", "standing"):
                tw = s20.year_tests((w[m] - w.dow4).values)
                tl = s20.year_tests((l[m] - l.dow4).values)
                r.update({"years_less_waste_than_wa": tw["years_better"], "mean_waste_gap_pts": tw["mean_diff"],
                          "waste_gap_ci_lo": tw["ci_lo"], "waste_gap_ci_hi": tw["ci_hi"], "waste_sign_p": tw["sign_p"],
                          "years_fewer_lost_than_wa": tl["years_better"], "mean_lost_gap_units": tl["mean_diff"],
                          "lost_gap_ci_lo": tl["ci_lo"], "lost_gap_ci_hi": tl["ci_hi"], "lost_sign_p": tl["sign_p"]})
            summ.append(r)
    summ = pd.DataFrame(summ)
    summ.to_csv(OUT / "26_weekend_summary.csv", index=False)

    wd = dows.groupby(["calendar", "model", "dow"]).waste_units.sum().reset_index()
    wd["share"] = wd.waste_units / wd.groupby(["calendar", "model"]).waste_units.transform("sum")
    wdp = wd.pivot_table(index=["calendar", "model"], columns="dow", values="share")
    wdp.columns = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wdp.loc[("RECORDED", "hospital"), :] = rec_waste_dow.values
    wdp.to_csv(OUT / "26_waste_share_by_weekday.csv")

    lines = ["=== Milestone 9 step 1: delivery-calendar sensitivity, 2012-2018 ===",
             f"check: base calendar vs script 27 (= scripts 08/13), max |waste diff| = {maxdiff:.2e} ({len(chk)} rows)",
             f"check: base standing order vs script 09, max |waste diff| = {maxdiff9:.2e}",
             f"recorded: emergency units per short day {rec_eps:.2f} ({rec.emergency_units.sum()} / {rec.short_days.sum()}); "
             f"Monday share of short days {rec_mon:.3f}",
             "recorded per year:", rec.to_string(index=False),
             "Summary:", summ.round(3).to_string(index=False),
             "Waste share by weekday (scored days, 2012-2018):", wdp.round(3).to_string()]
    txt = "\n".join(lines)
    print(txt)
    (OUT / "26_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["summary"]:
        summarise()
    else:
        main()
