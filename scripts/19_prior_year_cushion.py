#!/usr/bin/env python3
"""
Milestone 8, step 1: safety cushion chosen in advance from the PREVIOUS year.

In the main analysis (scripts 08 and 13) the cushion unit (sigma) comes from
the year before the test year, but the multiplier k is chosen, separately in
each run, so the simulation hits the hospital's recorded short days IN THE
TEST YEAR. That is a matched-service comparison device, not a policy anyone
could set in advance.

Here k is chosen in advance instead:
  1. At the end of year Y-1, replay year Y-1 with the forecasts that existed
     then (gradient boosting and SARIMA trained up to Y-2; baselines; zero-shot
     Chronos-Bolt; the source authors' published forecasts) and the cushion unit
     sigma_Y (each model's 2-day miss in Y-1, already known at the end of Y-1).
  2. Find the k that gives Y-1's recorded short days (interpolated, per run),
     and take the mean over the 30 runs as that model's single k for year Y.
  3. Run year Y with that k unchanged. Report waste, short days, emergency
     units and wasted + emergency units. Short days are NOT matched any more.

Same 30 paired seeds as scripts 08 and 13. Test years 2012-2018 (2011 is the
first replay year).
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/19_prior_year_cushion.py
"""
from __future__ import annotations

import importlib.util

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


def windows(fc: dict, authors: dict) -> dict:
    """2- and 4-day forecast totals; any missing warm-up origin is filled with the
    weekday average (only the unscored warm-up week is affected)."""
    w = {k: (L.m2.window_sum(f, 2), L.m2.window_sum(f, 4)) for k, f in fc.items()}
    for a in ("lasso", "rnn"):
        w[a] = (authors[f"{a}2"], authors[f"{a}4"])
    d2, d4 = w["dow4"]
    return {k: (v[0].reindex(d2.index).fillna(d2), v[1].reindex(d4.index).fillna(d4)) for k, v in w.items()}


