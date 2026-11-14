#!/usr/bin/env python3
"""Milestone 10, step 2 of the preregistered plan (Section 2.2): test the new code on
the SYNTHETIC teaching series only (data/SYNTHETIC_daily_platelet_demand.csv, clearly
labelled example data), then a timing test on Aachen with the STANDING ORDER ONLY.

Checks:
  1. simulate_m10 with the same cushion for every order (R2-style) reproduces
     lib_m4.simulate exactly (waste, emergency units, short days, weekday arrays),
     for the documented calendar and for Tue-Sun (3-day orders), grouped and pooled,
     standard and expiry-aware ordering.
  2. Block outputs add up to the yearly totals.
  3. match_weights/apply_match reproduces lib_m5.match_at.
Educational / advisory only. Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/37_m10_selftest.py
"""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M
import lib_m10 as X

log = []


def say(s):
    print(s, flush=True); log.append(s)


def main():
    syn = pd.read_csv(X.P / "data/SYNTHETIC_daily_platelet_demand.csv", parse_dates=["date"]).set_index("date")
    y = syn["units_transfused"].astype(float)
    base = X.m2.baseline_forecasts(y)
    fc = base["dow4"]
    win = {n: X.m2.window_sum(fc, n) for n in (2, 3, 4)}
    sigma = 5.0
    say("SYNTHETIC teaching series (not real data), test year 2024")
    for cal in ("tue_sat", "tue_sun"):
        for pooled in (False, True):
            for rule in ("standard", "expiry_aware"):
                if pooled and rule == "expiry_aware":
                    continue
                cfg = X.make_cfg(X.V9_BASE, pooled=pooled)
                tab = X.make_window_fn(X.CALENDARS[cal])
                dr = X.draws_for(y, cfg, 2024, n_seeds=4)
                days, ev0, ev1, D, FILL, U, LIFE = dr
                t0 = time.time()
                a = X.simulate_m10(days, D, FILL, U, LIFE, win, {2: sigma, 3: sigma, 4: sigma}, cfg, X.K_GRID,
                                   ev0, ev1, tab, rule, daily_fc=None)
                t1 = time.time()
                b = L.simulate(days, list(D), list(FILL), list(U), list(LIFE), win[2], win[4], sigma, cfg,
                               k_grid=X.K_GRID, eval_start=ev0, eval_end=ev1, order_rule=rule,
                               order_window_fn=lambda d: tab[d.dayofweek], f3=win[3])
                d1 = np.abs(a["waste_units"] - b["waste_pct"] * a["demand"] / 100).max()
                d2 = np.abs(a["short_units"] - b["short_units"]).max()
                d3 = np.abs(a["short_days"] - b["shortage_days"]).max()
                d4 = np.abs(a["waste_dow"] - b["waste_by_dow"]).max()
                d5 = np.abs(a["blk_waste"].sum(2) - a["waste_units"]).max() + np.abs(a["blk_demand"].sum(2) - a["demand"]).max()
                say(f"  {cal:8s} pooled={pooled!s:5s} {rule:12s}: max diffs waste {d1:.1e} emerg {d2:.1e} "
                    f"short days {d3:.1e} weekday {d4:.1e}; blocks-vs-total {d5:.1e}; m10 {t1 - t0:.1f}s")
                assert max(d1, d2, d3, d4, d5) < 1e-6
                # matching
                ref = M.match_at({"waste_pct": b["waste_pct"], "shortage_days": b["shortage_days"],
                                  "short_units": b["short_units"],
                                  "monday_share_of_short_days": b["monday_share_of_short_days"]},
                                 8, a["demand"][0, 0])
                mm = X.matched_summary(a, 8)
                dd = np.nanmax(np.abs(ref["waste_pct"].values - mm["waste_pct"]))
                say(f"     match_at check (target 8 short days): max diff {dd:.1e}")
                assert dd < 1e-9 or np.isnan(dd)
    # R1 (per-n cushion) differs from R2 when n varies: sanity only
    cfg = X.make_cfg(X.V9_BASE)
    tab = X.make_window_fn(X.CALENDARS["tue_sat"])
    dr = X.draws_for(y, cfg, 2024, n_seeds=4)
    days, ev0, ev1, D, FILL, U, LIFE = dr
    a = X.simulate_m10(days, D, FILL, U, LIFE, win, {2: 5.0, 3: 6.0, 4: 8.0}, cfg, X.K_GRID, ev0, ev1, tab)
    say(f"  R1 sanity (sigma 5/6/8): mean waste % at k=1: {100 * a['waste_units'][:, 4].mean() / a['demand'][0, 0]:.2f}")

    if "--timing" in sys.argv:
        df, ya, _ = L.load_series()
        s09 = X.load_module("s09", "09_reality_check.py")
        so = s09.standing_order_fc(ya)
        winA = {n: X.m2.window_sum(so, n) for n in (2, 3, 4)}
        cfg = X.make_cfg(X.V9_BASE)
        t0 = time.time()
        dr = X.draws_for(ya, cfg, 2010)
        t1 = time.time()
        r = X.run_policy(dr, winA, {2: 8.0, 3: 10.0, 4: 12.0}, cfg, X.make_window_fn(X.CALENDARS["tue_sat"]))
        t2 = time.time()
        say(f"TIMING (Aachen 2010, standing order only, 30 runs): draws {t1 - t0:.1f}s, sim {t2 - t1:.1f}s")
        cfg = X.make_cfg(dict(X.V9_BASE, demand="ep4"))
        t0 = time.time(); dr = X.draws_for(ya, cfg, 2010); t1 = time.time()
        say(f"TIMING episode draws (mean 4): {t1 - t0:.1f}s")
    (X.OUT / "37_selftest_log.txt").write_text("\n".join(log) + "\nALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
