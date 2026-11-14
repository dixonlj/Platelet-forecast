#!/usr/bin/env python3
"""Tables (paper/tables/*_v3.md) and simple charts for draft v3, straight from results/m6 (no retyping).

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: .venv/bin/python scripts/17_tables_charts_v3.py
"""
from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
R5, R6, OUT, CH = ROOT / "results/m5", ROOT / "results/m6", ROOT / "paper/tables", ROOT / "charts"
NAMES = {"dow4": "4-week weekday average", "hgbr": "Gradient boosting", "chronos": "Chronos-Bolt",
         "sarima": "SARIMA", "lasso": "Authors' LASSO (ref.)", "rnn": "Authors' RNN (ref.)"}
SHORT = {"dow4": "WA", "hgbr": "GB", "chronos": "CB", "sarima": "SA"}


def md(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "|" + "|".join("---" if i == 0 else "---:" for i in range(len(cols))) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(lines) + "\n"


def foot(fig, text):
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(text, 120)), ha="center", va="bottom", fontsize=11, color="#444444")


def style(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.3)


inv = pd.read_csv(R6 / "13_multiyear_inventory.csv")
h = inv[inv.target == "hospital"]
W = h.pivot(index="year", columns="model", values="waste_pct_mean")
Lo = h.pivot(index="year", columns="model", values="wasted_plus_emergency_mean")
E = h.pivot(index="year", columns="model", values="emergency_units_mean")
sd = h.drop_duplicates("year").set_index("year")["target_short_days"]
ms = ["dow4", "hgbr", "chronos", "sarima"]

# ---- Body Table 2 (v3): waste and wasted+emergency, four forecasts
t = pd.DataFrame({"Year": W.index, "Short days": sd.values.astype(int)})
for m in ms:
    t[f"Waste % {SHORT[m]}"] = W[m].map("{:.2f}".format).values
for m in ms:
    t[f"Lost {SHORT[m]}"] = Lo[m].round(0).astype(int).values
mean = {"Year": "Mean", "Short days": int(round(sd.mean()))}
for m in ms:
    mean[f"Waste % {SHORT[m]}"] = f"{W[m].mean():.2f}"
for m in ms:
    mean[f"Lost {SHORT[m]}"] = int(round(Lo[m].mean()))
t = pd.concat([t, pd.DataFrame([mean])], ignore_index=True)
(OUT / "table2_v3.md").write_text(md(t))

# ---- Supplement: SARIMA accuracy and DM tests
a = pd.read_csv(R6 / "13_accuracy_by_year.csv")
m = a[~a.model.str.startswith("DM_")].pivot(index="model", columns="year", values="mae_1d").loc[ms]
m["Mean"] = m.mean(axis=1)
m = m.round(2)
m.index = [NAMES[k] for k in m.index]
m = m.reset_index().rename(columns={"index": "Model (1-day MAE, units)"})
m.columns = [str(c) for c in m.columns]
(OUT / "sarima_acc_v3.md").write_text(md(m))
dm = a[a.model.str.startswith("DM_")].copy()
dm["Comparison"] = dm.model.map({"DM_sarima_vs_dow4": "SARIMA vs 4-week average",
                                 "DM_sarima_vs_hgbr": "SARIMA vs gradient boosting",
                                 "DM_sarima_vs_chronos": "SARIMA vs Chronos-Bolt"})
dm = pd.DataFrame({"Comparison": dm.Comparison, "Year": dm.year, "MAE difference (units)": dm.mae_1d.round(2),
                   "DM statistic": dm.dm_stat.round(2), "p-value": dm.dm_p.map(lambda p: f"{p:.3f}")})
(OUT / "sarima_dm_v3.md").write_text(md(dm.sort_values(["Comparison", "Year"])))
sel = pd.read_csv(R6 / "12_sarima_selected.csv")
(OUT / "sarima_sel_v3.md").write_text(md(pd.DataFrame({
    "Training data up to": sel.cutoff, "Used for test year": pd.to_datetime(sel.cutoff).dt.year + 1,
    "Chosen model": "SARIMA" + sel.order + "x" + sel.seasonal.str.replace(", 7)", ")7").str.replace("(", "(", regex=False),
    "AIC": sel.aic.round(1)})))
# SARIMA inventory incl. emergency units, robustness
rows = []
for tg, g in inv.groupby("target", sort=False):
    p = g.pivot(index="year", columns="model", values="waste_pct_mean")
    for Y, r in p.iterrows():
        rows.append({"Target": {"hospital": "Hospital's own", "fixed20": "20", "fixed50": "50"}[tg], "Year": Y,
                     **{f"Waste % {SHORT[k]}": f"{r[k]:.2f}" for k in ms}})