def at_k(res_model: dict, k: float, demand_total: float, k_grid=M.K_GRID) -> pd.DataFrame:
    rows = []
    for s in range(res_model["waste_pct"].shape[0]):
        w = np.interp(k, k_grid, res_model["waste_pct"][s])
        sd = np.interp(k, k_grid, res_model["shortage_days"][s])
        su = np.interp(k, k_grid, res_model["short_units"][s])
        rows.append(dict(seed=s, waste_pct=w, short_days=sd, short_units=su))
    out = pd.DataFrame(rows)
    out["waste_units"] = out["waste_pct"] * demand_total / 100
    out["lost_units"] = out["waste_units"] + out["short_units"]
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2010, 2018)}
    act2 = L.m2.actual_window_sum(y, 2)
    rows, per_seed = [], []
    for Y in M.YEARS:
        prev = Y - 1
        # Forecasts that existed during year Y-1 (used for the replay and for sigma).
        fcS = {"dow4": base["dow4"], "hgbr": gb[Y - 2], "chronos": chron, "sarima": sar[Y - 2]}
        fcY = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
        sigma = L.sigma_for_year(y, fcS, Y)
        o_prev = y.loc[pd.Timestamp(f"{prev - 1}-12-31"):pd.Timestamp(f"{prev}-12-30")].index
        for a in ("lasso", "rnn"):
            sigma[a] = L.m2.mae(act2[o_prev], authors[f"{a}2"][o_prev])
        # 1-2. Replay Y-1 and choose k there.
        _, p0, p1 = L.year_window(prev)
        hp = L.hospital_actual(df, p0, p1)
        res_prev = L.run_config(L.m3.BASE, y, windows(fcS, authors), sigma, MODELS, year=prev)
        k_sel = {}
        for m in MODELS:
            mt = M.match_at(res_prev[m], hp["shortage_days"], hp["demand"])
            k_sel[m] = float(np.nanmean(mt["k"]))
        # 3. Test year Y with k fixed in advance; plus the matched (oracle) point for reference.
        _, e0, e1 = L.year_window(Y)
        hosp = L.hospital_actual(df, e0, e1)
        res = L.run_config(L.m3.BASE, y, windows(fcY, authors), sigma, MODELS, year=Y)
        fixed = {m: at_k(res[m], k_sel[m], hosp["demand"]) for m in MODELS}
        matched = {m: M.match_at(res[m], hosp["shortage_days"], hosp["demand"]) for m in MODELS}
        for m in MODELS:
            f = fixed[m]
            dl = f["lost_units"] - fixed["dow4"]["lost_units"]
            dw = f["waste_pct"] - fixed["dow4"]["waste_pct"]
            rows.append({"year": Y, "model": m, "sigma": sigma[m], "k_prior_year": k_sel[m],
                         "k_matched_test_year": float(np.nanmean(matched[m]["k"])),
                         "prior_year_short_days_target": hp["shortage_days"],
                         "hospital_short_days": hosp["shortage_days"],
                         "short_days_mean": f["short_days"].mean(),
                         "waste_pct_mean": f["waste_pct"].mean(),
                         "emergency_units_mean": f["short_units"].mean(),
                         "wasted_plus_emergency_mean": f["lost_units"].mean(),
                         "waste_gap_vs_dow4": dw.mean(), "lost_gap_vs_dow4": dl.mean(),
                         "seeds_fewer_lost_than_dow4": int((dl < 0).sum()),
                         "matched_waste_pct_mean": matched[m]["waste_pct"].mean(),
                         "matched_lost_mean": matched[m]["lost_units"].mean(),
                         "demand": hosp["demand"]})
            for _, r in f.iterrows():
                per_seed.append({"year": Y, "model": m, "seed": 1000 + int(r["seed"]), **r.drop("seed").to_dict()})
        print(Y, "done", {m: round(k_sel[m], 2) for m in MODELS})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_prior_year_cushion.csv", index=False)
    pd.DataFrame(per_seed).to_csv(OUT / "19_per_seed.csv", index=False)

    # Check: the matched point must reproduce scripts 08/13.
    ref = pd.concat([pd.read_csv(P / "results/m5/08_multiyear_inventory.csv"),
                     pd.read_csv(P / "results/m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
    ref = ref[ref.target == "hospital"][["year", "model", "waste_pct_mean"]]
    chk = out.merge(ref, on=["year", "model"])
    maxdiff = float(np.abs(chk["matched_waste_pct_mean"] - chk["waste_pct_mean_y"]).max())

    lines = ["=== Milestone 8 step 1: cushion multiplier k chosen in Y-1, applied unchanged in Y ===",
             f"check: matched point vs scripts 08/13 max |waste diff| = {maxdiff:.2e} ({len(chk)} rows)"]
    for col in ("k_prior_year", "k_matched_test_year", "short_days_mean", "waste_pct_mean",
                "emergency_units_mean", "wasted_plus_emergency_mean"):
        pv = out.pivot(index="year", columns="model", values=col)[MODELS]
        lines += [f"{col}:", pv.round(2).to_string(), f"mean: {pv.mean().round(2).to_dict()}"]
    lost = out.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
    waste = out.pivot(index="year", columns="model", values="waste_pct_mean")
    sd = out.pivot(index="year", columns="model", values="short_days_mean")
    for m in MODELS[1:]:
        lines.append(f"{m}: fewer lost than WA in {int((lost[m] < lost.dow4).sum())}/7 "
                     f"(mean gap {(lost[m] - lost.dow4).mean():.1f}); less waste in {int((waste[m] < waste.dow4).sum())}/7 "
                     f"(mean gap {(waste[m] - waste.dow4).mean():.2f} pts); fewer short days in "
                     f"{int((sd[m] < sd.dow4).sum())}/7 (mean gap {(sd[m] - sd.dow4).mean():.1f})")
    lines.append(f"hospital short days: {out.groupby('year').hospital_short_days.first().to_dict()}")
    txt = "\n".join(lines)
    print(txt)
    (OUT / "19_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
