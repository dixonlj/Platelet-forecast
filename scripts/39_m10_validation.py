#!/usr/bin/env python3
"""Milestone 10, step 4 (prereg Section 2.4.5): validate the chosen calibration on
Aachen 2012-2018, STANDING ORDER ONLY, R1, k matched to each year's recorded short days.
Writes and fingerprints a dated validation report BEFORE any other forecast is run
through the new simulation.

Pass rules: A1 pooled waste within +/-1.5 points of 9.74%; A2 pooled emergency units per
short day within +/-25% of 8.82 (6.6 to 11.0); A3 TVD of weekday waste shares <= 0.20.
A4 (descriptive): yearly correlation and MAE of simulated vs recorded waste; per-year
emergency units. Calibration passes if A1, A2 and A3 all pass.

Educational / advisory only. Public Aachen data. Not clinical.
Run: OMP_NUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python scripts/39_m10_validation.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m10 as X

OUT = X.OUT


def main():
    ch = json.loads((OUT / "38_calibration_choice.json").read_text())
    spec = {k: ch[k] for k in ("calendar", "p2", "p3", "demand", "shortfall", "lag")}
    df, y, _ = L.load_series()
    rec, rec_sh = X.recorded(df, X.TEST_YEARS)
    W_rec = 100 * rec.waste_units.sum() / rec.demand.sum()
    E_rec = rec.emergency_units.sum() / rec.short_days.sum()
    assert abs(W_rec - 9.74) < 0.005 and abs(E_rec - 8.82) < 0.005
    assert list(rec.short_days) == [40, 31, 21, 38, 35, 42, 31]
    s09 = X.load_module("s09", "09_reality_check.py")
    so = s09.standing_order_fc(y)
    wa = X.m2.baseline_forecasts(y)["dow4"]
    win = {n: X.m2.window_sum(so, n).fillna(X.m2.window_sum(wa, n)) for n in (2, 3, 4)}
    cfg = X.make_cfg(spec)
    tab = X.make_window_fn(X.CALENDARS[spec["calendar"]])
    rows, wd_tot = [], np.zeros(7)
    for Y in X.TEST_YEARS:
        units = {n: X.mae_ntotal(y, so, n, X.prev_year_origins(y, Y)) for n in (2, 3, 4)}
        dr = X.draws_for(y, cfg, Y)
        tgt = int(rec.set_index("year").loc[Y, "short_days"])
        r = X.run_policy(dr, win, units, cfg, tab, need_reach=tgt)
        m = X.matched_summary(r, tgt)
        st = np.array(m["status"])
        wd = np.nanmean(m["waste_dow"], axis=0)
        wd_tot += wd
        rows.append(dict(year=Y, target_short_days=tgt, sim_waste_pct=float(np.nanmean(m["waste_pct"])),
                         sim_waste_units=float(np.nanmean(m["waste_units"])),
                         sim_emergency_units=float(np.nanmean(m["short_units"])),
                         sim_short_days=float(np.nanmean(m["short_days"])),
                         sim_k=float(np.nanmean(m["k"])), runs_matched=int((st != "unmatched").sum()),
                         runs_below_target_at_k0=int((st == "below_at_k0").sum()),
                         rec_waste_pct=float(rec.set_index("year").loc[Y, "waste_pct"]),
                         rec_emergency_units=int(rec.set_index("year").loc[Y, "emergency_units"]),
                         demand=int(rec.set_index("year").loc[Y, "demand"]),
                         **{f"sigma_n{n}": u for n, u in units.items()}))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "39_validation_per_year.csv", index=False)
    W = 100 * t.sim_waste_units.sum() / t.demand.sum()
    E = t.sim_emergency_units.sum() / t.sim_short_days.sum()
    sh = X.lag_shares(wd_tot, spec["lag"])
    TVD = 0.5 * np.abs(sh - rec_sh).sum()
    A1, A2, A3 = abs(W - W_rec) <= 1.5, 0.75 * E_rec <= E <= 1.25 * E_rec, TVD <= 0.20
    corr = float(np.corrcoef(t.sim_waste_pct, t.rec_waste_pct)[0, 1])
    mae = float(np.abs(t.sim_waste_pct - t.rec_waste_pct).mean())
    res = dict(spec=spec, W_sim=W, W_rec=W_rec, A1_pass=bool(A1), E_sim=E, E_rec=E_rec, A2_pass=bool(A2),
               TVD=TVD, A3_pass=bool(A3), calibration_passes=bool(A1 and A2 and A3),
               A4_yearly_corr=corr, A4_yearly_mae=mae,
               sim_shares=list(map(float, sh)), rec_shares=list(map(float, rec_sh)),
               saved_at=datetime.now().astimezone().isoformat(timespec="seconds"))
    (OUT / "39_validation_result.json").write_text(json.dumps(res, indent=2))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    lines = [
        "# Validation report (preregistered step 4), Aachen 2012-2018, standing order only, R1",
        "", f"Saved: {res['saved_at']} (box time, America/New_York).",
        "No forecast other than the standing order has been run through the new simulation at this point.",
        "", f"Configuration: {json.dumps(spec)}", "",
        f"- A1 mean waste: simulated {W:.2f}% vs recorded {W_rec:.2f}% (pass if within 1.5 points): "
        f"{'PASS' if A1 else 'FAIL'}",
        f"- A2 emergency units per short day: simulated {E:.2f} vs recorded {E_rec:.2f} (pass if 6.6 to 11.0): "
        f"{'PASS' if A2 else 'FAIL'}",
        f"- A3 weekday waste pattern: TVD {TVD:.3f} (pass if <= 0.20): {'PASS' if A3 else 'FAIL'}",
        "  - simulated shares: " + ", ".join(f"{d} {100 * v:.1f}" for d, v in zip(days, sh)),
        "  - recorded shares:  " + ", ".join(f"{d} {100 * v:.1f}" for d, v in zip(days, rec_sh)),
        f"- A4 (descriptive): yearly correlation simulated vs recorded waste {corr:.2f}; yearly MAE {mae:.2f} points",
        "", f"**Calibration {'PASSES' if res['calibration_passes'] else 'FAILS'} the preregistered validation.**", "",
        t.round(2).to_string(index=False), "",
    ]
    (OUT / "39_validation_report.md").write_text("\n".join(lines))
    h = {f: hashlib.sha256((OUT / f).read_bytes()).hexdigest()
         for f in ("39_validation_report.md", "39_validation_result.json", "39_validation_per_year.csv")}
    with open(OUT / "39_validation_report.md", "a") as fh:
        fh.write("## File fingerprints (SHA-256)\n" + "\n".join(f"- results/m10/{k}: {v}" for k, v in h.items()) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