(OUT / "sarima_robust_v3.md").write_text(md(pd.DataFrame(rows)))
pr = h[h.model == "sarima"]
(OUT / "sarima_paired_v3.md").write_text(md(pd.DataFrame({
    "Year": pr.year, "Emergency units SA": pr.emergency_units_mean.round(1),
    "Emergency units WA": E.loc[pr.year, "dow4"].round(1).values,
    "Waste gap vs WA (points)": pr.waste_gap_vs_dow4.map("{:+.2f}".format),
    "Runs with less waste": pr.seeds_less_waste_than_dow4.astype(int).astype(str) + "/30",
    "Lost-unit gap vs WA": pr.lost_gap_vs_dow4.map("{:+.1f}".format),
    "Runs with fewer lost units": pr.seeds_fewer_lost_than_dow4.astype(int).astype(str) + "/30"})))

# ---- Supplement: cost weights
cs = pd.read_csv(R6 / "14_cost_summary.csv")
rows = []
for view in ("matched", "best_cushion"):
    g = cs[cs.view == view]
    for w, gw in g.groupby("w"):
        if view == "best_cushion" and w == 0:
            continue  # with w = 0 the cheapest cushion is simply the smallest one; not meaningful
        r = {"View": {"matched": "At hospital's short days", "best_cushion": "Best cushion for each weight"}[view],
             "Weight w": f"{w:g}"}
        for k in ["hgbr", "chronos", "sarima", "lasso", "rnn"]:
            x = gw[gw.model == k].iloc[0]
            r[NAMES[k]] = f"{x.gap_vs_dow4_per_year:+.0f} ({int(x.years_better_than_dow4)}/7)"
        rows.append(r)
(OUT / "cost_v3.md").write_text(md(pd.DataFrame(rows)))

# ---- Supplement: life on arrival
la = pd.read_csv(R6 / "15_reality_life_sweep.csv")
am = la.groupby("share_3day")[["sim_waste_pct", "hosp_waste_pct", "sim_emergency_units"]].mean().reset_index()
(OUT / "life_sweep_v3.md").write_text(md(pd.DataFrame({
    "Share arriving with 3 days (rest 4)": (am.share_3day * 100).round(0).astype(int).astype(str) + "%",
    "Mean sim waste % (standing order)": am.sim_waste_pct.round(2),
    "Mean recorded waste %": am.hosp_waste_pct.round(2),
    "Mean sim emergency units": am.sim_emergency_units.round(1)})))
py = pd.read_csv(R6 / "15_matching_share_by_year.csv")
(OUT / "life_year_v3.md").write_text(md(pd.DataFrame({
    "Year": py.year, "Recorded waste %": py.hosp_waste_pct.round(2), "Sim waste % if all 4 days": py.sim_waste_0pct.round(2),
    "Sim waste % if all 3 days": py.sim_waste_100pct.round(2), "Share of 3-day units that matches": py.matching_share_3day})))
lb = pd.read_csv(R6 / "15_models_life_sweep.csv")
rows = []
for s3, g in lb.groupby("share_3day"):
    w_ = g.pivot(index="year", columns="model", values="waste_pct")
    l_ = g.pivot(index="year", columns="model", values="lost_units")
    rows.append({"Share arriving with 3 days": f"{s3:.0%}",
                 **{f"Mean waste % {SHORT[k]}": f"{w_[k].mean():.2f}" for k in ms},
                 **{f"Years less waste than WA: {SHORT[k]}": f"{int((w_[k] < w_.dow4).sum())}/7" for k in ms[1:]},
                 **{f"Years fewer lost than WA: {SHORT[k]}": f"{int((l_[k] < l_.dow4).sum())}/7" for k in ms[1:]}})
(OUT / "life_models_v3.md").write_text(md(pd.DataFrame(rows)))

# ---- Supplement: low-titer bound
lt = pd.read_csv(R6 / "16_low_titer_bound.csv")
(OUT / "low_titer_v3.md").write_text(md(pd.DataFrame({
    "Calendar": lt.calendar, "Group O to non-O patients": lt.o_to_non_o, "Model": lt.model.map(NAMES),
    "Waste %": lt.waste_pct_mean.round(2),
    "5th–95th pct": lt.waste_p05.round(2).astype(str) + "–" + lt.waste_p95.round(2).astype(str),
    "Emergency units": lt.emergency_units_mean.round(1), "Wasted + emergency": lt.wasted_plus_emergency_mean.round(1),
    "O units given to non-O patients": lt.o_units_to_non_o_mean.round(1)})))

# ================= Charts =================
# Chart 1 (body): 7-year mean lost units per forecast
ps = pd.read_csv(R6 / "13_per_seed.csv")
per = ps.groupby(["model", "seed"])["lost_units"].mean().unstack(0)
labels = {"dow4": "Average of last\n4 same weekdays", "hgbr": "Machine learning\n(gradient boosting)",
          "chronos": "Free pretrained\nmodel (Chronos-Bolt)", "sarima": "Standard statistics\nmodel (SARIMA)"}
