#!/usr/bin/env python3
"""Check that the numbers quoted in paper/draft_v8.src.md (and new v8 numbers in supplement_v8.src.md) match the results files.
Each check recomputes a number from results/ and confirms the exact string appears in the text.
Writes paper/refcheck/v8_number_check.md. Run: python3 scripts/35_check_v8_numbers.py
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

P = Path(__file__).resolve().parent.parent
R = P / "results"; M9 = R / "m9"
txt = (P / "paper/draft_v8.src.md").read_text()
sup = (P / "paper/supplement_v8.src.md").read_text()
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
chk("gbdt waste 9.6 (documented calendar)", f"under the documented calendar ({h['gbdt'].mean_model:.1f}%")
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
chk("Thursday bias", f"were {abs(ob[('gbdt', th)]):.1f} units too high on average, the original's {ob[('hgbr', th)]:.1f} units too low")
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
chk("Monday share", f"({100*wa.loc['tue_sun','monday_share_of_short_days']:.0f}% against 29%; Table 4)")
wd = pd.read_csv(M9 / "26_waste_share_by_weekday.csv").set_index(["calendar", "model"])
chk("recorded Wed 28%", f"and {100*wd.loc[('RECORDED','hospital'),'Wed']:.0f}% on Wednesdays")
chk("sim Sun 18%", f"the simulation put {100*wd.loc[('base','dow4'),'Sun']:.0f}% on Sundays")
cd = pd.read_csv(M9 / "28_cushion_diagnosis.csv")
f17 = cd[(cd.year == 2017)].set_index("variant").waste_pct_mean; f18 = cd[(cd.year == 2018)].set_index("variant").waste_pct_mean
chk("cushion 7.6 -> 13.2", f"({f17['fixed cushion']:.1f}% to {f17['day-by-day cushion (script 05)']:.1f}% in 2017)")
chk("cushion rescaled (extra-features GB label)", f"waste was {f17['day-by-day shape, fixed-rule size (diagnostic)']:.1f}% and {f18['day-by-day shape, fixed-rule size (diagnostic)']:.1f}%, close to that extra-features model's {f17['fixed cushion']:.1f}% and {f18['fixed cushion']:.1f}% with the fixed cushion")
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

# ---------------- New in v8 ----------------
from scipy import stats as _st
wd8 = pd.read_csv(M9 / "26_weekend_delivery.csv")
def G(cal, tg, mod, ref, col="waste_pct_mean"):
    g = wd8[(wd8.calendar == cal) & (wd8.target == tg)].pivot(index="year", columns="model", values=col)
    x = g[mod] - g[ref]
    lo, hi = _st.t.interval(0.95, 6, loc=x.mean(), scale=x.std(ddof=1) / np.sqrt(7))
    return x.mean(), lo, hi, int((x < 0).sum())
LO = "wasted_plus_emergency_mean"
st_mean = q[(q.calendar == "base") & (q.model == "standing")].mean_waste_pct.iloc[0]
chk("standing order 8.5% (abstract)", f"A standing order wasted {st_mean:.1f}%")
w = G("base", "hospital", "standing", "dow4"); l = G("base", "hospital", "standing", "dow4", LO)
chk("standing vs 4-week WA", f"The standing order wasted {st_mean:.1f}%, less than the 4-week weekday average in {w[3]} of 7 years ({abs(w[0]):.2f} points; 95% CI {abs(w[2]):.2f} to {abs(w[1]):.2f}), with {abs(l[0]):.0f} fewer lost units a year in all {l[3]} years")
tb2 = (P / "paper/tables/table2_v8.md").read_text()
chk("Table 2 standing row", f"| Standing weekday order (last year) | {st_mean:.2f} |", where=tb2)
gs = {m: G("base", "hospital", m, "standing") for m in ["sarima", "chronos", "hgbr"]}
f2 = lambda v: f"{v:+.2f}".replace("-", "−")
chk("vs standing: SARIMA/CB/GB gaps and years", f"({f2(gs['sarima'][0])}, {f2(gs['chronos'][0])} and {f2(gs['hgbr'][0])}; {gs['sarima'][3]}, {gs['chronos'][3]} and {gs['hgbr'][3]} of 7 years lower; every CI included zero)")
assert all(v[1] < 0 < v[2] for v in gs.values()) and max(abs(v[0]) for v in gs.values()) < 0.15
checks.append(("vs standing: CIs include 0 and |gap| < 0.15 (\"within about 0.1 points\")", "computed", True))
ls_ = {m: G("base", "hospital", m, "standing", LO)[0] for m in ["sarima", "chronos", "hgbr"]}
assert max(abs(v) for v in ls_.values()) < 4.5
chk("vs standing lost: CB 2, SARIMA 4 fewer", f"Chronos-Bolt and SARIMA had only {abs(ls_['chronos']):.0f} and {abs(ls_['sarima']):.0f} fewer lost units a year")
chk("vs standing lost (Discussion)", f"but only {abs(ls_['chronos']):.0f} and {abs(ls_['sarima']):.0f} fewer than the standing order")
g20 = {m: G("base", "fixed20", m, "standing") for m in ["sarima", "chronos", "hgbr"]}
chk("20 short days vs standing", f"(SARIMA {f2(g20['sarima'][0])}, Chronos-Bolt {f2(g20['chronos'][0])}, gradient boosting {f2(g20['hgbr'][0])} points; {g20['sarima'][3]} of 7 years each")
assert g20["sarima"][3] == g20["chronos"][3] == g20["hgbr"][3] == 4
alt8 = {c: G(c, "hospital", "sarima", "standing") for c in ["weekdays", "mon_sat", "tue_sun", "daily"]}
mn, mx = min(abs(v[0]) for v in alt8.values()), max(abs(v[0]) for v in alt8.values())
yl = [v[3] for v in alt8.values()]
excl = [c for c, v in alt8.items() if v[2] < 0]
assert excl == ["mon_sat"] and all(v[0] < 0 for v in alt8.values())
chk("SARIMA vs standing other calendars (main)", f"({mn:.2f} to {mx:.2f} points; {min(yl)} to {max(yl)} of 7 years; the CI excluded zero only for Monday to Saturday")
chk("SARIMA vs standing other calendars (supplement)", f"({mn:.2f} to {mx:.2f} points at the recorded short days; {min(yl)} to {max(yl)} of 7 years; the CI excluded zero only for Mon–Sat)", where=sup)
assert f"{mn:.1f}" == "0.3" and f"{mx:.1f}" == "0.4"
chk("abstract 0.3-0.4", "shrank to about 0.3–0.4 points")
chk("Discussion/Conclusion 0.3 to 0.4", "about 0.3 to 0.4 points")
gd = q[(q.model == "gbdt")].set_index("calendar")
assert gd.loc["base", "mean_waste_gap_pts"] > 0 and gd.loc["weekdays", "mean_waste_gap_pts"] > 0
assert all(gd.loc[c, "mean_waste_gap_pts"] < 0 for c in ["mon_sat", "tue_sun", "daily"])
dd = gd.loc["daily"]
chk("detrended GB daily 7/7 (main)", f"but less with daily deliveries (all {int(dd.years_less_waste_than_wa)} years; {abs(dd.mean_waste_gap_pts):.2f} points; 95% CI {abs(dd.waste_gap_ci_hi):.2f} to {abs(dd.waste_gap_ci_lo):.2f})")
chk("detrended GB daily (supplement)", f"in all {int(dd.years_less_waste_than_wa)} years with daily deliveries ({abs(dd.mean_waste_gap_pts):.2f} points; 95% CI {abs(dd.waste_gap_ci_hi):.2f} to {abs(dd.waste_gap_ci_lo):.2f})", where=sup)
checks.append(("detrended GB: more waste under base and Mon-Fri, less (mean) under Mon-Sat, Tue-Sun, daily", "computed", True))
chk("Mon-Fri WA barely changed 8.8%", f"barely changed it ({wa.loc['weekdays','mean_waste_pct']:.1f}%)")
chk("Mon-Fri WA (supplement)", f"barely changed it ({wa.loc['weekdays','mean_waste_pct']:.1f}%)", where=sup)
assert (S := pd.read_csv(M9 / "26_weekend_summary.csv")) is not None
assert f"{mae[(1,'gbdt')]:.2f}" == f"{mae[(1,'hgbr')]:.2f}" and mae[(2,'gbdt')] < mae[(2,'hgbr')] and mae[(4,'gbdt')] < mae[(4,'hgbr')]
chk("detrended accuracy wording", "more accurate on average for 2- and 4-day totals (tied at 1 day)")
ha = pd.read_csv(R / "aachen/hospital_actual_2018_window.csv")
v = sorted(ha.waste_pct.dropna().tolist()[1:])
assert [round(x, 2) for x in v] == [1.33, 1.99]
chk("source authors 4.9/5% and released 2018 output 1.3-2%", "about 5% simulated waste (4.9% with LASSO, 5% with the RNN) over their study period [@schilling2022]; their released 2018 simulation output, over a different window, gives 1.3–2%")
checks.append(("Schilling 2022 reports 4.93% (LASSO) and 5% (RNN): checked against the published abstract/Results text", "external", True))
oc = pd.read_csv(R / "m5/10_us_one_change.csv")
gb18 = oc[(oc.scenario == "German rules (base)") & (oc.model == "hgbr")].waste_pct_mean.iloc[0]
chk("main GB 2018 6.8%", f"(the main gradient boosting wasted {gb18:.1f}% in 2018)")
chk("Table S5.8 note 6.78%", f"not the main gradient boosting (2018 waste {gb18:.2f}%", where=sup)
cu = (P / "paper/tables/cushion_v8.md").read_text()
chk("Table S5.8 relabelled", "| fixed cushion (GB with extra features) |", where=cu)
import re as _re
ab = txt.split("# Abstract")[1].split("**Keywords")[0]
ab = _re.sub(r"\*\*(Background|Methods|Results|Conclusions)\.\*\*", "", ab)
checks.append((f"abstract words ≤ 250 ({len(ab.split())})", "computed", len(ab.split()) <= 250))
for bad_word in ["preregist", "pre-registered", "pre-specified"]:
    checks.append((f"absent: {bad_word}", "computed", bad_word.lower() not in (txt + sup).lower()))

lines = ["# Draft v8 number check", "", "| Check | Text searched | Result |", "|---|---|---|"]
lines += [f"| {l} | {v.replace('|', '/')} | {'OK' if ok else 'MISMATCH'} |" for l, v, ok in checks]
bad = [c for c in checks if not c[2]]
lines += ["", f"{len(checks) - len(bad)} of {len(checks)} checks passed."]
(P / "paper/refcheck").mkdir(exist_ok=True)
(P / "paper/refcheck/v8_number_check.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[-1:]))
for b_ in bad: print("MISMATCH:", b_[0], "|", b_[1])
