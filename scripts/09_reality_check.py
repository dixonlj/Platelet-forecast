#!/usr/bin/env python3
"""
Milestone 5, step 2: reality check. Can the simulation reproduce what the
hospital actually recorded?

The public Aachen file has daily units transfused, wasted and bought in an
emergency, but NOT the hospital's daily orders or stock on hand. So the
hospital's real ordering cannot be replayed. Instead we simulate two
"hospital-like" rules and calibrate them to the hospital's own number of
short days in each year 2012-2018:

  A. Standing weekday order: order up to last year's average use for each
     weekday (a fixed par per weekday, updated once a year), plus a cushion.
  B. 4-week weekday average (a common, simple rolling rule).

At the hospital's short days we compare simulated waste and emergency units
with the hospital's recorded waste and emergency purchases, and report the gap.
Then, for the standing order, we ask how short the remaining shelf life on
arrival would have to be for the simulation to reach the hospital's waste.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/09_reality_check.py
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

import lib_m4 as L
import lib_m5 as M

RES = M.RESULTS
LIFE_SCENARIOS = {
    "base: 70% 4 days, 30% 3 days": {4: 0.7, 3: 0.3},
    "all 3 days": {3: 1.0},
    "70% 3 days, 30% 2 days": {3: 0.7, 2: 0.3},
    "50% 3 days, 50% 2 days": {3: 0.5, 2: 0.5},
}


def standing_order_fc(y: pd.Series) -> pd.DataFrame:
    """Forecast for target day = previous calendar year's mean use on that weekday."""
    yr_dow = y.groupby([y.index.year, y.index.dayofweek]).mean()
    cols = {}
    for h in range(1, 5):
        tgt = y.index + pd.Timedelta(days=h)
        cols[h] = [yr_dow.get((d.year - 1, d.dayofweek), np.nan) for d in tgt]
    return pd.DataFrame(cols, index=y.index)


def main() -> None:
    df, y, _ = L.load_series()
    base = L.m2.baseline_forecasts(y)
    fcs = {"standing": standing_order_fc(y), "dow4": base["dow4"]}
    rows = []
    for Y in M.YEARS:
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        sigma = L.sigma_for_year(y, fcs, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcs.items()}
        for lname, life in LIFE_SCENARIOS.items():
            if not lname.startswith("base") and Y not in M.YEARS:  # all years run
                continue
            cfg = deepcopy(L.m3.BASE)
            cfg["life_on_arrival"] = life
            res = L.run_config(cfg, y, win, sigma, list(fcs), year=Y)
            for k in fcs:
                m = M.match_at(res[k], hosp["shortage_days"], hosp["demand"])
                rows.append({
                    "year": Y, "life_scenario": lname, "policy": k,
                    "target_short_days": hosp["shortage_days"],
                    "sim_waste_pct": m["waste_pct"].mean(),
                    "sim_waste_p05": M.p5(m["waste_pct"]), "sim_waste_p95": M.p95(m["waste_pct"]),
                    "sim_waste_units": m["waste_units"].mean(),
                    "sim_emergency_units": m["short_units"].mean(),
                    "sim_monday_share": m["monday_share"].mean(),
                    "hosp_waste_pct": hosp["waste_pct"], "hosp_waste_units": hosp["waste_units"],
                    "hosp_emergency_units": hosp["short_units"],
                    "gap_waste_pct_points": hosp["waste_pct"] - m["waste_pct"].mean(),
                    "gap_waste_units": hosp["waste_units"] - m["waste_units"].mean(),
                    "gap_emergency_units": hosp["short_units"] - m["short_units"].mean(),
                    "n_seeds": int(m["waste_pct"].notna().sum()),
                })
        print(Y, "done")
    out = pd.DataFrame(rows)
    out.to_csv(RES / "09_reality_check.csv", index=False)

    b = out[out["life_scenario"].str.startswith("base")]
    summ = b.groupby("policy").agg(
        years=("year", "count"),
        mean_sim_waste_pct=("sim_waste_pct", "mean"),
        mean_hosp_waste_pct=("hosp_waste_pct", "mean"),
        mean_gap_points=("gap_waste_pct_points", "mean"),
        min_gap_points=("gap_waste_pct_points", "min"),
        max_gap_points=("gap_waste_pct_points", "max"),
        years_sim_below_hosp=("gap_waste_pct_points", lambda s: int((s > 0).sum())),
        years_sim_emergency_below_hosp=("gap_emergency_units", lambda s: int((s > 0).sum())),
        mean_sim_monday_share=("sim_monday_share", "mean"),
        mean_sim_emergency=("sim_emergency_units", "mean"),
        mean_hosp_emergency=("hosp_emergency_units", "mean"),
        total_sim_waste_units=("sim_waste_units", "sum"),
        total_hosp_waste_units=("hosp_waste_units", "sum"),
        total_sim_emergency=("sim_emergency_units", "sum"),
        total_hosp_emergency=("hosp_emergency_units", "sum"),
    ).reset_index()
    summ.to_csv(RES / "09_reality_check_summary.csv", index=False)
    life = out[out["policy"] == "standing"].groupby("life_scenario").agg(
        mean_sim_waste_pct=("sim_waste_pct", "mean"),
        mean_hosp_waste_pct=("hosp_waste_pct", "mean"),
        mean_gap_points=("gap_waste_pct_points", "mean")).reset_index()
    life.to_csv(RES / "09_life_on_arrival_calibration.csv", index=False)

    corr = {p: float(np.corrcoef(g["sim_waste_pct"], g["hosp_waste_pct"])[0, 1]) for p, g in b.groupby("policy")}
    pd.DataFrame([{"policy": k, "corr_sim_vs_hosp_waste_by_year": v} for k, v in corr.items()]).to_csv(
        RES / "09_year_to_year_correlation.csv", index=False)

    txt = ["=== Milestone 5 step 2: reality check ===",
           b.round(2).to_string(index=False), "", summ.round(2).to_string(index=False), "",
           life.round(2).to_string(index=False), "", f"Year-to-year correlation: {corr}"]
    print("\n".join(txt))
    (RES / "09_run_log.txt").write_text("\n".join(txt) + "\n")
    chart(b)


