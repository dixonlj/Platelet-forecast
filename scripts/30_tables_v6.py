#!/usr/bin/env python3
"""Draft v6 tables (paper/tables/*_v6.md) straight from the results files. No simulation.
Run: .venv/bin/python scripts/30_tables_v6.py
Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
"""
from pathlib import Path
import numpy as np
import pandas as pd

P = Path(__file__).resolve().parent.parent
T = P / "paper/tables"; R = P / "results"; M9 = R / "m9"
N = {"dow4": "Weekday average", "hgbr": "Gradient boosting", "gbdt": "Gradient boosting, detrended",
     "chronos": "Chronos-Bolt", "sarima": "SARIMA", "lasso": "Authors’ LASSO", "rnn": "Authors’ RNN",
     "standing": "Standing weekday order"}
CAL = {"base": "Tue–Sat (documented, base)", "weekdays": "Mon–Fri (no weekend)", "mon_sat": "Mon–Sat",
       "tue_sun": "Tue–Sun", "daily": "Every day"}
CALS = ["base", "weekdays", "mon_sat", "tue_sun", "daily"]


def md(name, cols, rows, cap=18):
    wid = [max([len(w) + 3 for w in str(cols[i]).split()] + [min(len(str(r[i])), cap) + 2 for r in rows] + [10])
           for i in range(len(cols))]
    s = "| " + " | ".join(cols) + " |\n|" + "|".join(["-" * wid[0]] + ["-" * (w - 1) + ":" for w in wid[1:]]) + "|\n"
    s += "".join("| " + " | ".join(map(str, r)) + " |\n" for r in rows)
    (T / f"{name}_v6.md").write_text(s)


def p(x): return "<0.001" if x < .001 else ("1.00" if x >= .9995 else f"{x:.3g}")
def gap(m, lo, hi, f=".2f"): return f"{m:+{f}} ({lo:+{f}} to {hi:+{f}})"


tt = pd.read_csv(M9 / "29_target_tests.csv")
tt["isw"] = (tt.outcome == "Waste (points)").astype(bool)

# Table 2: main results at recorded short days
rows = []
h = tt[tt.target == "hospital"]
w0 = h[h.isw].iloc[0].mean_weekday_average
l0 = h[~h.isw].iloc[0].mean_weekday_average
rows.append([N["dow4"], f"{w0:.2f}", f"{l0:.0f}", "—", "—"])
for m in ["hgbr", "gbdt", "chronos", "sarima", "lasso", "rnn"]:
    a = h[(h.model == m) & h.isw].iloc[0]
    b = h[(h.model == m) & ~h.isw].iloc[0]
    rows.append([N[m], f"{a.mean_model:.2f}", f"{b.mean_model:.0f}",
                 gap(a.mean_diff, a.ci_lo, a.ci_hi) + f"; {a.years_better}/7",
                 gap(b.mean_diff, b.ci_lo, b.ci_hi, ".0f") + f"; {b.years_better}/7"])
md("table2", ["Forecast", "Waste %", "Lost units/year", "Waste gap (95% CI); years lower",
              "Lost gap (95% CI); years lower"], rows)

# Table 3: waste gap at three service levels
rows = []
for m in ["hgbr", "gbdt", "chronos", "sarima", "rnn"]:
    r = [N[m]]
    for t in ["fixed20", "hospital", "fixed50"]:
        a = tt[(tt.target == t) & (tt.model == m) & tt.isw].iloc[0]
        r.append(f"{a.mean_diff:+.2f} ({a.ci_lo:+.2f} to {a.ci_hi:+.2f}); {a.years_better}/7")
    rows.append(r)
wa = [tt[(tt.target == t) & tt.isw].iloc[0].mean_weekday_average for t in ["fixed20", "hospital", "fixed50"]]
rows.insert(0, ["Weekday average, waste %"] + [f"{v:.2f}" for v in wa])
md("service", ["Forecast", "20 short days a year", "Recorded short days (21–42)", "50 short days a year"], rows)

# Supplement: full target tests
rows = []
for _, a in tt.iterrows():
    rows.append([{"hospital": "Recorded", "fixed20": "20", "fixed50": "50"}[a.target], a.outcome, N[a.model],
                 f"{a.years_better}/7", p(a.sign_p), p(a.wilcoxon_p),
                 gap(a.mean_diff, a.ci_lo, a.ci_hi, ".2f" if a.isw else ".0f")])
md("target_tests", ["Short days", "Outcome", "Forecast vs weekday average", "Years lower", "Sign p", "Wilcoxon p",
                    "Mean difference (95% CI)"], rows)

