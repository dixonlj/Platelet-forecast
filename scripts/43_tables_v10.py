#!/usr/bin/env python3
"""Build the v10 paper tables straight from the m10 results files (no hand-typed numbers).
Writes paper/tables/{validation_v10,secondary_v10,stanford_sens_v10,sensitivity_v10,accuracy_v10}.md
Run: python3 scripts/43_tables_v10.py
"""
from pathlib import Path
import json
import pandas as pd

P = Path(__file__).resolve().parent.parent
R = P / "results" / "m10"; S = P / "study2" / "results" / "s2m10"; T = P / "paper" / "tables"
MINUS = "\u2212"

def f(x, d=2, sign=True):
    if x != 0 and round(x, d) == 0:   # e.g. -0.004: show one more decimal so the sign is not lost
        d += 1
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace("-", MINUS)

def ci(lo, hi, d=2):
    return f"{f(lo, d)} to {f(hi, d)}"

def cell(r, d=2):
    return f"{f(r.mu, d)} ({ci(r.ci_lo, r.ci_hi, d)})"

v = json.loads((R / "39_validation_result.json").read_text())
val = ["| Check (preset rule) | Simulated | Recorded | Result |", "|---|---:|---:|---|",
       f"| Overall waste, % of units transfused (within ±1.5 points) | {v['W_sim']:.2f} | {v['W_rec']:.2f} | Fail |",
       f"| Emergency units per short day (6.6 to 11.0) | {v['E_sim']:.2f} | {v['E_rec']:.2f} | Fail |",
       f"| Weekday waste pattern, total variation distance (≤ 0.20) | {v['TVD']:.3f} | — | Fail |",
       f"| Year-by-year agreement (descriptive, no rule) | correlation {v['A4_yearly_corr']:.2f} | mean miss {v['A4_yearly_mae']:.1f} points | — |"]
assert not (v["A1_pass"] or v["A2_pass"] or v["A3_pass"])
(T / "validation_v10.md").write_text("\n".join(val) + "\n")

sec = pd.read_csv(R / "41_secondary_waste.csv"); sen = pd.read_csv(R / "41_sensitivity_vs_so.csv")
tr = pd.read_csv(R / "41_tradeoff_summary.csv")
order = ["gb", "dgb", "sarima", "cb"]
def row_from(df, label, note=""):
    d = df.set_index("policy")
    cells = []
    for p in order:
        r = d.loc[p]
        c = cell(r)
        if "fallback" in str(r.get("method", "")): c += "†"
        cells.append(c)
    return f"| {label}{note} | " + " | ".join(cells) + " |"
rows = ["| Analysis (status) | Gradient boosting | Detrended GB | SARIMA | Chronos-Bolt |", "|---|---|---|---|---|"]
rows.append(row_from(sec[sec.analysis.str.startswith("RQ2")], "Against the 4-week weekday average (secondary)"))
t = tr[tr.vs == "so"].rename(columns={"yr_mean": "mu", "yr_ci_lo": "ci_lo", "yr_ci_hi": "ci_hi"})
rows.append(row_from(t, "Mean gap across 20–50 short days a year (secondary)"))
rows.append(row_from(sec[sec.analysis.str.contains("rule R2")], "Constant cushion, R2 (secondary)"))
rows.append(row_from(sec[sec.analysis.str.contains("rule R3")], "Age-aware ordering, R3 (secondary)"))
rows.append(row_from(sec[sec.analysis.str.contains("20 short days a year vs so")], "Fixed 20 short days a year (sensitivity)"))
rows.append(row_from(sec[sec.analysis.str.contains("50 short days a year vs so")], "Fixed 50 short days a year (sensitivity)"))
so_w = sen.groupby("scenario").mean_waste_so.first()
rows.append(row_from(sen[sen.scenario == "v9base"], f"Uncalibrated v9 configuration (sensitivity; SO {so_w['v9base']:.1f}%)"))
rows.append(row_from(sen[sen.scenario == "cal_tue_sat"], f"Tue–Sat deliveries, documented calendar (exploratory; SO {so_w['cal_tue_sat']:.1f}%)"))
rows.append(row_from(sen[sen.scenario == "cal_mon_fri"], f"Mon–Fri deliveries (exploratory; SO {so_w['cal_mon_fri']:.1f}%)"))
(T / "secondary_v10.md").write_text("\n".join(rows) + "\n")

# Supplement: full sensitivity table
names = {"v9base": "Uncalibrated v9 configuration", "cal_tue_sat": "Tue–Sat deliveries (documented)", "cal_mon_fri": "Mon–Fri deliveries",
         "cal_tue_sun": "Tue–Sun deliveries", "cal_daily": "Daily deliveries", "sf_none": "No delivery shortfalls",
         "sf_v9_10pct": "10% shortfalls (v9)", "ep2": "Patient episodes (mean 2 units)", "pooled": "No blood groups (pooled stock)"}
for s in sorted(sen.scenario.unique()):
    if s.startswith("life_p3"): names[s] = f"Share arriving with 3 days = {s.split('_')[-1]}"
rows = ["| Scenario | Gradient boosting | Detrended GB | SARIMA | Chronos-Bolt | SO waste % |", "|---|---|---|---|---|---:|"]
for s in list(names):
    d = sen[sen.scenario == s].set_index("policy")
    if not set(order) <= set(d.index): continue
    rows.append(f"| {names[s]} | " + " | ".join(cell(d.loc[p]) for p in order) + f" | {so_w[s]:.2f} |")
(T / "sensitivity_v10.md").write_text("\n".join(rows) + "\n")

st = pd.read_csv(S / "11_secondary_stanford.csv")
nm = {"gb_noclin": "Gradient boosting", "dgb": "Detrended GB", "sarima": "SARIMA", "cb": "Chronos-Bolt"}
rows = ["| Target | Forecast | Mean block difference (95% bootstrap CI) | Blocks lower (of 18) |", "|---|---|---|---:|"]
for tg in [0, 25]:
    for p in nm:
        r = st[(st.policy == p) & (st.vs == "so") & (st.target == tg)].iloc[0]
        rows.append(f"| {tg} short days | {nm[p]} | {f(r.mean_block_diff)} ({ci(r.boot_ci_lo, r.boot_ci_hi)}) | {int(r.blocks_lower)} |")
(T / "stanford_sens_v10.md").write_text("\n".join(rows) + "\n")

acc = pd.read_csv(R / "42_descriptive_accuracy_mean_2012_2018.csv").set_index("policy")
lab = {"sarima": "SARIMA", "cb": "Chronos-Bolt", "dgb": "Detrended GB", "gb": "Gradient boosting", "so": "Standing order", "wa4": "4-week weekday average"}
rows = ["| Forecast | 1-day | 2-day total | 3-day total | 4-day total |", "|---|---:|---:|---:|---:|"]
for p in lab:
    a = acc.loc[p]
    rows.append(f"| {lab[p]} | {a.mae_1day:.2f} | {a.mae_2day_total:.2f} | {a.mae_3day_total:.2f} | {a.mae_4day_total:.2f} |")
(T / "accuracy_v10.md").write_text("\n".join(rows) + "\n")
print("v10 tables written")