def chart(b: pd.DataFrame) -> None:
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s = b[b["policy"] == "standing"].sort_values("year")
    years = s["year"].tolist()
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(13, 7.2))
    ax.bar(x - 0.2, s["hosp_waste_pct"], 0.38, color="#222222", label="What the hospital recorded")
    ax.bar(x + 0.2, s["sim_waste_pct"], 0.38, color="#80b1d3", label="Simulation of a hospital-like standing order")
    ax.errorbar(x + 0.2, s["sim_waste_pct"], yerr=[s["sim_waste_pct"] - s["sim_waste_p05"],
                s["sim_waste_p95"] - s["sim_waste_pct"]], fmt="none", ecolor="black", capsize=3)
    sim_m, hosp_m = s["sim_waste_pct"].mean(), s["hosp_waste_pct"].mean()
    worst = s["gap_waste_pct_points"].abs().max()
    ax.set_title(f"On average the simulation came close to the real hospital ({sim_m:.1f}% vs {hosp_m:.1f}% wasted),\n"
                 f"but single years missed by up to {worst:.1f} points, in both directions", fontsize=17, pad=12)
    ax.set_xticks(x, [str(v) for v in years], fontsize=15)
    ax.tick_params(axis="y", labelsize=14)
    ax.set_ylabel("Platelets thrown away\n(% of units used)", fontsize=16)
    ax.set_ylim(0, max(s["hosp_waste_pct"].max(), s["sim_waste_p95"].max()) * 1.3)
    ax.legend(fontsize=14, frameon=False, loc="upper center", ncol=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    foot = ("Aachen hospital public data, 8 Jan to 18 Dec of each year. The simulated order is set so it has the "
            "hospital's own number of short days. Black lines = 5th to 95th percentile of 30 simulated runs. "
            "The simulation leaves out special-order units, transfers, quality-control losses and real ordering choices.")
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(foot, 120)), ha="center", va="bottom", fontsize=11, color="#444444")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(M.CHARTS / "m5_reality_check.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