colors = {"dow4": "#1b9e77", "hgbr": "#d95f02", "chronos": "#7570b3", "sarima": "#e7298a"}
fig, ax = plt.subplots(figsize=(12, 7.4))
vals = [per[k].mean() for k in ms]
lo = [per[k].mean() - np.percentile(per[k], 5) for k in ms]
hi = [np.percentile(per[k], 95) - per[k].mean() for k in ms]
ax.bar(range(4), vals, 0.62, color=[colors[k] for k in ms])
ax.errorbar(range(4), vals, yerr=[lo, hi], fmt="none", ecolor="black", capsize=8, lw=1.5)
for i, v in enumerate(vals):
    ax.text(i, v + max(hi) + 8, f"{v:.0f}", ha="center", fontsize=16, fontweight="bold")
ax.set_xticks(range(4), [labels[k] for k in ms], fontsize=14)
ax.set_ylabel("Units thrown away + emergency units\n(average per year, 2012–2018)", fontsize=15)
ax.tick_params(axis="y", labelsize=13)
ax.set_ylim(0, max(vals) * 1.25)
gaps = [vals[0] - v for v in vals[1:]]
ax.set_title(f"All three newer forecasts lost {min(gaps):.0f}–{max(gaps):.0f} fewer units a year than the weekday average;\n"
             "the standard statistics model did as well as the pretrained model", fontsize=16, pad=12)
style(ax)
foot(fig, "Aachen hospital public data, 2012–2018. Each forecast is set so it has the hospital's own number of short days "
     "each year. Bars = 7-year average of 30 simulated runs; black lines = 5th to 95th percentile of runs. "
     "A learning exercise on public data, not a real-world result.")
fig.tight_layout(rect=(0, 0.09, 1, 1))
fig.savefig(CH / "m6_lost_units_four_forecasts.png", dpi=150)
plt.close(fig)

# Chart 2 (supplement): cost weight
g = cs[cs.view == "matched"]
fig, ax = plt.subplots(figsize=(12, 7.2))
for k in ["hgbr", "chronos", "sarima"]:
    s = g[g.model == k].sort_values("w")
    ax.plot(s.w, -s.gap_vs_dow4_per_year, marker="o", lw=3, ms=8, color=colors[k], label=labels[k].replace("\n", " "))
ax.axhline(0, color="#1b9e77", lw=2, ls="--")
ax.text(10, 6, "weekday average", ha="right", va="bottom", fontsize=13, color="#1b9e77")
ax.set_xlabel("How many wasted units one emergency unit is worth (cost weight)", fontsize=15)
ax.set_ylabel("Weighted units saved per year\ncompared with the weekday average", fontsize=15)
ax.tick_params(labelsize=13)
ax.legend(fontsize=13, frameon=False, loc="upper left")
ax.set_title("The more an emergency unit costs, the more the newer forecasts save\ncompared with the weekday average",
             fontsize=16, pad=12)
style(ax)
foot(fig, "Aachen public data, 2012–2018, at the hospital's own short days; average of 7 years and 30 simulated runs. "
     "Weighted units = wasted units + weight x emergency units. Real prices are not in the data. A learning exercise only.")
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(CH / "m6_cost_weight.png", dpi=150)
plt.close(fig)

# Chart 3 (supplement): life on arrival
fig, ax = plt.subplots(figsize=(12, 7.2))
ax.plot(am.share_3day * 100, am.sim_waste_pct, marker="o", lw=3, ms=8, color="#80b1d3", label="Simulated standing order")
ax.axhline(am.hosp_waste_pct.iloc[0], color="#222222", lw=2.5, ls="--", label="What the hospital recorded (average)")
x0 = float(np.interp(am.hosp_waste_pct.iloc[0], am.sim_waste_pct, am.share_3day * 100))
ax.axvline(x0, color="#999999", lw=1.5, ls=":")
ax.text(x0 + 1, 15, f"about {x0:.0f}%", fontsize=14, color="#444444")
ax.set_xlabel("Share of units arriving with only 3 usable days (the rest have 4)", fontsize=15)
ax.set_ylabel("Platelets thrown away\n(% of units used, 2012–2018 average)", fontsize=15)
ax.tick_params(labelsize=13)
ax.legend(fontsize=13, frameon=False, loc="upper left")
ax.set_title(f"Simulated waste matched the hospital's average when about {round(x0 / 10):.0f} in 10 units\n"
             "arrived with only 3 days left", fontsize=16, pad=12)
style(ax)
foot(fig, "Aachen public data; hospital-like standing weekday order matched to each year's recorded short days; "
     "average of 7 years and 30 simulated runs. The real age of units on arrival is not in the data. A learning exercise only.")
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(CH / "m6_life_on_arrival.png", dpi=150)
plt.close(fig)
print("v3 tables and charts written; matching share", round(x0, 1))
