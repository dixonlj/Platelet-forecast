#!/usr/bin/env python3
"""Paper-size redraws of every figure in draft v5 and its supplement (layout build).

Same data and the same results files as the original chart scripts; nothing is re-simulated.
Drawn at the final printed size (6.0 inches wide), so the font sizes below are the real
printed sizes (about 11-13 pt). No in-chart titles or footnotes: the paper captions carry
the takeaway and the notes. Output: charts/paper/<same file name as the original>.png,
which build_paper.py --layout uses in place of the original chart.

  Figure 1   m5_multiyear_waste.png        <- results/m5/08_per_seed.csv
  Figure 2   m8_lost_gap_by_year.png       <- results/m5/08_multiyear_inventory.csv + m6/13_multiyear_inventory.csv
  Figure 3   m8_prior_year_cushion.png     <- results/m8/19_prior_year_cushion.csv
  Figure 4   m8_reality_check.png          <- results/m5/09_reality_check.csv
  Figure S4  realistic_tradeoff_uncertainty.png <- results/realistic/k_sweep_base_mean_sd.csv, per_seed_waste_at31.csv
  Figure S5.1 m5_multiyear_lost_units.png  <- results/m5/08_per_seed.csv
  Figure S5.2 m8_cost_weight.png           <- results/m6/14_cost_summary.csv
  Figure S6  m6_life_on_arrival.png        <- results/m6/15_reality_life_sweep.csv
  Figure S7  m5_us_one_change.png          <- results/m5/10_us_one_change.csv

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
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
OUT = ROOT / "charts" / "paper"
OUT.mkdir(parents=True, exist_ok=True)

fams = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({
    "font.family": "Carlito" if "Carlito" in fams else "DejaVu Sans",
    "font.size": 12, "axes.labelsize": 12.5, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "legend.fontsize": 12, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True, "savefig.dpi": 300,
})
W = 6.0
GREEN, ORANGE, PURPLE, PINK, GREY = "#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#666666"


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def grouped(per_seed, metric, models, labels, colors, ylabel, name, h=3.9):
    years = sorted(per_seed["year"].unique())
    fig, ax = plt.subplots(figsize=(W, h))
    w = 0.8 / len(models)
    top = 0
    for i, m in enumerate(models):
        g = per_seed[per_seed["model"] == m].groupby("year")[metric]
        mean, lo, hi = g.mean().reindex(years), g.quantile(0.05).reindex(years), g.quantile(0.95).reindex(years)
        x = np.arange(len(years)) + (i - (len(models) - 1) / 2) * w
        ax.bar(x, mean, w * 0.95, color=colors[m], label=labels[m])
        ax.errorbar(x, mean, yerr=[mean - lo, hi - mean], fmt="none", ecolor="black", capsize=2, lw=1)
        top = max(top, hi.max())
    ax.set_xticks(range(len(years)), [str(y) for y in years])
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, top * 1.25)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper center", ncol=len(models), bbox_to_anchor=(0.5, 1.13),
              handlelength=1.2, columnspacing=1.2)
    save(fig, name)


ps = pd.read_csv(R / "m5/08_per_seed.csv")
lab = {"dow4": "Weekday average", "hgbr": "Gradient boosting", "chronos": "Chronos-Bolt"}
col = {"dow4": GREEN, "hgbr": ORANGE, "chronos": PURPLE}
grouped(ps, "waste_pct", ["dow4", "hgbr"], lab, col, "Platelets thrown away\n(% of units used)", "m5_multiyear_waste.png")
grouped(ps, "lost_units", ["dow4", "hgbr", "chronos"], lab, col, "Thrown-away + emergency\nunits per year",
        "m5_multiyear_lost_units.png")

# ---- Figures 2 and 3: yearly gaps against the weekday average
MS = ["hgbr", "chronos", "sarima", "rnn"]
GLAB = {"hgbr": "Gradient\nboosting", "chronos": "Chronos-Bolt\n(pretrained)", "sarima": "SARIMA",
        "rnn": "Authors' RNN\n(clinical inputs)"}
GCOL = {"hgbr": ORANGE, "chronos": PURPLE, "sarima": PINK, "rnn": GREY}


def gap_chart(lost, name):
    fig, ax = plt.subplots(figsize=(W, 4.1))
    rng = np.random.default_rng(1)
    gaps = {m: (lost[m] - lost["dow4"]).values for m in MS}
    lo = min(g.min() for g in gaps.values()); hi = max(g.max() for g in gaps.values())
    for i, m in enumerate(MS):
        g = gaps[m]
        ax.bar(i, g.mean(), 0.6, color=GCOL[m], alpha=0.85)
        ax.scatter(i + rng.uniform(-0.13, 0.13, len(g)), g, s=26, color="black", zorder=3)
        ax.text(i, min(g.min(), g.mean()) - 0.05 * (hi - lo + 60), f"fewer in\n{int((g < 0).sum())} of 7 years",
                ha="center", va="top", fontsize=11.5)
    ax.axhline(0, color=GREEN, lw=2)
    ax.text(3.45, 2, "weekday average", ha="right", va="bottom", fontsize=11.5, color=GREEN)
    ax.set_xticks(range(len(MS)), [GLAB[m] for m in MS])
    ax.set_ylabel("Lost units per year vs\nthe weekday average")
    ax.set_ylim(lo - 0.30 * (hi - lo + 60), max(hi, 0) + 0.10 * (hi - lo + 60))
    ax.grid(axis="x", visible=False)
    save(fig, name)


inv = pd.concat([pd.read_csv(R / "m5/08_multiyear_inventory.csv"),
                 pd.read_csv(R / "m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
h = inv[inv.target == "hospital"]
gap_chart(h.pivot(index="year", columns="model", values="wasted_plus_emergency_mean"), "m8_lost_gap_by_year.png")
pr = pd.read_csv(R / "m8/19_prior_year_cushion.csv")
gap_chart(pr.pivot(index="year", columns="model", values="wasted_plus_emergency_mean"), "m8_prior_year_cushion.png")

# ---- Figure 4: reality check
b = pd.read_csv(R / "m5/09_reality_check.csv")
s = b[b["life_scenario"].str.startswith("base") & (b["policy"] == "standing")].sort_values("year")
x = np.arange(len(s))
fig, ax = plt.subplots(figsize=(W, 3.15))
ax.bar(x - 0.2, s["hosp_waste_pct"], 0.38, color="#222222", label="Hospital's record")
ax.bar(x + 0.2, s["sim_waste_pct"], 0.38, color="#80b1d3", label="Simulated standing order")
ax.errorbar(x + 0.2, s["sim_waste_pct"], yerr=[s["sim_waste_pct"] - s["sim_waste_p05"],
            s["sim_waste_p95"] - s["sim_waste_pct"]], fmt="none", ecolor="black", capsize=2, lw=1)
ax.set_xticks(x, [str(int(v)) for v in s["year"]])
ax.set_ylabel("Platelets thrown away\n(% of units used)")
ax.set_ylim(0, max(s["hosp_waste_pct"].max(), s["sim_waste_p95"].max()) * 1.22)
ax.grid(axis="x", visible=False)
ax.legend(frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.13), handlelength=1.2)
save(fig, "m8_reality_check.png")

# ---- Figure S4: 2018 trade-off (left) and waste at 31 short days (right)
KEYS = ["naive", "last7", "same_dow", "dow4", "hgbr", "lasso", "rnn"]
SLAB = {"naive": "Yesterday", "last7": "Last 7 days", "same_dow": "Same weekday", "dow4": "Weekday avg.",
        "hgbr": "Grad. boosting", "lasso": "Authors' LASSO", "rnn": "Authors' RNN"}
SCOL = {"naive": "#999999", "last7": "#66a61e", "same_dow": "#e7298a", "dow4": "#1f77b4", "hgbr": ORANGE,
        "lasso": PURPLE, "rnn": "#a6761d"}
ks = pd.read_csv(R / "realistic/k_sweep_base_mean_sd.csv")
seeds = pd.read_csv(R / "realistic/per_seed_waste_at31.csv")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.9), gridspec_kw={"width_ratios": [1.05, 1]})
for k in KEYS:
    g = ks[ks.model == k].sort_values("k")
    thin = k in ("naive", "last7", "same_dow")
    a1.plot(g.waste_pct_mean, g.shortage_days_mean, "--" if k in ("lasso", "rnn") else "-", color=SCOL[k],
            lw=1.2 if thin else 2.2, alpha=0.6 if thin else 1)
a1.plot(12.30, 31, "*", ms=13, color="black", zorder=5)
a1.annotate("Hospital\n2018", (12.30, 31), xytext=(13.5, 58), fontsize=11, arrowprops=dict(arrowstyle="->"))
a1.axhline(31, color="black", lw=0.8, ls=":")
a1.set_xlim(0, 22); a1.set_ylim(0, 110)
a1.set_xlabel("Waste (% of units used)")
a1.set_ylabel("Short days in the year")
data = [seeds[k].dropna().values for k in KEYS]
bp = a2.boxplot(data, orientation="horizontal", patch_artist=True, widths=0.6, showfliers=False,
                tick_labels=[SLAB[k] for k in KEYS], medianprops=dict(color="black"))
for patch, k in zip(bp["boxes"], KEYS):
    patch.set_facecolor(SCOL[k]); patch.set_alpha(0.6)
for i, d in enumerate(data):
    a2.plot(d, np.full(len(d), i + 1) + np.random.default_rng(i).uniform(-0.18, 0.18, len(d)), ".",
            color="black", ms=2.5, alpha=0.5)
a2.axvline(12.30, color="black", ls="--", lw=1)
a2.text(12.6, 7.35, "hospital", fontsize=11, va="center")
a2.invert_yaxis()
a2.set_xlabel("Waste % at 31 short days")
a2.grid(axis="y", visible=False)
for t, k in zip(a2.get_yticklabels(), KEYS):
    t.set_color(SCOL[k] if k not in ("naive",) else "#555555")
fig.tight_layout(w_pad=0.6)
save(fig, "realistic_tradeoff_uncertainty.png")

# ---- Figure S5.2: cost weight
cs = pd.read_csv(R / "m6/14_cost_summary.csv")
g = cs[cs.view == "matched"]
fig, ax = plt.subplots(figsize=(W, 3.9))
end = {}
for k, c, l in (("hgbr", ORANGE, "Gradient boosting"), ("chronos", PURPLE, "Chronos-Bolt"), ("sarima", PINK, "SARIMA")):
    s2 = g[g.model == k].sort_values("w")
    ax.plot(s2.w, -s2.gap_vs_dow4_per_year, marker="o", lw=2.2, ms=5, color=c)
    end[l] = (float(s2.w.iloc[-1]), float(-s2.gap_vs_dow4_per_year.iloc[-1]), c)
ys = sorted(end.items(), key=lambda kv: kv[1][1])
last = -1e9
span = ax.get_ylim()[1] - ax.get_ylim()[0]
for l, (xw, yv, c) in ys:      # label line ends, nudged apart
    yv2 = max(yv, last + 0.07 * span); last = yv2
    ax.text(xw + 0.25, yv2, l, color=c, va="center", fontsize=11.5)
ax.axhline(0, color=GREEN, lw=1.8, ls="--")
ax.text(0.1, 0.02 * span, "weekday average", va="bottom", fontsize=11.5, color=GREEN)
ax.set_xlim(-0.3, 13.2)
ax.set_xticks(range(0, 11, 2))
ax.set_xlabel("Cost weight: wasted units one emergency unit is worth")
ax.set_ylabel("Weighted units saved per year\nvs the weekday average")
save(fig, "m8_cost_weight.png")

# ---- Figure S6: share of units arriving with 3 days
la = pd.read_csv(R / "m6/15_reality_life_sweep.csv")
am = la.groupby("share_3day")[["sim_waste_pct", "hosp_waste_pct"]].mean().reset_index()
fig, ax = plt.subplots(figsize=(W, 3.8))
ax.plot(am.share_3day * 100, am.sim_waste_pct, marker="o", lw=2.2, ms=5, color="#3b8bc2", label="Simulated standing order")
hw = am.hosp_waste_pct.iloc[0]
ax.axhline(hw, color="#222222", lw=1.8, ls="--", label="Hospital's recorded average")
x0 = float(np.interp(hw, am.sim_waste_pct, am.share_3day * 100))
ax.axvline(x0, color="#999999", lw=1.2, ls=":")
ax.text(x0 + 1.5, ax.get_ylim()[0] + 0.08 * (ax.get_ylim()[1] - ax.get_ylim()[0]), f"about {x0:.0f}%", fontsize=12, color="#444444")
ax.set_xlabel("Units arriving with only 3 usable days (%, rest have 4)")
ax.set_ylabel("Platelets thrown away\n(% of units used)")
ax.legend(frameon=False, loc="upper left")
save(fig, "m6_life_on_arrival.png")

# ---- Figure S7: one US change at a time (horizontal bars so the labels stay large)
order = [("German rules (base)", "German rules (start)"),
         ("Only US blood-group shares", "Only US blood-type mix"),
         ("Only US ABO order (plasma-compatible first)", "Only US backup order"),
         ("Only US shelf life (50/50 5-day and 7-day)", "Only longer US shelf life"),
         ("German rules + daily deliveries", "Only daily deliveries"),
         ("All three US changes (German calendar)", "All three US changes"),
         ("All three US changes + daily deliveries", "All three + daily deliveries")]
u = pd.read_csv(R / "m5/10_us_one_change.csv")
u = u[u.model == "hgbr"].set_index("scenario")
v = np.array([u.loc[s3, "waste_pct_mean"] for s3, _ in order])
lo = v - np.array([u.loc[s3, "waste_p05"] for s3, _ in order])
hi = np.array([u.loc[s3, "waste_p95"] for s3, _ in order]) - v
cols = ["#999999", "#bebada", "#bebada", "#fb8072", "#fdb462", "#80b1d3", "#80b1d3"]
fig, ax = plt.subplots(figsize=(W - 0.9, 3.9))   # long y labels add ~0.9 in
y = np.arange(len(order))
ax.barh(y, v, 0.65, color=cols)
ax.errorbar(v, y, xerr=[lo, hi], fmt="none", ecolor="black", capsize=2, lw=1)
for yi, vi, hii in zip(y, v, hi):
    ax.text(vi + hii + 0.2, yi, f"{vi:.1f}%", va="center", fontsize=12)
ax.set_yticks(y, [b2 for _, b2 in order])
ax.invert_yaxis()
ax.set_xlabel("Platelets thrown away (% of units used)")
ax.set_xlim(0, (v + hi).max() * 1.2)
ax.grid(axis="y", visible=False)
save(fig, "m5_us_one_change.png")
print("paper-size charts written to", OUT)
