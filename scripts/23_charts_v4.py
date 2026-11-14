#!/usr/bin/env python3
"""Charts for draft v4 (simple: one idea, large plain labels, takeaway in the title).

  charts/m8_lost_gap_by_year.png   (replaces Figure 2: yearly gaps, not run-to-run bars)
  charts/m8_prior_year_cushion.png (new: cushion size fixed from the year before)
  charts/m8_cost_weight.png        (Figure S5.2 with a corrected title)
  charts/m8_reality_check.png      (Figure 4 with the asymmetric miss stated correctly)

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: .venv/bin/python scripts/23_charts_v4.py
"""
from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
CH = ROOT / "charts"
MS = ["hgbr", "chronos", "sarima", "rnn"]
LAB = {"hgbr": "Machine learning\n(gradient boosting)", "chronos": "Free pretrained\nmodel (Chronos-Bolt)",
       "sarima": "Standard statistics\nmodel (SARIMA)", "rnn": "Source authors'\nnetwork (clinical inputs)"}
COL = {"hgbr": "#d95f02", "chronos": "#7570b3", "sarima": "#e7298a", "rnn": "#666666"}


def foot(fig, text):
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(text, 125)), ha="center", va="bottom", fontsize=11, color="#444444")


def gap_chart(lost: pd.DataFrame, title: str, path: Path, note: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 7.4))
    rng = np.random.default_rng(1)
    for i, m in enumerate(MS):
        g = (lost[m] - lost["dow4"]).values
        ax.bar(i, g.mean(), 0.6, color=COL[m], alpha=0.85)
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(g)), g, s=70, color="black", zorder=3)
        n = int((g < 0).sum())
        ax.text(i, min(g.min(), g.mean()) - 14, f"fewer in\n{n} of 7 years", ha="center", va="top", fontsize=14)
    ax.axhline(0, color="#1b9e77", lw=2.5)
    ax.text(3.45, 3, "weekday average", ha="right", va="bottom", fontsize=13, color="#1b9e77")
    ax.set_xticks(range(len(MS)), [LAB[m] for m in MS], fontsize=14)
    ax.set_ylabel("Thrown-away + emergency units per year\ncompared with the weekday average", fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    lo = min((lost[m] - lost["dow4"]).min() for m in MS)
    hi = max((lost[m] - lost["dow4"]).max() for m in MS)
    ax.set_ylim(lo - 70, max(hi, 0) + 25)
    ax.set_title(title, fontsize=16, pad=12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    foot(fig, note)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


inv = pd.concat([pd.read_csv(R / "m5/08_multiyear_inventory.csv"),
                 pd.read_csv(R / "m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
h = inv[inv.target == "hospital"]
lost = h.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
gap_chart(lost, "Below zero = fewer units lost than the weekday average. Most years were below zero,\n"
          "but gradient boosting was not consistent",
          CH / "m8_lost_gap_by_year.png",
          "Aachen public data, 2012-2018. Each forecast is set to the hospital's own number of short days in each "
          "year. Bar = 7-year average gap; dots = the 7 single years (each the mean of 30 simulated runs). "
          "A learning exercise on public data, not a real-world result.")

pr = pd.read_csv(R / "m8/19_prior_year_cushion.csv")
lost2 = pr.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
gap_chart(lost2, "With the safety cushion fixed from the year before, only the pretrained model\n"
          "lost fewer units than the weekday average in every year",
          CH / "m8_prior_year_cushion.png",
          "Aachen public data, 2012-2018. Each forecast's cushion size was chosen to hit the previous year's "
          "recorded short days, then kept unchanged for the test year, so short days now differ between forecasts. "
          "Bar = 7-year average gap; dots = single years. A learning exercise, not a real-world result.")

cs = pd.read_csv(R / "m6/14_cost_summary.csv")
g = cs[cs.view == "matched"]
fig, ax = plt.subplots(figsize=(12, 7.2))
for k in ["hgbr", "chronos", "sarima"]:
    s = g[g.model == k].sort_values("w")
    ax.plot(s.w, -s.gap_vs_dow4_per_year, marker="o", lw=3, ms=8, color=COL[k], label=LAB[k].replace("\n", " "))
ax.axhline(0, color="#1b9e77", lw=2, ls="--")
ax.text(10, 6, "weekday average", ha="right", va="bottom", fontsize=13, color="#1b9e77")
ax.set_xlabel("How many wasted units one emergency unit is worth (cost weight)", fontsize=15)
ax.set_ylabel("Weighted units saved per year\ncompared with the weekday average (average of 7 years)", fontsize=15)
ax.tick_params(labelsize=13)
ax.legend(fontsize=13, frameon=False, loc="upper left")
ax.set_title("On average the saving grows with the cost weight,\n"
             "but at high weights it held in only 4 of 7 years", fontsize=16, pad=12)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", alpha=0.3)
foot(fig, "Aachen public data, 2012-2018, at the hospital's own short days; average of 7 years and 30 simulated runs. "
     "Weighted units = wasted units + weight x emergency units. Real prices are not in the data. A learning exercise only.")
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(CH / "m8_cost_weight.png", dpi=150)
plt.close(fig)


# Reality check (Figure 4): same chart as script 09, corrected title (misses were asymmetric).
b = pd.read_csv(R / "m5/09_reality_check.csv")
b = b[b["life_scenario"].str.startswith("base")]
s = b[b["policy"] == "standing"].sort_values("year")
x = np.arange(len(s))
fig, ax = plt.subplots(figsize=(13, 7.2))
ax.bar(x - 0.2, s["hosp_waste_pct"], 0.38, color="#222222", label="What the hospital recorded")
ax.bar(x + 0.2, s["sim_waste_pct"], 0.38, color="#80b1d3", label="Simulation of a hospital-like standing order")
ax.errorbar(x + 0.2, s["sim_waste_pct"], yerr=[s["sim_waste_pct"] - s["sim_waste_p05"],
            s["sim_waste_p95"] - s["sim_waste_pct"]], fmt="none", ecolor="black", capsize=3)
gap = s["sim_waste_pct"] - s["hosp_waste_pct"]
ax.set_title(f"On average the simulation came close to the hospital ({s.sim_waste_pct.mean():.1f}% vs "
             f"{s.hosp_waste_pct.mean():.1f}% wasted),\nbut single years missed by up to {gap.max():.1f} points "
             f"too high and {-gap.min():.1f} points too low", fontsize=17, pad=12)
ax.set_xticks(x, [str(int(v)) for v in s["year"]], fontsize=15)
ax.tick_params(axis="y", labelsize=14)
ax.set_ylabel("Platelets thrown away\n(% of units used)", fontsize=16)
ax.set_ylim(0, max(s["hosp_waste_pct"].max(), s["sim_waste_p95"].max()) * 1.3)
ax.legend(fontsize=14, frameon=False, loc="upper center", ncol=2)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", alpha=0.3)
foot(fig, "Aachen hospital public data, 8 Jan to 18 Dec of each year. The simulated order is set so it has the "
     "hospital's own number of short days. Black lines = 5th to 95th percentile of 30 simulated runs (simulation "
     "noise only). The simulation leaves out special-order units, transfers, quality-control losses and real ordering choices.")
fig.tight_layout(rect=(0, 0.09, 1, 1))
fig.savefig(CH / "m8_reality_check.png", dpi=150)
plt.close(fig)
print("v4 charts written")
