#!/usr/bin/env python3
"""Milestone 10, step 3 (prereg Section 2.4): calibrate the simulation on Aachen
2009-2011 using the STANDING ORDER ONLY, under the primary rule R1, with k matched
per year and run to each year's recorded short days (25, 26, 40).

Grid (Section 2.4.3): calendar (5) x life on arrival (15) x logging lag (4, applied
after simulation) x demand clustering (3) x delivery shortfalls (3) = 2,700 combinations,
675 distinct simulations per year. All 30 runs (seeds 1000-1029) for every combination
(the full grid takes far less than 48 hours, so the screening rule is not needed).

Loss (Section 2.4.4): ((W-8.25)/1.0)^2 + ((E-6.53)/1.5)^2 + (TVD/0.10)^2.
Tie rule: among L within 5% of the minimum, fewest departures from the v9 base
(Tue-Sat, p2=0, p3=0.30, no lag, unit demand, 10% shortfalls), then lowest L.
No forecast other than the standing order is run here.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: OMP_NUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python scripts/38_m10_calibration.py
"""
from __future__ import annotations

import hashlib
import itertools
import json
import time
from datetime import datetime
from multiprocessing import Pool

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m10 as X

OUT = X.OUT
TARGET_W, TARGET_E = 8.25, 6.53
TARGET_SHARES = np.array([21.9, 12.9, 33.9, 14.8, 13.6, 1.8, 0.9]) / 100

_G = {}


def so_inputs(y):
    s09 = X.load_module("s09", "09_reality_check.py")
    so = s09.standing_order_fc(y)
    wa = X.m2.baseline_forecasts(y)["dow4"]
    win, fallback = {}, {}
    for n in (2, 3, 4):
        w, d = X.m2.window_sum(so, n), X.m2.window_sum(wa, n)
        win[n] = w.fillna(d)
        fallback[n] = w.isna()
    units = {}
    for Y in X.CAL_YEARS:
        if Y == 2009:   # prereg 2.3.2: sigma for 2009 taken from 2009 itself (no 2007 data)
            org = y.loc[pd.Timestamp("2008-12-31"):pd.Timestamp("2009-12-30")].index
        else:
            org = X.prev_year_origins(y, Y)
        units[Y] = {n: X.mae_ntotal(y, so, n, org) for n in (2, 3, 4)}
    return so, win, fallback, units


def init():
    df, y, _ = L.load_series()
    so, win, fb, units = so_inputs(y)
    rec, _ = X.recorded(df, X.CAL_YEARS)
    _G.update(y=y, win=win, units=units, rec=rec.set_index("year"))


def run_combo(key):
    cal, p2, p3, dem, sf = key
    y, win, units, rec = _G["y"], _G["win"], _G["units"], _G["rec"]
    spec = dict(calendar=cal, p2=p2, p3=p3, demand=dem, shortfall=sf, lag="0")
    cfg = X.make_cfg(spec)
    tab = X.make_window_fn(X.CALENDARS[cal])
    out = []
    for Y in X.CAL_YEARS:
        dr = X.draws_for(y, cfg, Y)
        target = int(rec.loc[Y, "short_days"])
        r = X.run_policy(dr, win, units[Y], cfg, tab, need_reach=target)
        m = X.matched_summary(r, target)
        st = np.array(m["status"])
        ok = st != "unmatched"
        out.append(dict(calendar=cal, p2=p2, p3=p3, demand=dem, shortfall=sf, year=Y, target=target,
                        n_matched=int(ok.sum()), n_below_k0=int((st == "below_at_k0").sum()),
                        extended=bool(r["extended"]),
                        waste_units=float(np.nanmean(m["waste_units"])),
                        demand_units=float(np.nanmean(m["demand"])),
                        short_units=float(np.nanmean(m["short_units"])),
                        short_days=float(np.nanmean(m["short_days"])),
                        k=float(np.nanmean(m["k"])),
                        **{f"wdow{i}": float(v) for i, v in enumerate(np.nanmean(m["waste_dow"], axis=0))}))
    return out


