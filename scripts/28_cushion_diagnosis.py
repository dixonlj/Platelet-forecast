#!/usr/bin/env python3
"""
Milestone 9, step 3 (draft v6): why did the day-by-day ("quantile") cushion of
script 05 nearly double waste (about 7.6% -> 13.2% in 2017, 8.4% -> 13.6% in
2018) at the same number of short days?

Reruns script 05's 2017 and 2018 setup exactly (same improved gradient-boosting
point forecast, same 50th/90th percentile models, same 30 seeds) and adds:
  1. bug checks: the quantile bands are aligned with the order windows, the
     band never goes negative, the matched k is inside the grid, and the run
     reproduces script 05's published numbers;
  2. the size of the cushion unit: fixed unit (prior-year 2-day miss, the same
     for 2- and 4-day orders) against the band (q90 - q50 summed over the days
     an order covers), for Sunday-Wednesday (2-day) and Thursday (4-day) orders;
  3. waste by weekday at the matched point (fixed vs day-by-day);
  4. a diagnostic variant that keeps the day-to-day SHAPE of the band but gives
     2- and 4-day orders the same average cushion unit as the fixed rule
     (band / its mean over that year's origins of the same order type x fixed
     unit). This uses only forecasts, not outcomes, but the yearly mean is a
     look-ahead over forecasts, so it is a diagnostic, not a new method.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=2 PYTHONPATH=scripts .venv/bin/python scripts/28_cushion_diagnosis.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd

import lib_m4 as L

P = L.PROJECT_ROOT
OUT = P / "results/m9"
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s05 = _load("s05", "05_better_model.py")


def at_match(res_m, key, target):
    """Per-seed value of res_m[key] (S x K [x 7]) at the first k where short days <= target, interpolated."""
    SD, A = res_m["shortage_days"], res_m[key]
    vals = []
    for s in range(SD.shape[0]):
        idx = np.where(SD[s] <= target)[0]
        if not len(idx):
            vals.append(np.full(A.shape[2:], np.nan)); continue
        j = idx[0]
        if j == 0 or SD[s, j - 1] == SD[s, j]:
            vals.append(A[s, j])
        else:
            f = (SD[s, j - 1] - target) / (SD[s, j - 1] - SD[s, j])
            vals.append(A[s, j - 1] + f * (A[s, j] - A[s, j - 1]))
    return np.array(vals)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    feat_old = L.m2.hgbr_feature_table(y)
    feat_new = s05.better_feature_table(y)
    ref05 = pd.read_csv(P / "results/m4/05_inventory.csv")
    rows, dow_rows, unit_rows, checks = [], [], [], []
    for year in (2017, 2018):
        _, ev0, ev1 = L.year_window(year)
        hosp = L.hospital_actual(df, ev0, ev1)
        target = hosp["shortage_days"]
        fcs = s05.forecasts_for(y, feat_old, feat_new, pd.Timestamp(f"{year - 1}-12-31"))
        fcs_sig = s05.forecasts_for(y, feat_old, feat_new, pd.Timestamp(f"{year - 2}-12-31"))
        sigma = L.sigma_for_year(y, {"hgbr_new": fcs_sig["hgbr_new"]}, year)["hgbr_new"]
        sp = {n: s05.window_spread(fcs["q50"], fcs["q90"], n) for n in (2, 4)}
        days = pd.date_range(ev0, ev1)
        thu = days[days.day_of_week == 3]
        sw = days[np.isin(days.day_of_week, [6, 0, 1, 2])]
        # bug checks
        raw2 = (fcs["q90"][[1, 2]].sum(axis=1) - fcs["q50"][[1, 2]].sum(axis=1))
        checks.append(f"{year}: share of 2-day windows where q90 < q50 before clipping = {(raw2.loc[sw] < 0).mean():.3f}; "
                      f"share of Thursday 4-day windows clipped = {((fcs['q90'][[1,2,3,4]].sum(axis=1) - fcs['q50'][[1,2,3,4]].sum(axis=1)).loc[thu] < 0).mean():.3f}")
        checks.append(f"{year}: spread index equals forecast origin index: {bool(sp[2].index.equals(fcs['q50'].index))}; "
                      f"missing spread on scored order days: {int(sp[2].reindex(sw).isna().sum() + sp[4].reindex(thu).isna().sum())}")
        # empirical coverage of the band for the order windows (actual <= q90-window?)
        act = {n: L.m2.actual_window_sum(y, n) for n in (2, 4)}
        q90w = {n: fcs["q90"][list(range(1, n + 1))].sum(axis=1) for n in (2, 4)}
        q50w = {n: fcs["q50"][list(range(1, n + 1))].sum(axis=1) for n in (2, 4)}
        for n, o in ((2, sw), (4, thu)):
            unit_rows.append({"year": year, "order_type": "Thursday (4-day)" if n == 4 else "Sun-Wed (2-day)",
                              "fixed_unit": sigma, "band_mean": float(sp[n].reindex(o).mean()),
                              "band_cv": float(sp[n].reindex(o).std() / sp[n].reindex(o).mean()),
                              "band_over_fixed": float(sp[n].reindex(o).mean() / sigma),
                              "share_actual_above_q90_window": float((act[n][o] > q90w[n][o]).mean()),
                              "share_actual_above_q50_window": float((act[n][o] > q50w[n][o]).mean())})
        # variant: same shape, fixed-rule average size per order type
        scaled = {}
        for n, o in ((2, sw), (4, thu)):
            scaled[n] = sp[n] / float(sp[n].reindex(o).mean()) * sigma
        win = s05.pack_windows(fcs)
        win = {"hgbr_new": win["hgbr_new"], "hgbr_new_q": win["hgbr_new"], "hgbr_new_qscaled": win["hgbr_new"]}
        sig = {k: sigma for k in win}
        res = L.run_config(L.m3.BASE, y, win, sig, list(win), year=year,
                           safety_daily={"hgbr_new_q": sp, "hgbr_new_qscaled": scaled})
        labels = {"hgbr_new": "fixed cushion", "hgbr_new_q": "day-by-day cushion (script 05)",
                  "hgbr_new_qscaled": "day-by-day shape, fixed-rule size (diagnostic)"}
        for m in win:
            w = at_match(res[m], "waste_pct", target)
            st = at_match(res[m], "mean_end_stock", target)
            wd = at_match(res[m], "waste_by_dow", target)
            k = []
            for s in range(30):
                idx = np.where(res[m]["shortage_days"][s] <= target)[0]
                k.append(np.nan if not len(idx) else L.K_GRID[idx[0]])
            unit = {"hgbr_new": (sigma, sigma), "hgbr_new_q": (float(sp[2].reindex(sw).mean()), float(sp[4].reindex(thu).mean())),
                    "hgbr_new_qscaled": (sigma, sigma)}[m]
            km = None
            # interpolated k
            kk = []
            for s in range(30):
                SD = res[m]["shortage_days"][s]; idx = np.where(SD <= target)[0]
                if not len(idx): kk.append(np.nan); continue
                j = idx[0]
                if j == 0 or SD[j - 1] == SD[j]: kk.append(L.K_GRID[j])
                else:
                    f = (SD[j - 1] - target) / (SD[j - 1] - SD[j]); kk.append(L.K_GRID[j - 1] + f * 0.25)
            km = float(np.nanmean(kk))
            rows.append({"year": year, "variant": labels[m], "target_short_days": target,
                         "waste_pct_mean": float(np.nanmean(w)), "mean_end_stock": float(np.nanmean(st)),
                         "k_matched_mean": km, "n_seeds_matched": int(np.sum(~np.isnan(w))),
                         "max_grid_k_used": float(np.nanmax(k)),
                         "mean_cushion_sun_wed_units": km * unit[0], "mean_cushion_thursday_units": km * unit[1]})
            tot = np.nanmean(wd, axis=0)
            for d in range(7):
                dow_rows.append({"year": year, "variant": labels[m], "dow": DOW[d], "waste_units": float(tot[d]),
                                 "share": float(tot[d] / tot.sum())})
        r05 = ref05[(ref05.year == year)].set_index("model").waste_mean
        got = {r["variant"]: r["waste_pct_mean"] for r in rows if r["year"] == year}
        checks.append(f"{year}: reproduces script 05: fixed {got['fixed cushion']:.4f} vs {r05['hgbr_new']:.4f}; "
                      f"day-by-day {got['day-by-day cushion (script 05)']:.4f} vs {r05['hgbr_new_q']:.4f}")
        print(year, "done", flush=True)
    out = pd.DataFrame(rows); out.to_csv(OUT / "28_cushion_diagnosis.csv", index=False)
    units = pd.DataFrame(unit_rows); units.to_csv(OUT / "28_cushion_units.csv", index=False)
    dows = pd.DataFrame(dow_rows); dows.to_csv(OUT / "28_waste_by_weekday.csv", index=False)
    txt = "\n".join(["=== Milestone 9 step 3: day-by-day cushion diagnosis (2017, 2018) ===", *checks,
                     "Cushion units:", units.round(3).to_string(index=False),
                     "Matched results:", out.round(3).to_string(index=False),
                     "Waste share by weekday:", dows.pivot_table(index=["year", "variant"], columns="dow", values="share")[DOW].round(3).to_string()])
    print(txt)
    (OUT / "28_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
