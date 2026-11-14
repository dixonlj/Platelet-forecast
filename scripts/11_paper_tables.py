#!/usr/bin/env python3
"""Write markdown tables for the v2 supplement straight from result files (no retyping)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R5, OUT = ROOT / "results/m5", ROOT / "paper/tables"
OUT.mkdir(parents=True, exist_ok=True)
NAMES = {"naive": "Use yesterday", "last7": "Last-7-day average", "same_dow": "Same weekday last week",
         "dow4": "4-week weekday average", "hgbr": "Gradient boosting", "chronos": "Chronos-Bolt",
         "lasso": "Authors' LASSO (ref.)", "rnn": "Authors' RNN (ref.)"}
ORDER = list(NAMES)


def md(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" if i == 0 else "---:" for i in range(len(cols))) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(lines) + "\n"


# S-yearly hospital profile (full calendar years)
y = pd.read_csv(ROOT / "results/aachen/yearly_profile.csv")
t = pd.DataFrame({"Year": y.year, "Units transfused": y.transfused.map("{:,}".format),
                  "Mean per day": y.mean_per_day.map("{:.2f}".format), "Waste units": y.waste,
                  "Waste %": y.waste_pct.map("{:.2f}".format), "Emergency units": y.purchase,
                  "Emergency %": y.shortage_pct.map("{:.2f}".format), "Days with a purchase": y.purchase_days,
                  "Zero-use days": y.zero_days})
(OUT / "yearly.md").write_text(md(t))

# Accuracy by year
a = pd.read_csv(R5 / "08_accuracy_by_year.csv")
m = a[~a.model.str.startswith("DM_")].pivot(index="model", columns="year", values="mae_1d")
m = m.loc[[k for k in ORDER if k in m.index]].round(2)
m.index = [NAMES[k] for k in m.index]
m = m.reset_index().rename(columns={"index": "Model (1-day MAE, units)"})
m.columns = [str(c) for c in m.columns]
(OUT / "accuracy.md").write_text(md(m))
dm = a[a.model.str.startswith("DM_")].copy()
dm["Comparison"] = dm.model.map({"DM_hgbr_vs_dow4": "Gradient boosting vs 4-week average",
                                  "DM_chronos_vs_dow4": "Chronos-Bolt vs 4-week average"})
dm = pd.DataFrame({"Year": dm.year, "Comparison": dm.Comparison, "MAE difference (units)": dm.mae_1d.round(2),
                   "DM statistic": dm.dm_stat.round(2), "p-value": dm.dm_p.map(lambda p: f"{p:.3f}")})
(OUT / "dm.md").write_text(md(dm.sort_values(["Comparison", "Year"])))

# Full multi-year inventory, hospital target
d = pd.read_csv(R5 / "08_multiyear_inventory.csv")
for metric, fmt, fname in (("waste_pct_mean", "{:.2f}", "inv_waste.md"),
                           ("emergency_units_mean", "{:.1f}", "inv_emerg.md"),
                           ("wasted_plus_emergency_mean", "{:.1f}", "inv_lost.md")):
    h = d[d.target == "hospital"].pivot(index="model", columns="year", values=metric)
    h = h.loc[ORDER].map(lambda v: fmt.format(v))
    h.index = [NAMES[k] for k in h.index]
    h = h.reset_index().rename(columns={"index": "Model"})
    h.columns = [str(c) for c in h.columns]
    (OUT / fname).write_text(md(h))
# paired GB / Chronos vs dow4 per year
rows = []
for _, r in d[(d.target == "hospital") & d.model.isin(["hgbr", "chronos"])].iterrows():
    rows.append({"Year": r.year, "Model": NAMES[r.model], "Short days": int(r.target_short_days),
                 "Waste gap vs 4-week avg (points)": f"{r.waste_gap_vs_dow4:+.2f}",
                 "5th–95th pct waste": f"{r.waste_pct_p05:.2f}–{r.waste_pct_p95:.2f}",
                 "Runs with less waste": f"{int(r.seeds_less_waste_than_dow4)}/30",
                 "Lost-unit gap": f"{r.lost_gap_vs_dow4:+.1f}",
                 "Runs with fewer lost units": f"{int(r.seeds_fewer_lost_than_dow4)}/30"})
(OUT / "paired.md").write_text(md(pd.DataFrame(rows).sort_values(["Model", "Year"])))
# robustness at 20 / 50
rows = []
for tg, g in d[d.model.isin(["dow4", "hgbr", "chronos"])].groupby("target"):
    p = g.pivot(index="year", columns="model", values="waste_pct_mean")
    for Y, r in p.iterrows():
        rows.append({"Target": {"hospital": "Hospital's own", "fixed20": "20", "fixed50": "50"}[tg], "Year": Y,
                     "Waste % WA": f"{r.dow4:.2f}", "Waste % GB": f"{r.hgbr:.2f}", "Waste % CB": f"{r.chronos:.2f}"})
(OUT / "robust.md").write_text(md(pd.DataFrame(rows)))
w = pd.read_csv(R5 / "08_wins_count.csv")
w = w[w.scope.isin(["dow4_vs_hgbr", "dow4_vs_chronos", "hgbr_vs_chronos", "all_models"])].copy()
w["winner"] = w.winner.map(NAMES)
w = w.rename(columns={"target": "Short-day target", "metric": "Outcome", "scope": "Comparison",
                      "winner": "Winner", "years_won": "Years won (of 7)"})
w["Outcome"] = w["Outcome"].map({"waste_pct_mean": "Waste %", "wasted_plus_emergency_mean": "Wasted + emergency"})
(OUT / "wins.md").write_text(md(w))

# Reality check
rc = pd.read_csv(R5 / "09_reality_check.csv")
b = rc[rc.life_scenario.str.startswith("base")].copy()
b["Policy"] = b.policy.map({"standing": "Standing weekday order", "dow4": "4-week weekday average"})
t = pd.DataFrame({"Year": b.year, "Policy": b.Policy, "Short days": b.target_short_days,
                  "Sim waste %": b.sim_waste_pct.round(2), "Recorded waste %": b.hosp_waste_pct.round(2),
                  "Gap (points)": b.gap_waste_pct_points.round(2), "Sim emergency units": b.sim_emergency_units.round(1),
                  "Recorded emergency units": b.hosp_emergency_units,
                  "Sim Monday share of short days": b.sim_monday_share.round(2)})
(OUT / "reality.md").write_text(md(t.sort_values(["Policy", "Year"])))
lf = pd.read_csv(R5 / "09_life_on_arrival_calibration.csv").round(2)
lf.columns = ["Life on arrival", "Mean sim waste % (2012–2018)", "Mean recorded waste %", "Mean gap (points)"]
(OUT / "life.md").write_text(md(lf))
hb = pd.read_csv(R5 / "08_hospital_by_year.csv")
(OUT / "hosp_monday.md").write_text(md(pd.DataFrame({"Year": hb.year, "Recorded Monday share of purchase days": hb.monday_share_of_purchase_days.round(2)})))

# US one change
u = pd.read_csv(R5 / "10_us_one_change.csv")
t = pd.DataFrame({"Scenario": u.scenario, "Model": u.model.map(NAMES), "Waste %": u.waste_pct_mean.round(2),
                  "5th–95th pct": u.waste_p05.round(2).astype(str) + "–" + u.waste_p95.round(2).astype(str),
                  "Emergency units": u.emergency_units_mean.round(1), "Wasted + emergency": u.wasted_plus_emergency_mean.round(1)})
(OUT / "us_one.md").write_text(md(t))
u7 = pd.read_csv(ROOT / "results/m4/07_inventory.csv")
t = pd.DataFrame({"Scenario": u7.scenario, "Model": u7.model.map(NAMES), "Waste %": u7.waste_mean.round(2),
                  "5th–95th pct": u7.waste_p05.round(2).astype(str) + "–" + u7.waste_p95.round(2).astype(str)})
(OUT / "us07.md").write_text(md(t))

# 2018 sensitivity
s = pd.read_csv(ROOT / "results/realistic/sensitivity.csv")
(OUT / "sens_raw_cols.txt").write_text(",".join(s.columns))
print("tables written:", sorted(p.name for p in OUT.glob("*.md")))

# 2018 sensitivity table (one change at a time, 31 short days)
p = s.pivot(index="scenario", columns="model", values="waste_at31_mean")
c = s[s.model == "hgbr"].set_index("scenario")["change_vs_base_pp"]
order = list(dict.fromkeys(s.scenario))
t = pd.DataFrame({"Change from base": order, "4-week weekday average": [p.loc[o, "dow4"] for o in order],
                  "Gradient boosting": [p.loc[o, "hgbr"] for o in order],
                  "Change for GB (points)": [f"{c.loc[o]:+.2f}" for o in order]})
(OUT / "sens.md").write_text(md(t))
print("sens written")
