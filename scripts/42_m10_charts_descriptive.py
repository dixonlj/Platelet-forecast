#!/usr/bin/env python3
"""Milestone 10: descriptive forecast accuracy (already known; descriptive only, prereg 4.2)
and the simple charts for the revision results. One idea per chart, takeaway in the title.
Educational / advisory only. Public data. Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/42_m10_charts_descriptive.py
"""
from __future__ import annotations

import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import lib_m10 as X

OUT = X.OUT
CH = X.P / "charts"
S2 = X.P / "study2/results/s2m10"
NAME = {"so": "Standing order", "wa4": "4-week weekday average", "gb": "Gradient boosting",
        "dgb": "Detrended gradient boosting", "sarima": "SARIMA", "cb": "Chronos-Bolt"}
plt.rcParams.update({"font.size": 15, "axes.spines.top": False, "axes.spines.right": False})


def foot(fig, text):
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(text, 120)), ha="center", va="bottom", fontsize=10.5, color="#444")


def descriptive_mae():
    s40 = X.load_module("s40", "40_m10_run_comparisons.py")
    df, y, authors, wa, gb, gd, sar, chron, stand = s40.load_forecasts()
    ch = json.loads((OUT / "38_calibration_choice.json").read_text())
    tab = X.make_window_fn(X.CALENDARS[ch["calendar"]])
    rows = []
    for Y in X.TEST_YEARS:
        fcY = {"so": stand, "wa4": wa, "gb": gb[Y - 1], "dgb": gd[Y - 1], "sarima": sar[Y - 1], "cb": chron}
        org = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        for k, fc in fcY.items():
            r = dict(year=Y, policy=k, mae_1day=X.m2.mae(y.shift(-1)[org], fc[1][org]))
            for n in (2, 3, 4):
                a, f = X.m2.actual_window_sum(y, n)[org], X.m2.window_sum(fc, n)[org]
                r[f"mae_{n}day_total"] = X.m2.mae(a, f)
                od = [d for d in org if tab[d.dayofweek] == n]
                r[f"bias_{n}day_orders"] = float(np.mean(f[od] - a[od])) if od else np.nan
            rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "42_descriptive_accuracy_by_year.csv", index=False)
    s = t.groupby("policy").mean(numeric_only=True).drop(columns="year").round(2)
    s.to_csv(OUT / "42_descriptive_accuracy_mean_2012_2018.csv")
    return s


def chart_validation():
    v = pd.read_csv(OUT / "39_validation_per_year.csv")
    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.plot(v.year, v.rec_waste_pct, "o-", color="#222", lw=3, ms=9, label="Recorded at the hospital")
    ax.plot(v.year, v.sim_waste_pct, "s--", color="#d95f02", lw=3, ms=9, label="Calibrated simulation (standing order)")
    ax.set_ylim(0, 15); ax.set_ylabel("Platelets wasted (% of units transfused)")
    ax.set_xticks(v.year)
    ax.legend(frameon=False, fontsize=14, loc="upper left")
    ax.set_title("The calibrated simulation failed its pre-set check:\nit wastes about half as much as Aachen recorded", fontsize=17)
    foot(fig, "Aachen 2012-2018 (validation years, not used for calibration). Standing order only, cushion matched to each "
              "year's recorded short days. Pre-set pass rule: within 1.5 points of 9.7% overall; simulated 5.2%. Emergency "
              "size and weekday pattern also failed. Simulation, not real ordering. Public data (Schilling et al., JMIR Med Inform 2022).")
    fig.tight_layout(rect=(0, 0.09, 1, 1)); fig.savefig(CH / "m10_calibration_validation.png", dpi=150); plt.close(fig)


