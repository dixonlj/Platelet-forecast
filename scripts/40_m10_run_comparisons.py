#!/usr/bin/env python3
"""Milestone 10, steps 5 and 7 (prereg Sections 4, 5.1, 5.2): run every policy through
the CALIBRATED simulation for Aachen 2012-2018 and save per-run outputs.

Scenarios (R1 = cushion k*sigma_m(n) sized to each order's days, PRIMARY; R2 = constant
cushion k*sigma_m(2); R3 = R1 cushion + expiry-aware ordering):
  main            calibrated configuration, R1, R2, R3 (primary + RQ2/RQ3/RQ4 + secondary outcomes)
  v9base          v9 base configuration, R1 (sensitivity 5.2.1)
  cal_<name>      each calendar not chosen, other calibrated parameters fixed (5.2.2)
  life_p3_<x>     p3 = 0.30, 0.43 and sweep 0..1 by 0.1, p2 fixed at calibrated value (5.2.3)
  sf_<name>       delivery shortfalls none / 10% / heavy 25% (5.2.4)
  pooled, ep2     no blood groups; patient episodes mean 2 units (5.2.5)
Sensitivities 5.2.6 (cushion chosen in advance) and 5.2.7 (fixed 20/50 targets) are computed
from the saved main-R1 outputs in script 41.

Forecasts are reused unchanged (prereg 2.3.1). Every forecast origin that falls back to the
4-week weekday average is counted. Common random numbers: seeds 1000-1029 in every scenario.
Educational / advisory only. Public Aachen data. Not clinical.
Run: OMP_NUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python scripts/40_m10_run_comparisons.py [main|sens|all]
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m10 as X

OUT = X.OUT
RAW = OUT / "raw"
POLICIES = ["so", "wa4", "gb", "dgb", "sarima", "cb"]
REFS = ["lasso", "rnn"]
LEVELS = list(range(20, 51))
_G = {}


def load_forecasts():
    df, y, authors = L.load_series()
    s08 = X.load_module("s08", "08_multiyear_test.py")
    s09 = X.load_module("s09", "09_reality_check.py")
    s12 = X.load_module("s12", "12_sarima.py")
    s27 = X.load_module("s27", "27_gb_detrended.py")
    base = X.m2.baseline_forecasts(y)
    feat = X.m2.hgbr_feature_table(y)
    gb = {Y: X.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    # dGB: read the v9 cached forecasts (results/m9/27_gb_detrended_forecasts_<cutoff>.csv), unchanged
    gd = {}
    for Y in range(2010, 2018):
        d = pd.read_csv(X.P / f"results/m9/27_gb_detrended_forecasts_{Y}.csv", index_col=0, parse_dates=True)
        d.columns = [int(c) for c in d.columns]
        gd[Y] = d
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2010, 2018)}
    chron = s08.chronos_forecasts(y)
    stand = s09.standing_order_fc(y)
    return df, y, authors, base["dow4"], gb, gd, sar, chron, stand


def init():
    df, y, authors, wa, gb, gd, sar, chron, stand = load_forecasts()
    _G.update(df=df, y=y, authors=authors, wa=wa, gb=gb, gd=gd, sar=sar, chron=chron, stand=stand)


def year_inputs(Y, tab):
    y, wa = _G["y"], _G["wa"]
    fcY = {"so": _G["stand"], "wa4": wa, "gb": _G["gb"][Y - 1], "dgb": _G["gd"][Y - 1],
           "sarima": _G["sar"][Y - 1], "cb": _G["chron"]}
    fcS = {"so": _G["stand"], "wa4": wa, "gb": _G["gb"][Y - 2], "dgb": _G["gd"][Y - 2],
           "sarima": _G["sar"][Y - 2], "cb": _G["chron"]}
    org = X.prev_year_origins(y, Y)
    sim_start, ev0, ev1 = L.year_window(Y)
    days = pd.date_range(sim_start, ev1)
    win, units, fallbacks = {}, {}, {}
    for k in POLICIES:
        win[k], fb = {}, 0
        for n in (2, 3, 4):
            w, d = X.m2.window_sum(fcY[k], n), X.m2.window_sum(wa, n)
            win[k][n] = w.fillna(d)
            od = [dd for dd in days if tab[dd.dayofweek] == n]
            fb += int(w.reindex(od).isna().sum())
        fallbacks[k] = fb
        units[k] = {n: X.mae_ntotal(y, fcS[k], n, org) for n in (2, 3, 4)}
    a = _G["authors"]
    act = {n: X.m2.actual_window_sum(y, n) for n in (2, 4)}
    for k in REFS:
        win[k] = {2: a[f"{k}2"], 4: a[f"{k}4"], 3: None}
        units[k] = {n: X.m2.mae(act[n][org], a[f"{k}{n}"][org]) for n in (2, 4)}
        od = [dd for dd in days if tab[dd.dayofweek] in (2, 4)]
        fallbacks[k] = int(sum(pd.isna(win[k][tab[dd.dayofweek]][dd]) for dd in od))
    return fcY, win, units, fallbacks


def summarise_target(r, target):
    m = X.matched_summary(r, target)
    return {k: m[k] for k in ("waste_units", "short_units", "short_days", "demand", "k", "status",
                              "blk_waste", "blk_demand", "waste_dow", "short_dow", "short_days_dow")}


def tradeoff(r):
    """Per run, waste % at every integer short-day level 20..50; NaN where not reachable."""
    out = np.full((r["short_days"].shape[0], len(LEVELS)), np.nan)
    for li, lev in enumerate(LEVELS):
        w = X.match_weights(r["short_days"], lev)
        wp = 100 * X.apply_match(r["waste_units"], w) / X.apply_match(r["demand"], w)
        for s, (_, _, _, st) in enumerate(w):
            if st == "ok":
                out[s, li] = wp[s]
    return out


def run_task(task):
    name, spec, pooled, rule, Y, save_curves = task
    t0 = time.time()
    df, y = _G["df"], _G["y"]
    cfg = X.make_cfg(spec, pooled=pooled)
    tab = X.make_window_fn(X.CALENDARS[spec["calendar"]])
    fcY, win, units, fallbacks = year_inputs(Y, tab)
    rec, _ = X.recorded(df, [Y])
    tgt_rec = int(rec.short_days.iloc[0])
    dr = X.draws_for(y, cfg, Y)
    pols = list(POLICIES)
    ns_used = set(v for v in tab.values() if v)
    if rule != "R3" and ns_used <= {2, 4}:
        pols += REFS
    res = {"scenario": name, "spec": spec, "pooled": pooled, "rule": rule, "year": Y, "target_recorded": tgt_rec,
           "demand": int(rec.demand.iloc[0]), "policies": {}}
    for k in pols:
        u = dict(units[k])
        if rule == "R2":
            u = {n: units[k][2] for n in u}
        fw = {n: v for n, v in win[k].items() if v is not None}
        order_rule = "expiry_aware" if rule == "R3" else "standard"
        r = X.run_policy(dr, fw, u, cfg, tab, need_reach=20, order_rule=order_rule,
                         daily_fc=fcY.get(k) if rule == "R3" else None)
        pr = {"units": u, "fallbacks": fallbacks[k], "extended": r["extended"],
              "recorded": summarise_target(r, tgt_rec), "fixed20": summarise_target(r, 20),
              "fixed50": summarise_target(r, 50), "tradeoff": tradeoff(r),
              "sd_k0_mean": float(r["short_days"][:, 0].mean())}
        if save_curves:
            pr["curves"] = {kk: r[kk] for kk in ("k_grid", "waste_units", "short_units", "short_days", "demand")}
        res["policies"][k] = pr
    RAW.mkdir(parents=True, exist_ok=True)
    fn = RAW / f"{name}__{rule}__{Y}.pkl"
    with open(fn, "wb") as fh:
        pickle.dump(res, fh)
    return f"{name} {rule} {Y} ({len(pols)} policies) {time.time() - t0:.0f}s"


def tasks(which):
    ch = json.loads((OUT / "38_calibration_choice.json").read_text())
    cal = {k: ch[k] for k in ("calendar", "p2", "p3", "demand", "shortfall")}
    out = []
    if which in ("main", "all"):
        for rule in ("R1", "R2", "R3"):
            for Y in X.TEST_YEARS:
                out.append(("main", cal, False, rule, Y, rule == "R1"))
    if which in ("sens", "all"):
        sens = {"v9base": (dict(X.V9_BASE), False)}
        for c in X.CALENDARS:
            if c != cal["calendar"]:
                sens[f"cal_{c}"] = (dict(cal, calendar=c), False)
        p3s = sorted(set([0.30, 0.43] + [round(x, 1) for x in np.arange(0, 1.01, 0.1)]))
        for p3 in p3s:
            if p3 <= 1 - cal["p2"] + 1e-9 and abs(p3 - cal["p3"]) > 1e-9:
                sens[f"life_p3_{p3:.2f}"] = (dict(cal, p3=p3), False)
        for sf in X.SHORTFALL:
            if sf != cal["shortfall"]:
                sens[f"sf_{sf}"] = (dict(cal, shortfall=sf), False)
        sens["pooled"] = (dict(cal), True)
        if cal["demand"] != "ep2":
            sens["ep2"] = (dict(cal, demand="ep2"), False)
        for name, (spec, pooled) in sens.items():
            for Y in X.TEST_YEARS:
                out.append((name, spec, pooled, "R1", Y, False))
    return out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    tl = tasks(which)
    print(f"{len(tl)} tasks", flush=True)
    t0 = time.time()
    with Pool(6, initializer=init) as pool:
        for i, msg in enumerate(pool.imap_unordered(run_task, tl)):
            print(f"[{i + 1}/{len(tl)} {time.time() - t0:.0f}s] {msg}", flush=True)


if __name__ == "__main__":
    main()
