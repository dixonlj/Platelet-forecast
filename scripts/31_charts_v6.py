#!/usr/bin/env python3
"""Draft v6 charts, from results files only (no simulation).

Each chart is drawn twice:
  charts/paper/<name>.png  6.0 in wide, no in-chart title (the paper caption carries the takeaway)
  charts/<name>.png        stand-alone version with the takeaway as the title, for slides and messages
In the yearly-gap charts each point is printed as its two-digit test year ("12" = 2012).

  Figure 1  m9_waste_gap_by_year.png   <- results/m9/27_multiyear_inventory.csv + m5/08 (RNN)
  Figure 2  m9_lost_gap_by_year.png    <- same
  Figure 3  m9_prior_year_cushion.png  <- results/m8/19_prior_year_cushion.csv
  Figure 5  m9_service_level.png       <- results/m9/29_target_tests.csv            (new in v6)
  Figure 6  m9_delivery_calendar.png   <- results/m9/26_weekend_delivery.csv        (new in v6)
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: .venv/bin/python scripts/31_charts_v6.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
OUTP = ROOT / "charts" / "paper"; OUTP.mkdir(parents=True, exist_ok=True)
OUTS = ROOT / "charts"
fams = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({
    "font.family": "Carlito" if "Carlito" in fams else "DejaVu Sans",
    "font.size": 12, "axes.labelsize": 12.5, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "legend.fontsize": 12, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True, "savefig.dpi": 300})
W = 6.0
GREEN, ORANGE, PURPLE, PINK, GREY = "#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#666666"
FOOT = "Public Aachen hospital data, 2012–2018. Simulation, not real-world results. Educational only."


def save(fig, name, title=None, foot_y=-0.04):
    fig.savefig(OUTP / name, dpi=300, bbox_inches="tight", pad_inches=0.04)
    if title:   # stand-alone copy with a takeaway title and source line
        fig.suptitle(title, fontsize=13.5, fontweight="bold", y=1.02, x=0.02, ha="left")
        fig.text(0.02, foot_y, FOOT, fontsize=9.5, color="#555555", ha="left", va="top")
        fig.savefig(OUTS / name, dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def year_points(ax, x0, gaps: pd.Series, half=0.32, fs=8.5):
    xs = np.linspace(x0 - half, x0 + half, len(gaps))
    for x, (yr, g) in zip(xs, gaps.items()):
        ax.text(x, g, f"{int(yr) % 100:02d}", ha="center", va="center", fontsize=fs, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="#333333", lw=0.6), zorder=4)


MS = ["hgbr", "chronos", "sarima", "rnn"]
GLAB = {"hgbr": "Gradient\nboosting", "chronos": "Chronos-Bolt\n(pretrained)", "sarima": "SARIMA",
        "rnn": "Authors' RNN\n(clinical inputs)"}
GCOL = {"hgbr": ORANGE, "chronos": PURPLE, "sarima": PINK, "rnn": GREY}


def gap_chart(pv, name, ylabel, unit_pad, title, word="less"):
    fig, ax = plt.subplots(figsize=(W, 3.55))
    gaps = {m: (pv[m] - pv["dow4"]) for m in MS}
    lo = min(g.min() for g in gaps.values()); hi = max(g.max() for g in gaps.values())
    span = hi - lo + unit_pad
    for i, m in enumerate(MS):
        g = gaps[m]
        ax.bar(i, g.mean(), 0.7, color=GCOL[m], alpha=0.55)
        year_points(ax, i, g)
        ax.text(i, lo - 0.10 * span, f"{word} in\n{int((g < 0).sum())} of 7 years", ha="center", va="top", fontsize=11.5)
    ax.axhline(0, color=GREEN, lw=2)
    ax.set_xticks(range(len(MS)), [GLAB[m] for m in MS])
    ax.set_ylabel(ylabel)
    ax.set_ylim(lo - 0.36 * span, max(hi, 0) + 0.10 * span)
    ax.grid(axis="x", visible=False)
    save(fig, name, title)


inv = pd.read_csv(R / "m9/27_multiyear_inventory.csv")
a8 = pd.read_csv(R / "m5/08_multiyear_inventory.csv").query("model == 'rnn'")
inv = pd.concat([inv, a8[inv.columns.intersection(a8.columns)]], ignore_index=True)
h = inv[inv.target == "hospital"]
w = h.pivot(index="year", columns="model", values="waste_pct_mean")
gap_chart(w, "m9_waste_gap_by_year.png", "Waste gap, percentage points\n(0 = weekday average)", 0.6,
          "On waste, no forecast beat the simple weekday average\nconsistently: each won some years and lost others")
l = h.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
gap_chart(l, "m9_lost_gap_by_year.png", "Lost units per year\n(0 = weekday average)", 60,
          "Counting wasted plus emergency units, the pretrained model\nand SARIMA lost fewer units in most or all years", word="fewer")
pr = pd.read_csv(R / "m8/19_prior_year_cushion.csv")
gap_chart(pr.pivot(index="year", columns="model", values="wasted_plus_emergency_mean"), "m9_prior_year_cushion.png",
          "Lost units per year\n(0 = weekday average)", 60,
          "With the cushion fixed from the year before, only the\npretrained model lost fewer units every year (two near-ties)", word="fewer")

# ---- Figure 5: service level (grouped bars, years lower printed under each bar)
tt = pd.read_csv(R / "m9/29_target_tests.csv")
tt = tt[tt.outcome == "Waste (points)"]
order = [("fixed20", "20 short days a year\n(stricter)"), ("hospital", "Hospital's own\n(21–42 a year)"),
         ("fixed50", "50 short days a year\n(looser)")]
fig, ax = plt.subplots(figsize=(W, 3.35))
mods = (("hgbr", ORANGE, "Gradient boosting"), ("chronos", PURPLE, "Chronos-Bolt"), ("sarima", PINK, "SARIMA"))
bw = 0.26
for j, (m, c, lab) in enumerate(mods):
    g = tt[tt.model == m].set_index("target")
    for i, (t, _) in enumerate(order):
        v = g.loc[t, "mean_diff"]; n = int(g.loc[t, "years_better"])
        xi = i + (j - 1) * bw
        ax.bar(xi, v, bw * 0.92, color=c, label=lab if i == 0 else None)
        ax.text(xi, v - 0.04, f"{n}/7", ha="center", va="top", fontsize=10.5)
ax.axhline(0, color=GREEN, lw=2)
ax.set_xticks(range(3), [b2 for _, b2 in order])
ax.set_ylim(-1.32, 0.05)
ax.set_ylabel("Waste gap, percentage points\n(0 = weekday average)")
ax.legend(frameon=False, loc="lower right", fontsize=11)
ax.grid(axis="x", visible=False)
save(fig, "m9_service_level.png",
     "When shortages had to be rarer, the model forecasts wasted\nless than the weekday average in 6 or 7 of 7 years")

# ---- Delivery calendar (main Figure 3 in v7): years on the x-axis, legend below so labels stay large
wd = pd.read_csv(R / "m9/26_weekend_delivery.csv")
wd = wd[wd.target == "hospital"]
CALS = [("base", "Tue–Sat (documented)", "#555555", "o", 8, 2.0),
        ("weekdays", "Mon–Fri", ORANGE, "s", 7, 1.3),
        ("mon_sat", "Mon–Sat", PURPLE, "D", 7, 1.3),
        ("tue_sun", "Tue–Sun", PINK, "^", 7.5, 1.3),
        ("daily", "Every day", "#1f77b4", "v", 7.5, 1.3)]
fig, ax = plt.subplots(figsize=(W, 2.55))
years = None
for c, lab, color, mk, ms, lw in CALS:
    pv = wd[wd.calendar == c].pivot(index="year", columns="model", values="waste_pct_mean")
    g = (pv["sarima"] - pv["dow4"]).sort_index()
    years = g.index.astype(int).to_numpy()
    n = int((g < 0).sum())
    ax.plot(years, g.values, color=color, lw=lw, zorder=3)
    ax.scatter(years, g.values, s=ms**2, marker=mk, color=color, zorder=4,
               edgecolors="white", linewidths=0.5, label=f"{lab}  ({n} of 7 lower)")
ax.axhline(0, color=GREEN, lw=2, zorder=2)
ax.set_xticks(years, [str(y) for y in years])
ax.set_ylabel("SARIMA waste gap, points\n(0 = weekday average)")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.20),
          ncol=3, fontsize=9, handlelength=1.3, columnspacing=0.9, handletextpad=0.4)
ax.grid(axis="x", visible=False)
save(fig, "m9_delivery_calendar.png",
     "SARIMA wasted less than the weekday average in every year\nunder every delivery calendar except the documented one", foot_y=-0.22)
print("v6/v7 charts written to", OUTP, "and", OUTS)