def forest(rows, path, title, xlabel, mmd, footnote, xlim):
    fig, ax = plt.subplots(figsize=(12, 6.8))
    n = len(rows)
    if mmd is not None:
        ax.axvspan(-mmd, mmd, color="#dddddd", alpha=0.7, zorder=0)
        ax.text(0, n - 0.35, "smaller than the minimum\nmeaningful difference", ha="center", va="bottom", fontsize=11, color="#555", bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
    ax.axvline(0, color="#333", lw=1)
    for i, (lab, m, lo, hi) in enumerate(rows):
        yy = n - 1 - i
        ax.plot([lo, hi], [yy, yy], color="#1b6ca8", lw=4, solid_capstyle="round")
        ax.plot(m, yy, "o", color="#1b6ca8", ms=13)
        ax.text(hi + 0.04 * (xlim[1] - xlim[0]), yy, f"{m:+.2f} ({lo:+.2f} to {hi:+.2f})", va="center", fontsize=12.5)
    ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=15)
    ax.set_xlim(*xlim); ax.set_ylim(-0.7, n + 0.4)
    ax.set_xlabel(xlabel)
    ax.text(xlim[0], -0.65, "<- wastes less than the standing order", fontsize=11.5, color="#555", va="bottom")
    ax.text(xlim[1], -0.65, "wastes more ->", fontsize=11.5, color="#555", ha="right", va="bottom")
    ax.set_title(title, fontsize=17)
    foot(fig, footnote)
    fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(path, dpi=150); plt.close(fig)


def chart_primary():
    p = pd.read_csv(OUT / "41_primary_H1.csv")
    rows = [(NAME[r.policy], r.mu, r.ci_lo, r.ci_hi) for r in p.itertuples()]
    forest(rows, CH / "m10_primary_vs_standing_order.png",
           "Aachen: no forecast clearly wasted less\nthan last year's standing order",
           "Difference in waste vs standing order (percentage points, 95% CI)", 0.5,
           "Preregistered primary analysis. Aachen 2012-2018, calibrated simulation (which failed its validation check), cushion "
           "sized to each order's days, matched to each year's recorded short days, 30 runs. Mixed model over 84 four-week blocks; "
           "Holm-adjusted p >= 0.75 for all four. Grey band: +/-0.5 points. Simulation only.", (-1.5, 1.5))


def chart_stanford():
    p = pd.read_csv(S2 / "11_primary_stanford.csv")
    nm = {"gb_noclin": "Gradient boosting", "dgb": "Detrended gradient boosting", "sarima": "SARIMA", "cb": "Chronos-Bolt"}
    rows = [(nm[r.policy], r.mean_block_diff, r.boot_ci_lo, r.boot_ci_hi) for r in p.itertuples()]
    mmd = float(p.mmd_points.iloc[0])
    forest(rows, CH / "m10_stanford_vs_standing_order.png",
           "Stanford: forecasts wasted less than the standing order,\nbut the evidence is too uncertain to count",
           "Difference in waste vs standing order (percentage points, 95% CI)", mmd,
           f"Preregistered replication. Stanford public pip data, 8 Jan 2014 - 31 May 2015 (509 days), shortages on 5 days (1%). "
           f"Standing order wasted {p.window_waste_base.iloc[0]:.1f}%. Moving-block bootstrap over 18 four-week blocks; "
           f"Holm-adjusted p 0.10 to 0.22. Grey band: +/-6% of the standing order's waste ({mmd:.2f} points). Simulation only.",
           (-5, 3.2))


def chart_tradeoff():
    c = pd.read_csv(OUT / "41_tradeoff_curves_pooled.csv", index_col=0)
    fc = c[["gb", "dgb", "sarima", "cb"]]
    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.fill_between(c.index, fc.min(axis=1), fc.max(axis=1), color="#1b6ca8", alpha=0.25,
                    label="Range of the four forecasts")
    ax.plot(c.index, c.so, color="#222", lw=3.5, label="Standing order")
    ax.plot(c.index, c.wa4, color="#d95f02", lw=3, ls="--", label="4-week weekday average")
    ax.set_xlabel("Short days per year (days needing an emergency order)")
    ax.set_ylabel("Platelets wasted (% of units transfused)")
    ax.legend(frameon=False, fontsize=14)
    ax.set_ylim(0, max(8, float(c.max().max()) * 1.1))
    ax.set_title("Accepting more short days cuts waste for every method;\nthe methods differ by less than one point", fontsize=17)
    foot(fig, "Aachen 2012-2018, calibrated simulation (failed validation), cushion sized to each order's days. Average over 7 "
              "years and 30 runs. Preregistered secondary analysis (RQ3). Simulation only.")
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(CH / "m10_tradeoff_curves.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    print(descriptive_mae())
    chart_validation(); chart_primary(); chart_stanford(); chart_tradeoff()
    print("charts written")
