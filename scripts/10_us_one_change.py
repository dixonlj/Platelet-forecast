#!/usr/bin/env python3
"""
Milestone 5, step 3: separate the US-rule effects, one change at a time.

Script 07 changed three things at once (ABO order, blood-group shares and
shelf life) and kept Aachen's German delivery calendar (no deliveries Sun/Mon,
no orders Fri/Sat, 2-day lead). Here, on the same 2018 Aachen demand and the
same 30 seeds, each US change is added alone, then all together, and finally
with a daily delivery calendar (an order every evening, arriving two days later).

Educational / advisory only. Still German demand, not a US hospital.
Run: PYTHONPATH=scripts .venv/bin/python scripts/10_us_one_change.py
"""
from __future__ import annotations

from copy import deepcopy

import pandas as pd

import lib_m4 as L
import lib_m5 as M

YEAR = 2018
MODELS = ["dow4", "hgbr"]
US_LIFE = {4: 0.5, 5: 0.5}   # 50/50 5-day PRT (4 usable) and 7-day LVDS (5 usable), as in script 07


def cfg_with(**chg):
    c = deepcopy(L.m3.BASE)
    c.update(chg)
    return c


SCEN = {
    "German rules (base)": cfg_with(),
    "Only US shelf life (50/50 5-day and 7-day)": cfg_with(life_on_arrival=US_LIFE),
    "Only US ABO order (plasma-compatible first)": cfg_with(abo_mode="us_plasma_first",
                                                            rhdneg_female_le50_share=0.15),
    "Only US blood-group shares": cfg_with(group_share=dict(L.US_GROUP_SHARE)),
    "All three US changes (German calendar)": cfg_with(life_on_arrival=US_LIFE, abo_mode="us_plasma_first",
                                                       rhdneg_female_le50_share=0.15,
                                                       group_share=dict(L.US_GROUP_SHARE)),
}


def main() -> None:
    df, y, _ = L.load_series()
    _, ev0, ev1 = L.year_window(YEAR)
    hosp = L.hospital_actual(df, ev0, ev1)
    feat = L.m2.hgbr_feature_table(y)
    base = L.m2.baseline_forecasts(y)
    fcs = {"dow4": base["dow4"], "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 1}-12-31"))}
    fcs_s = {"dow4": base["dow4"], "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 2}-12-31"))}
    sigma = L.sigma_for_year(y, fcs_s, YEAR)
    win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcs.items()}

    rows = []
    def run(name, cfg):
        res = L.run_config(cfg, y, win, sigma, MODELS, year=YEAR)
        for k in MODELS:
            m = M.match_at(res[k], hosp["shortage_days"], hosp["demand"])
            rows.append({"scenario": name, "model": k, "target_short_days": hosp["shortage_days"],
                         "waste_pct_mean": m["waste_pct"].mean(), "waste_p05": M.p5(m["waste_pct"]),
                         "waste_p95": M.p95(m["waste_pct"]),
                         "emergency_units_mean": m["short_units"].mean(),
                         "wasted_plus_emergency_mean": m["lost_units"].mean(),
                         "n_seeds": int(m["waste_pct"].notna().sum())})
        print("done:", name)

    for name, cfg in SCEN.items():
        run(name, cfg)
    # Daily delivery calendar: order every evening, covering the next 2 days.
    old = L.m2.order_window
    L.m2.order_window = lambda day: 2
    try:
        run("All three US changes + daily deliveries", SCEN["All three US changes (German calendar)"])
        run("German rules + daily deliveries", SCEN["German rules (base)"])
    finally:
        L.m2.order_window = old

    out = pd.DataFrame(rows)
    out.to_csv(M.RESULTS / "10_us_one_change.csv", index=False)
    txt = out.round(2).to_string(index=False)
    print(txt)
    (M.RESULTS / "10_run_log.txt").write_text("=== US rules one change at a time, 2018, 31 short days ===\n" + txt + "\n")
    chart(out)


def chart(out):
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    order = [("German rules (base)", "German rules\n(starting point)"),
             ("Only US blood-group shares", "Only US\nblood-type mix"),
             ("Only US ABO order (plasma-compatible first)", "Only US\nbackup order"),
             ("Only US shelf life (50/50 5-day and 7-day)", "Only longer\nUS shelf life"),
             ("German rules + daily deliveries", "Only daily\ndeliveries"),
             ("All three US changes (German calendar)", "All three\nUS changes"),
             ("All three US changes + daily deliveries", "All three +\ndaily deliveries")]
    g = out[out["model"] == "hgbr"].set_index("scenario")
    v = [g.loc[s, "waste_pct_mean"] for s, _ in order]
    lo = [g.loc[s, "waste_pct_mean"] - g.loc[s, "waste_p05"] for s, _ in order]
    hi = [g.loc[s, "waste_p95"] - g.loc[s, "waste_pct_mean"] for s, _ in order]
    cols = ["#999999", "#bebada", "#bebada", "#fb8072", "#fdb462", "#80b1d3", "#80b1d3"]
    fig, ax = plt.subplots(figsize=(13, 7.2))
    x = np.arange(len(order))
    ax.bar(x, v, 0.65, color=cols)
    ax.errorbar(x, v, yerr=[lo, hi], fmt="none", ecolor="black", capsize=4)
    for xi, vi in zip(x, v):
        ax.text(xi, vi + max(hi) + 0.25, f"{vi:.1f}%", ha="center", fontsize=14)
    ax.set_xticks(x, [b for _, b in order], fontsize=12.5)
    ax.set_ylabel("Platelets thrown away\n(% of units used)", fontsize=16)
    ax.tick_params(axis="y", labelsize=14)
    ax.set_ylim(0, max(v) * 1.35)
    ax.set_title("Longer shelf life, and separately daily deliveries, each cut waste about in half;\n"
                 "the US blood-type rules alone changed little", fontsize=17, pad=12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    foot = ("Same German (Aachen) 2018 demand in every bar; machine-learning forecast; 31 short days as at the hospital. "
            "Black lines = 5th to 95th percentile of 30 simulated runs. This is not a US hospital. A learning exercise only.")
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(foot, 120)), ha="center", va="bottom", fontsize=11, color="#444444")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(M.CHARTS / "m5_us_one_change.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