def tvd(a, b):
    return 0.5 * np.abs(np.asarray(a) - np.asarray(b)).sum()


def departures(r):
    b = X.V9_BASE
    return int(r.calendar != b["calendar"]) + int(r.p2 != b["p2"]) + int(abs(r.p3 - b["p3"]) > 1e-9) \
        + int(r.lag != b["lag"]) + int(r.demand != b["demand"]) + int(r.shortfall != b["shortfall"])


def main():
    t0 = time.time()
    df, y, _ = L.load_series()
    rec, rec_sh = X.recorded(df, X.CAL_YEARS)
    W_rec = 100 * rec.waste_units.sum() / rec.demand.sum()
    E_rec = rec.emergency_units.sum() / rec.short_days.sum()
    assert abs(W_rec - TARGET_W) < 0.005 and abs(E_rec - TARGET_E) < 0.005, (W_rec, E_rec)
    assert np.abs(np.round(100 * rec_sh, 1) - 100 * TARGET_SHARES).max() < 0.051, rec_sh
    assert list(rec.short_days) == [25, 26, 40]
    so, win, fb, units = so_inputs(y)
    keys = list(itertools.product(list(X.CALENDARS), X.P2_GRID, X.P3_GRID, list(X.DEMAND), list(X.SHORTFALL)))
    assert len(keys) == 675
    with Pool(6, initializer=init) as pool:
        res = []
        for i, part in enumerate(pool.imap_unordered(run_combo, keys, chunksize=2)):
            res += part
            if (i + 1) % 75 == 0:
                print(f"{i + 1}/675 combos, {time.time() - t0:.0f}s", flush=True)
    per_year = pd.DataFrame(res).sort_values(["calendar", "p2", "p3", "demand", "shortfall", "year"])
    per_year.to_csv(OUT / "38_calibration_per_year.csv", index=False)

    rows = []
    for key, g in per_year.groupby(["calendar", "p2", "p3", "demand", "shortfall"], sort=False):
        W = 100 * g.waste_units.sum() / g.demand_units.sum()
        E = g.short_units.sum() / g.short_days.sum()
        wd = g[[f"wdow{i}" for i in range(7)]].sum().values
        for lag in X.LAGS:
            sh = X.lag_shares(wd, lag)
            T = tvd(sh, rec_sh)   # recorded shares from the file (match the prereg table to 0.1 point)
            Ls = ((W - TARGET_W) / 1.0) ** 2 + ((E - TARGET_E) / 1.5) ** 2 + (T / 0.10) ** 2
            rows.append(dict(zip(["calendar", "p2", "p3", "demand", "shortfall"], key), lag=lag,
                             W_sim=W, E_sim=E, TVD=T, loss=Ls, min_runs_matched=int(g.n_matched.min()),
                             runs_below_target_at_k0=int(g.n_below_k0.sum()), k_extended=bool(g.extended.any()),
                             **{f"share_{d}": v for d, v in zip(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], sh)}))
    grid = pd.DataFrame(rows)
    assert len(grid) == 2700
    grid["departures_from_v9"] = grid.apply(departures, axis=1)
    lmin = grid.loss.min()
    tied = grid[grid.loss <= 1.05 * lmin].sort_values(["departures_from_v9", "loss"])
    chosen = tied.iloc[0]
    grid = grid.sort_values("loss").reset_index(drop=True)
    grid.to_csv(OUT / "38_calibration_grid.csv", index=False)
    v9 = grid[(grid.calendar == "tue_sat") & (grid.p2 == 0) & (np.isclose(grid.p3, 0.30)) & (grid.lag == "0")
              & (grid.demand == "unit") & (grid.shortfall == "v9_10pct")].iloc[0]
    choice = {k: (v.item() if hasattr(v, "item") else v) for k, v in chosen.items()}
    choice["n_combinations_within_5pct"] = int(len(tied))
    choice["chosen_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    (OUT / "38_calibration_choice.json").write_text(json.dumps(choice, indent=2, default=str))
    gh = hashlib.sha256((OUT / "38_calibration_grid.csv").read_bytes()).hexdigest()
    ch = hashlib.sha256((OUT / "38_calibration_choice.json").read_bytes()).hexdigest()
    fb_n = {n: int(fb[n].loc[pd.Timestamp("2008-12-25"):pd.Timestamp("2011-12-18")].sum()) for n in (2, 3, 4)}
    lines = [
        "# Calibration report (preregistered step 3), Aachen 2009-2011, standing order only",
        "",
        f"Saved: {choice['chosen_at']} (box time, America/New_York). Run time {time.time() - t0:.0f} s.",
        "No forecast other than the standing order has been run through the new simulation at this point.",
        "",
        "## Recorded targets (scoring windows 2009-2011, pooled, from the public file)",
        f"- Waste {W_rec:.2f}%; emergency units per short day {E_rec:.2f}; short days per year {list(rec.short_days)}",
        "- Weekday shares of waste (Mon..Sun): " + ", ".join(f"{100 * v:.1f}" for v in rec_sh),
        "",
        "## Standing-order cushion units sigma_SO(n) (MAE of n-day totals, previous year; 2009 from 2009 itself)",
        *[f"- {Y}: " + ", ".join(f"n={n}: {u:.2f}" for n, u in units[Y].items()) for Y in X.CAL_YEARS],
        f"- Forecast origins that fell back to the 4-week weekday average (warm-up of 2009 only, no 2007 data): "
        f"{fb_n}",
        "",
        "## Grid",
        "- 2,700 combinations (675 simulations per year, logging lag applied afterwards), 30 runs each.",
        f"- Loss minimum {lmin:.3f}; {len(tied)} combination(s) within 5% of it.",
        f"- Runs never matched (dropped): {int((30 - per_year.n_matched).sum())} of {len(per_year) * 30} run-years. "
        f"Run-years already below the target at k = 0 (flagged, k = 0 used): {int(per_year.n_below_k0.sum())}.",
        "",
        "## Chosen configuration (tie rule applied)",
        f"- Calendar {X.CAL_LABEL[chosen.calendar]}; life on arrival p2={chosen.p2}, p3={chosen.p3}, "
        f"p4={1 - chosen.p2 - chosen.p3:.2f}; logging lag {chosen.lag}; demand {chosen.demand}; shortfalls {chosen.shortfall}.",
        f"- W_sim {chosen.W_sim:.2f}% (target {TARGET_W}), E_sim {chosen.E_sim:.2f} (target {TARGET_E}), "
        f"TVD {chosen.TVD:.3f}; loss {chosen.loss:.3f}; departures from v9 base {chosen.departures_from_v9}.",
        "- Simulated weekday shares (Mon..Sun): " + ", ".join(
            f"{100 * chosen[f'share_{d}']:.1f}" for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
        "",
        "## For reference: v9 base configuration in the same grid",
        f"- W_sim {v9.W_sim:.2f}%, E_sim {v9.E_sim:.2f}, TVD {v9.TVD:.3f}, loss {v9.loss:.3f} (rank {int(v9.name) + 1} of 2,700).",
        "",
        "## Ten lowest-loss combinations",
        grid.head(10)[["calendar", "p2", "p3", "lag", "demand", "shortfall", "W_sim", "E_sim", "TVD", "loss",
                       "departures_from_v9"]].round(3).to_string(index=False),
        "",
        "## File fingerprints (SHA-256)",
        f"- results/m10/38_calibration_grid.csv: {gh}",
        f"- results/m10/38_calibration_choice.json: {ch}",
    ]
    (OUT / "38_calibration_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