# Table 4 (main): delivery calendars
s = pd.read_csv(M9 / "26_weekend_summary.csv")
log = (M9 / "26_run_log.txt").read_text()
rows = []
for c in CALS:
    g = s[(s.calendar == c) & (s.target == "hospital")].set_index("model")
    r = [CAL[c], f"{g.loc['dow4', 'mean_waste_pct']:.1f}"]
    for m in ["sarima", "chronos", "hgbr", "gbdt"]:
        r.append(f"{g.loc[m, 'mean_waste_gap_pts']:+.2f}; {int(g.loc[m, 'years_less_waste_than_wa'])}/7")
    r += [f"{g.loc['dow4', 'emergency_per_short_day']:.1f}", f"{100 * g.loc['dow4', 'monday_share_of_short_days']:.0f}%"]
    rows.append(r)
import re
eps = float(re.search(r"emergency units per short day ([\d.]+)", log).group(1))
mon = float(re.search(r"Monday share of short days ([\d.]+)", log).group(1))
rows.append(["Hospital's record", "—", "—", "—", "—", "—", f"{eps:.1f}", f"{100 * mon:.0f}%"])
md("calendar", ["Delivery days", "Weekday average waste %", "SARIMA gap; years lower", "Chronos-Bolt gap; years lower",
                "Gradient boosting gap; years lower", "Detrended GB gap; years lower",
                "Emergency units per short day*", "Short days on a Monday*"], rows)

# Supplement: full calendar table
rows = []
for c in CALS:
    for t in ["hospital", "fixed20"]:
        g = s[(s.calendar == c) & (s.target == t)]
        for _, a in g.iterrows():
            if a.model in ("dow4", "standing"):
                wg = lg = "—"
            else:
                wg = gap(a.mean_waste_gap_pts, a.waste_gap_ci_lo, a.waste_gap_ci_hi) + f"; {int(a.years_less_waste_than_wa)}/7"
                lg = gap(a.mean_lost_gap_units, a.lost_gap_ci_lo, a.lost_gap_ci_hi, ".0f") + f"; {int(a.years_fewer_lost_than_wa)}/7"
            rows.append([CAL[c], "Recorded" if t == "hospital" else "20", N[a.model], f"{a.mean_waste_pct:.2f}", wg,
                         f"{a.mean_lost_units:.0f}", lg, f"{a.emergency_per_short_day:.1f}",
                         f"{100 * a.monday_share_of_short_days:.0f}%"])
md("calendar_full", ["Delivery days", "Short days", "Forecast", "Waste %", "Waste gap (95% CI); years lower",
                     "Lost units/year", "Lost gap (95% CI); years lower", "Emergency units per short day",
                     "Monday share of short days"], rows)

# Supplement: waste share by weekday
wd = pd.read_csv(M9 / "26_waste_share_by_weekday.csv")
rows = []
for c in CALS + ["RECORDED"]:
    g = wd[(wd.calendar == c) & (wd.model.isin(["dow4", "hospital"]))]
    for _, a in g.iterrows():
        rows.append([("Hospital's record" if c == "RECORDED" else CAL[c] + ", weekday average")] +
                    [f"{100 * a[d]:.0f}%" for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]])
md("waste_weekday", ["Calendar", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], rows)

# Supplement: detrended GB accuracy
a = pd.read_csv(M9 / "27_accuracy_by_horizon.csv")
dm = pd.read_csv(M9 / "27_dm_tests.csv")
h42 = pd.read_csv(M9 / "27_dm_1day_holm42.csv")
rows = []
for n in (1, 2, 4):
    wa_ = a[(a.model == "dow4") & (a.horizon_days == n)].set_index("year").mae
    for m in ["dow4", "hgbr", "gbdt", "chronos", "sarima"]:
        g = a[(a.model == m) & (a.horizon_days == n)].set_index("year")
        yb = "—" if m == "dow4" else f"{int((g.mae < wa_).sum())}/7"
        if m == "gbdt":
            d = dm[(dm.horizon_days == n) & (dm.comparison == "gbdt vs dow4")]
            hs = str(int((d[d.year != "pooled 2012-2018"].holm_p_within_7_years.astype(float) < .05).sum()))
            if n == 1:
                hs += f" ({int((h42[h42.model == 'DM_gbdt_vs_dow4'].holm_p_42 < .05).sum())} of 42)"
            pp = p(float(d[d.year == "pooled 2012-2018"].dm_p.iloc[0]))
        else:
            hs = pp = "—"
        rows.append([f"{n}-day", N[m], f"{g.mae.mean():.2f}", f"{g.mean_error_actual_minus_fc.mean():+.2f}", yb, hs, pp])
