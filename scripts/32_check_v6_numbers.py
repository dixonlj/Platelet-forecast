#!/usr/bin/env python3
"""Check that the numbers quoted in paper/draft_v6.src.md match the results files.
Each check recomputes a number from results/ and confirms the exact string appears in the text.
Writes paper/refcheck/v6_number_check.md. Run: .venv/bin/python scripts/32_check_v6_numbers.py
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

P = Path(__file__).resolve().parent.parent
R = P / "results"; M9 = R / "m9"
txt = (P / "paper/draft_v6.src.md").read_text()
sup = (P / "paper/supplement_v6.src.md").read_text()
checks = []


def chk(label, value_str, where=txt, context=None):
    ok = (context or value_str) in where
    checks.append((label, value_str, ok))


tt = pd.read_csv(M9 / "29_target_tests.csv")
def T(t, o, m): return tt[(tt.target == t) & (tt.outcome == o) & (tt.model == m)].iloc[0]
W, Lo = "Waste (points)", "Wasted + emergency units a year"
h = {m: T("hospital", W, m) for m in ["hgbr", "gbdt", "chronos", "sarima", "rnn", "lasso"]}
chk("WA waste 8.9", f"versus {h['hgbr'].mean_weekday_average:.1f}%")
chk("SARIMA/CB/GB waste", f"({h['sarima'].mean_model:.1f}%, {h['chronos'].mean_model:.1f}% and {h['hgbr'].mean_model:.1f}% versus {h['hgbr'].mean_weekday_average:.1f}%)")
chk("main text means", f"(7-year means {h['hgbr'].mean_model:.1f}%, {h['chronos'].mean_model:.1f}% and {h['sarima'].mean_model:.1f}% against {h['hgbr'].mean_weekday_average:.1f}%)")
for m in ["hgbr", "chronos", "sarima"]:
    assert h[m].years_better == 4 and h[m].ci_lo < 0 < h[m].ci_hi
checks.append(("4 of 7 and CIs include 0 (GB, CB, SARIMA)", "computed", True))
chk("gbdt waste 9.6", f"wasted more ({h['gbdt'].mean_model:.1f}%)")
chk("gbdt less in 2/7", f"({h['gbdt'].mean_model:.1f}%; less in {h['gbdt'].years_better} of 7 years)")
chk("RNN 6/7 8.2 p", f"wasted less in {h['rnn'].years_better} of 7 years ({h['rnn'].mean_model:.1f}%; sign test p = {h['rnn'].sign_p:.3f})")
pw = pd.read_csv(M9 / "29_power.csv").set_index("model")
mdd = pw.loc[["hgbr", "chronos", "sarima"], "approx_min_detectable_gap_80pct"]
chk("MDD range", f"about {mdd.min():.1f} to {mdd.max():.1f} points")
for m in ["chronos", "sarima"]:
    assert T("fixed20", W, m).years_better == 7 and T("fixed20", W, m).ci_hi < 0
assert T("fixed20", W, "hgbr").years_better == 6 and T("fixed20", W, "hgbr").ci_hi < 0
checks.append(("20 short days: CB 7/7, SARIMA 7/7, GB 6/7, CIs exclude 0", "computed", True))
assert max(T("fixed50", W, m).years_better for m in ["hgbr", "chronos", "sarima"]) == 4
checks.append(("50 short days: ours at most 4/7", "computed", True))
assert all(T(t, W, "gbdt").mean_diff > 0 for t in ["fixed20", "hospital", "fixed50"])
checks.append(("gbdt never better on mean waste at any target", "computed", True))
c, s_ = T("hospital", Lo, "chronos"), T("hospital", Lo, "sarima")
chk("CB lost", f"all 7 years ({abs(c.mean_diff):.0f} fewer a year; 95% CI {abs(c.ci_hi):.0f} to {abs(c.ci_lo):.0f}; sign test p = {c.sign_p:.3f})")
chk("SARIMA lost", f"SARIMA in {s_.years_better} ({abs(s_.mean_diff):.0f} fewer; {abs(s_.ci_hi):.0f} to {abs(s_.ci_lo):.0f})")
g = T("hospital", Lo, "hgbr")
chk("GB lost", f"({g.years_better} of 7; {abs(g.mean_diff):.0f} fewer, CI −{abs(g.ci_hi):.0f} to {abs(g.ci_lo):.0f})")
chk("gbdt lost", f"detrended gradient boosting had {T('hospital', Lo, 'gbdt').mean_diff:.0f} more")
dc = pd.read_csv(M9 / "29_lost_decomposition.csv")
cm = dc[(dc.model == "chronos") & (dc.year == "mean")].iloc[0]; sm = dc[(dc.model == "sarima") & (dc.year == "mean")].iloc[0]
chk("decomposition CB", f"About {100 * cm.share_of_lost_gap_from_waste:.0f}% of Chronos-Bolt's advantage ({abs(cm.waste_unit_gap):.0f} of {abs(cm.lost_unit_gap):.0f} units) and {100 * sm.share_of_lost_gap_from_waste:.0f}% of SARIMA's")
yr = dc[(dc.model == "chronos") & (dc.year != "mean")].copy(); yr["year"] = yr.year.astype(int)
rev = yr[(yr.waste_unit_gap > 0) & (yr.emergency_unit_gap < 0)].year.tolist()
rev2 = yr[(yr.waste_unit_gap < 0) & (yr.emergency_unit_gap > 0)].year.tolist()
assert rev == [2015, 2016, 2017] and rev2 == [2013, 2014, 2018], (rev, rev2)
checks.append(("CB trade years 2015-17 vs 2013/14/18", "computed", True))
a = pd.read_csv(M9 / "27_accuracy_by_horizon.csv")
mae = a.groupby(["horizon_days", "model"]).mae.mean(); bias = a.groupby(["horizon_days", "model"]).mean_error_actual_minus_fc.mean()
chk("1-day MAEs", f"(3.75 units a day, against {mae[(1,'chronos')]:.2f} for Chronos-Bolt, {mae[(1,'hgbr')]:.2f} for both gradient-boosting versions and {mae[(1,'dow4')]:.2f}")
assert f"{mae[(1,'gbdt')]:.2f}" == f"{mae[(1,'hgbr')]:.2f}" and f"{mae[(1,'sarima')]:.2f}" == "3.75"
chk("GB 4-day", f"(MAE {mae[(4,'hgbr')]:.2f} versus {mae[(4,'dow4')]:.2f}) and forecast {bias[(4,'hgbr')]:.1f} units too low")
chk("gbdt 4-day", f"({bias[(4,'gbdt')]:.1f} units too low) and cut its 4-day MAE to {mae[(4,'gbdt')]:.2f}")
chk("4-day others", f"SARIMA ({mae[(4,'sarima')]:.2f}), the source authors' LASSO (8.90) and Chronos-Bolt ({mae[(4,'chronos')]:.2f})")
ob = pd.read_csv(M9 / "27_bias_by_order_type.csv").groupby(["model", "order_type"]).bias_actual_minus_fc.mean()
th = "Thursday order (Fri-Mon, 4 days)"
chk("Thursday bias", f"were {abs(ob[('gbdt', th)]):.1f} units too high on average, while the original's were {ob[('hgbr', th)]:.1f} units too low")
s26 = pd.read_csv(M9 / "26_weekend_summary.csv")
q = s26[(s26.target == "hospital")]
alt = q[(q.calendar != "base") & (q.model == "sarima")]
assert (alt.years_less_waste_than_wa == 7).all() and (alt.waste_gap_ci_hi < 0).all()
chk("SARIMA calendar gap range", f"gaps {abs(alt.mean_waste_gap_pts).min():.1f} to {abs(alt.mean_waste_gap_pts).max():.1f} points")
cb = q[(q.calendar != "base") & (q.model == "chronos")].years_less_waste_than_wa
gb = q[(q.calendar != "base") & (q.model == "hgbr")].years_less_waste_than_wa
chk("CB calendar years", f"Chronos-Bolt was ahead in {int(cb.min())} to {int(cb.max())} years and gradient boosting in {int(gb.min())} to {int(gb.max())}")
cbl = q[q.model == "chronos"].years_fewer_lost_than_wa
assert cbl.min() >= 6 and (q[(q.calendar != "base") & (q.model == "sarima")].years_fewer_lost_than_wa == 7).all()
checks.append(("CB lost 6-7/7 all calendars; SARIMA 7/7 alternatives", "computed", True))
wa = q[q.model == "dow4"].set_index("calendar")
chk("halving", f"({wa.loc['base','mean_waste_pct']:.1f}% to {wa.loc[['mon_sat','tue_sun','daily'],'mean_waste_pct'].min():.1f}–{wa.loc[['mon_sat','tue_sun','daily'],'mean_waste_pct'].max():.1f}% for the weekday average)")
chk("emergency per short day", f"({wa.emergency_per_short_day.min():.1f} to {wa.emergency_per_short_day.max():.1f}) than the hospital bought (8.8)")
chk("Monday share", f"({100*wa.loc['tue_sun','monday_share_of_short_days']:.0f}% against 29%), and the documented calendar gave {100*wa.loc['base','monday_share_of_short_days']:.0f}%")
wd = pd.read_csv(M9 / "26_waste_share_by_weekday.csv").set_index(["calendar", "model"])
chk("recorded Wed 28%", f"and {100*wd.loc[('RECORDED','hospital'),'Wed']:.0f}% on Wednesdays")
chk("sim Sun 18%", f"the simulation put {100*wd.loc[('base','dow4'),'Sun']:.0f}% on Sundays")
cd = pd.read_csv(M9 / "28_cushion_diagnosis.csv")
f17 = cd[(cd.year == 2017)].set_index("variant").waste_pct_mean; f18 = cd[(cd.year == 2018)].set_index("variant").waste_pct_mean
chk("cushion 7.6 -> 13.2", f"({f17['fixed cushion']:.1f}% to {f17['day-by-day cushion (script 05)']:.1f}% in 2017)")
chk("cushion rescaled", f"waste was {f17['day-by-day shape, fixed-rule size (diagnostic)']:.1f}% and {f18['day-by-day shape, fixed-rule size (diagnostic)']:.1f}%, close to the fixed cushion's {f17['fixed cushion']:.1f}% and {f18['fixed cushion']:.1f}%")
r = cd.set_index(["year", "variant"])
ratios = [r.loc[(y, "day-by-day cushion (script 05)"), "mean_cushion_thursday_units"] / r.loc[(y, "day-by-day cushion (script 05)"), "mean_cushion_sun_wed_units"] for y in (2017, 2018)]
chk("cushion ratio", f"cushion {min(ratios):.1f} to {max(ratios):.1f} times")
# Earlier numbers carried from v5 (sources as in v5)
rc = pd.read_csv(R / "m5/09_reality_check_summary.csv").set_index("policy")
chk("reality 8.5 vs 9.7", f"{rc.loc['standing','mean_sim_waste_pct']:.1f}% simulated waste over 2012–2018 against {rc.loc['standing','mean_hosp_waste_pct']:.1f}% recorded")
chk("emergency 1,242 vs 2,099", f"({rc.loc['standing','total_sim_emergency']:,.0f} against {rc.loc['standing','total_hosp_emergency']:,.0f}")
pr = pd.read_csv(R / "m8/20_year_level_tests.csv")
pc = pr[(pr.analysis.str.startswith("cushion")) & (pr.model == "chronos") & (pr.outcome.str.startswith("Wasted"))].iloc[0]
chk("prior CB", f"({abs(pc.mean_diff):.0f} fewer; 95% CI {abs(pc.ci_hi):.0f} to {abs(pc.ci_lo):.0f})")
ps = pr[(pr.analysis.str.startswith("cushion")) & (pr.model == "sarima") & (pr.outcome.str.startswith("Wasted"))].iloc[0]
chk("prior SARIMA", f"SARIMA was ahead in {ps.years_better} of 7 ({abs(ps.mean_diff):.0f} fewer; CI −{abs(ps.ci_hi):.0f} to {abs(ps.ci_lo):.0f})")
acc = pd.read_csv(R / "m8/20_accuracy_by_horizon.csv")
best2 = acc[acc.horizon_days == 2].pivot(index="year", columns="model", values="mae").idxmin(axis=1)
best4 = acc[acc.horizon_days == 4].pivot(index="year", columns="model", values="mae").idxmin(axis=1)
assert (best2 == "sarima").sum() == 1 and best2[2018] == "sarima" and best2[2014] == "chronos" and (best4 == "sarima").sum() == 3
chk("SARIMA best 1 of 7 at 2 days", "best forecast in 1 of 7 years at 2 days (2018, plus a near-tie with Chronos-Bolt in 2014) and 3 of 7 at 4 days")
f42 = pd.read_csv(M9 / "27_dm_1day_holm42.csv"); n42 = f42.assign(sig=f42.holm_p_42 < .05).groupby("model").sig.sum()
o35 = pd.read_csv(R / "m8/20_dm_1day_holm.csv"); n35 = o35.assign(sig=o35.holm_p < .05).groupby("model").sig.sum()
chk("Holm 35 counts", f"significant in {n35['DM_sarima_vs_dow4']} of 7 years, gradient boosting's in {n35['DM_hgbr_vs_dow4']} and Chronos-Bolt's in {n35['DM_chronos_vs_dow4']}")
chk("Holm 42 counts", f"Chronos-Bolt's count fell to {n42['DM_chronos_vs_dow4']} and detrended gradient boosting had none")
assert n42["DM_gbdt_vs_dow4"] == 0
lines = ["# Draft v6 number check", "", "| Check | Text searched | Result |", "|---|---|---|"]
lines += [f"| {l} | {v.replace('|', '/')} | {'OK' if ok else 'MISMATCH'} |" for l, v, ok in checks]
bad = [c for c in checks if not c[2]]
lines += ["", f"{len(checks) - len(bad)} of {len(checks)} checks passed."]
(P / "paper/refcheck").mkdir(exist_ok=True)
(P / "paper/refcheck/v6_number_check.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[-1:]))
for b_ in bad: print("MISMATCH:", b_[0], "|", b_[1])
