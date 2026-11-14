#!/usr/bin/env python3
"""Draft v8 tables. Re-tabulates existing results only (no new simulation runs).
- table2_v8.md, service_v8.md: v6 tables plus a standing-order row (gaps against the 4-week weekday average).
- standing_v8.md (Supplement Table S8.4): every forecast against the standing weekday order, all calendars, both targets.
- cushion_v8.md: Table S5.8 with the comparator labelled as gradient boosting with extra features.
Source: results/m9/26_weekend_delivery.csv (per-year means of 30 runs). Run: .venv/bin/python scripts/34_tables_v8.py
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

P = Path(__file__).resolve().parent.parent
T = P / "paper/tables"
d = pd.read_csv(P / "results/m9/26_weekend_delivery.csv")
NAMES = {"dow4": "4-week weekday average", "hgbr": "Gradient boosting", "gbdt": "Gradient boosting, detrended",
         "chronos": "Chronos-Bolt", "sarima": "SARIMA", "standing": "Standing weekday order"}
CAL = {"base": "Tue–Sat (documented, base)", "weekdays": "Mon–Fri (no weekend)", "mon_sat": "Mon–Sat",
       "tue_sun": "Tue–Sun", "daily": "Every day"}

def m(x): return f"{x:+.2f}".replace("-", "−")
def mu(x): return f"{x:+.0f}".replace("-", "−")

def gap(cal, target, model, ref, col):
    g = d[(d.calendar == cal) & (d.target == target)].pivot(index="year", columns="model", values=col)
    x = g[model] - g[ref]
    lo, hi = stats.t.interval(0.95, len(x) - 1, loc=x.mean(), scale=x.std(ddof=1) / np.sqrt(len(x)))
    return x.mean(), lo, hi, int((x < 0).sum()), g[model].mean()

def cell(v, f):
    return f"{f(v[0])} ({f(v[1])} to {f(v[2])}); {v[3]}/7"

# Table 2 and Table 3: add the standing order row
w = gap("base", "hospital", "standing", "dow4", "waste_pct_mean")
l = gap("base", "hospital", "standing", "dow4", "wasted_plus_emergency_mean")
t2 = (T / "table2_v6.md").read_text().rstrip("\n").split("\n")
t2 = [r.replace("| Weekday average |", "| 4-week weekday average |") for r in t2]
t2.insert(3, f"| Standing weekday order (last year) | {w[4]:.2f} | {l[4]:.0f} | {cell(w, m)} | {cell(l, mu)} |")
(T / "table2_v8.md").write_text("\n".join(t2) + "\n")

w20 = gap("base", "fixed20", "standing", "dow4", "waste_pct_mean")
t3 = (T / "service_v6.md").read_text().rstrip("\n").split("\n")
t3 = [r.replace("| Weekday average, waste % |", "| 4-week weekday average, waste % |") for r in t3]
t3.insert(3, f"| Standing weekday order (last year) | {cell(w20, m)} | {cell(w, m)} | not run |")
(T / "service_v8.md").write_text("\n".join(t3) + "\n")

# Supplement Table S8.4: against the standing order
rows = ["| Delivery days | Target | Forecast | Waste gap vs standing order (95% CI); years lower | Lost gap vs standing order (95% CI); years lower |",
        "|--------------------|----------|-------------------:|-------------------:|-------------------:|"]
for cal in CAL:
    for tg, tn in (("hospital", "Recorded"), ("fixed20", "20 a year")):
        for mod in ["dow4", "hgbr", "gbdt", "chronos", "sarima"]:
            rows.append(f"| {CAL[cal]} | {tn} | {NAMES[mod]} | {cell(gap(cal, tg, mod, 'standing', 'waste_pct_mean'), m)} | "
                        f"{cell(gap(cal, tg, mod, 'standing', 'wasted_plus_emergency_mean'), mu)} |")
(T / "standing_v8.md").write_text("\n".join(rows) + "\n")

c = (T / "cushion_v6.md").read_text()
c = c.replace("| fixed cushion |", "| fixed cushion (GB with extra features) |")
c = c.replace("| day-by-day cushion (script 05) |", "| day-by-day cushion (GB with extra features, script 05) |")
(T / "cushion_v8.md").write_text(c)
print("wrote table2_v8, service_v8, standing_v8, cushion_v8")