md("gbdt_accuracy", ["Horizon", "Forecast", "Mean MAE (units)", "Mean bias (actual − forecast)",
                     "Years more accurate than WA", "Years significant vs WA after Holm*", "Pooled DM p vs WA"], rows)

ob = pd.read_csv(M9 / "27_bias_by_order_type.csv")
rows = []
for m in ["dow4", "hgbr", "gbdt", "chronos", "sarima"]:
    g = ob[ob.model == m].groupby("order_type").bias_actual_minus_fc.mean()
    rows.append([N[m], f"{g['Sun-Wed orders (2 days)']:+.2f}", f"{g['Thursday order (Fri-Mon, 4 days)']:+.2f}"])
md("order_bias", ["Forecast", "Sun–Wed orders, 2-day total", "Thursday order, Fri–Mon 4-day total"], rows)

# Supplement: lost-unit decomposition
dc = pd.read_csv(M9 / "29_lost_decomposition.csv")
rows = []
for m in ["chronos", "sarima", "hgbr", "rnn"]:
    g = dc[dc.model == m]
    for _, r in g.iterrows():
        rows.append([N[m], r.year, f"{r.waste_unit_gap:+.0f}", f"{r.emergency_unit_gap:+.0f}", f"{r.lost_unit_gap:+.0f}",
                     f"{100 * r.share_of_lost_gap_from_waste:.0f}%" if r.year == "mean" else ""])
md("decomp", ["Forecast", "Year", "Wasted units gap", "Emergency units gap", "Lost units gap",
              "Share of lost gap from waste"], rows)

# Supplement: power
pw = pd.read_csv(M9 / "29_power.csv")
md("power", ["Forecast", "SD of the 7 yearly waste gaps (points)", "Half-width of 95% CI", "Gap detectable with 80% power"],
   [[N[r.model], f"{r.sd_of_yearly_waste_gap:.2f}", f"{r.ci_half_width:.2f}", f"{r.approx_min_detectable_gap_80pct:.2f}"]
    for _, r in pw.iterrows()])

# Supplement: cushion diagnosis
u = pd.read_csv(M9 / "28_cushion_units.csv")
cd = pd.read_csv(M9 / "28_cushion_diagnosis.csv")
cw = pd.read_csv(M9 / "28_waste_by_weekday.csv")
rows = []
for _, r in cd.iterrows():
    sh = cw[(cw.year == r.year) & (cw.variant == r.variant)].set_index("dow").share
    rows.append([int(r.year), r.variant, f"{r.waste_pct_mean:.2f}", f"{r.k_matched_mean:.2f}",
                 f"{r.mean_cushion_sun_wed_units:.1f}", f"{r.mean_cushion_thursday_units:.1f}",
                 f"{100 * (sh['Mon'] + sh['Tue']):.0f}%"])
md("cushion", ["Year", "Cushion", "Waste %", "Matched k", "Cushion, Sun–Wed orders (units)",
               "Cushion, Thursday order (units)", "Waste on Mon + Tue"], rows)
md("cushion_units", ["Year", "Order", "Fixed unit", "Band (q90 − q50) mean", "Band / fixed unit"],
   [[int(r.year), r.order_type, f"{r.fixed_unit:.1f}", f"{r.band_mean:.1f}", f"{r.band_over_fixed:.2f}"] for _, r in u.iterrows()])
print("v6 tables written")

# Per-year tables with detrended GB added (supplement S5.10 / S5.11)
inv = pd.read_csv(M9 / "27_multiyear_inventory.csv")
a8 = pd.read_csv(R / "m5/08_multiyear_inventory.csv").query("model in ['lasso', 'rnn']")
inv = pd.concat([inv, a8[inv.columns.intersection(a8.columns)]], ignore_index=True)
hh = inv[inv.target == "hospital"]
MS6 = ["dow4", "hgbr", "gbdt", "chronos", "sarima", "lasso", "rnn"]
SH = {"dow4": "WA", "hgbr": "GB", "gbdt": "GB detrended", "chronos": "Chronos-Bolt", "sarima": "SARIMA",
      "lasso": "LASSO", "rnn": "RNN"}
for col, n, fmt in [("waste_pct_mean", "annual_waste", ".2f"), ("wasted_plus_emergency_mean", "annual_lost", ".0f"),
                    ("emergency_units_mean", "annual_emerg", ".0f")]:
    pv = hh.pivot(index="year", columns="model", values=col)
    md(n, ["Year"] + [SH[m] for m in MS6], [[int(y)] + [format(pv.loc[y, m], fmt) for m in MS6] for y in pv.index] +
       [["Mean"] + [format(pv[m].mean(), fmt) for m in MS6]])
print("v6 annual tables written")
