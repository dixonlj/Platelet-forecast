#!/usr/bin/env python3
"""Tie every number in paper/draft_v11.src.md to the results files (v11 copy of script 44, with checks for the v11 additions).

Part A recomputes each quoted number from results/ (or the public data file) and confirms the exact text
appears in the draft. Part B lists every numeric token in the abstract and body (Introduction to Conclusion,
captions and Table 3 included) and confirms each is covered by a Part A check or is a design constant
(dates, plan settings, counts of things) that is listed in DESIGN below with its source.
Writes paper/refcheck/v11_number_check.md. Run: python3 scripts/45_check_v11_numbers.py
"""
from pathlib import Path
import json, re
import pandas as pd

P = Path(__file__).resolve().parent.parent
R = P / "results" / "m10"; S = P / "study2" / "results" / "s2m10"
txt = (P / "paper/draft_v11.src.md").read_text()
M = "\u2212"
checks = []

def sg(x, d=2):   # signed, unicode minus
    return f"{x:+.{d}f}".replace("-", M)
def ng(x, d=2):   # plain number with unicode minus if negative
    return f"{x:.{d}f}".replace("-", M)
def ab(x, d=2):
    return f"{abs(x):.{d}f}"
def chk(label, s, source):
    checks.append((label, s, source, s in txt))

v = json.loads((R / "39_validation_result.json").read_text())
c = json.loads((R / "38_calibration_choice.json").read_text())
src = "results/m10/39_validation_result.json"
chk("validation waste sim vs rec (abstract)", f"waste {v['W_sim']:.2f}% simulated against {v['W_rec']:.2f}% recorded", src)
chk("emergency per short day (abstract)", f"{v['E_sim']:.2f} against {v['E_rec']:.2f} emergency units per shortage day", src)
chk("TVD (abstract)", f"weekday-pattern distance of {v['TVD']:.3f} (limit 0.20)", src)
assert not (v["A1_pass"] or v["A2_pass"] or v["A3_pass"]) and not v["calibration_passes"]
checks.append(("all three checks failed", "computed", src, True))
src = "results/m10/38_calibration_choice.json"
chk("calibration fit waste", f"it gave {c['W_sim']:.2f}% waste against 8.25% recorded", src)
chk("calibration fit emergency", f"{c['E_sim']:.2f} against 6.53 emergency units per short day", src)
chk("calibration fit TVD", f"a TVD of {c['TVD']:.3f}", src)
assert c["calendar"] == "mon_sat" and c["p2"] == 0 and c["p3"] == 0 and c["lag"] == "+1" and c["demand"] == "unit" and c["shortfall"] == "heavy_25pct"
checks.append(("chosen setting Mon-Sat, all 4-day life, lag +1, unit demand, heavy shortfalls", "computed", src, True))
g = pd.read_csv(R / "38_calibration_grid.csv")
assert len(g) == 2700 and g.E_sim.max() < 4.5
chk("2,700 combinations; none reached 4.5", "No combination of the 2,700 reached 4.5 emergency units per short day", "results/m10/38_calibration_grid.csv")

h = pd.read_csv(R / "41_primary_H1.csv").set_index("policy"); src = "results/m10/41_primary_H1.csv"
so = h.mean_waste_so.iloc[0]
chk("SO waste 5.30 (abstract)", f"(standing order waste {so:.2f}%)", src)
chk("SO waste 5.30 (results)", f"The standing order wasted {so:.2f}% on average", src)
chk("abstract four estimates", f"seasonal model {sg(h.loc['sarima'].mu)} points (95% confidence interval {sg(h.loc['sarima'].ci_lo)} to {sg(h.loc['sarima'].ci_hi)}), pretrained {sg(h.loc['cb'].mu)}, detrended boosting {sg(h.loc['dgb'].mu)}, boosting {sg(h.loc['gb'].mu)}", src)
r = h.loc["sarima"]
chk("SARIMA primary full", f"a difference of {sg(r.mu)} points (95% CI {sg(r.ci_lo)} to {sg(r.ci_hi)}; Holm-adjusted p = {r.p_holm:.2f}; lower in {r.years_lower} of 7 years)", src)
chk("CB/dGB/GB primary", f"Chronos-Bolt differed by {sg(h.loc['cb'].mu)} points ({sg(h.loc['cb'].ci_lo)} to {sg(h.loc['cb'].ci_hi)}), detrended gradient boosting by {sg(h.loc['dgb'].mu)} ({sg(h.loc['dgb'].ci_lo)} to {sg(h.loc['dgb'].ci_hi)}) and gradient boosting by {sg(h.loc['gb'].mu)} ({sg(h.loc['gb'].ci_lo)} to {sg(h.loc['gb'].ci_hi)})", src)
assert all(abs(h.loc[p].p_holm - 1.0) < 1e-9 for p in ["cb", "dgb", "gb"])
chk("other Holm p = 1.00", "their Holm-adjusted p-values were 1.00", src)
assert all((h.ci90_lo < -0.5) | (h.ci90_hi > 0.5)) and all(h.p_holm >= 0.05)
checks.append(("none equivalent (90% CI beyond ±0.5), none Holm-significant", "computed", src, True))
assert round(h.ci_lo.min(), 1) == -0.9 and round(h.ci_hi.max(), 1) == 0.7
chk("compatible range 0.9 less to 0.7 more", "about 0.9 points less waste to 0.7 points more", src)
assert h.mm_converged.all() and not h.mm_singular.any()
chk("lag-1 residual correlation range", f"was {h.lag1_resid_corr.min():.2f} to {h.lag1_resid_corr.max():.2f}, below the preset 0.3", src)
mp = min(h.sign_p.min(), h.wilcoxon_p.min()); assert mp >= 0.29
chk("sign/Wilcoxon p >= 0.29", "p ≥ 0.29 for all four", src)
chk("SARIMA years lower 5 (via primary sentence)", f"lower in {int(h.loc['sarima'].years_lower)} of 7 years", src)

st = pd.read_csv(S / "11_primary_stanford.csv").set_index("policy"); src = "study2/results/s2m10/11_primary_stanford.csv"
chk("Stanford SO window waste", f"wasting {st.window_waste_base.iloc[0]:.2f}% over the window", src)
chk("Stanford range 1.40-2.29 (abstract)", f"by {ab(st.mean_block_diff.max())} to {ab(st.mean_block_diff.min())} points", src)
chk("Stanford Holm min 0.10 (abstract)", f"(Holm-adjusted p ≥ {st.p_holm.min():.2f})", src)
assert all(st.p_holm >= 0.10 - 1e-9) and round(st.p_holm.min(), 2) == 0.10
for p, nm in [("gb_noclin", "gradient boosting"), ("dgb", "detrended gradient boosting"), ("sarima", "SARIMA"), ("cb", "Chronos-Bolt")]:
    r = st.loc[p]
    s = f"{nm} by {ab(r.mean_block_diff)}" + (" points" if p == "gb_noclin" else "") + f" ({'95% CI ' if p == 'gb_noclin' else ''}{sg(r.boot_ci_lo)} to {sg(r.boot_ci_hi)})"
    chk(f"Stanford {p}", s, src)
chk("Stanford SARIMA p and Holm", f"(p = {st.loc['sarima'].p_boot:.3f}; Holm-adjusted p = {st.loc['sarima'].p_holm:.2f})", src)
oth = st.drop("sarima").p_holm
chk("Stanford other Holm range", f"Holm-adjusted p-values for the others were {oth.min():.2f} to {oth.max():.2f}", src)
assert (st.boot_ci_hi > 0).drop("sarima").all() and st.loc["sarima"].boot_ci_hi < 0
checks.append(("only SARIMA's CI excludes zero", "computed", src, True))
assert abs(st.mmd_points.iloc[0] - 0.17) < 0.005
chk("Stanford MMD 0.17 in caption", "(0.17 points)", src)
chk("Stanford 1.4 to 2.3 (discussion)", f"by {abs(st.mean_block_diff.max()):.1f} to {abs(st.mean_block_diff.min()):.1f} points", src)
ml = pd.read_csv(S / "11_matched_levels.csv")
wa = ml[(ml.model == "wd_avg4") & (ml.target_short_days == 5)].waste_pct.iloc[0]
chk("Stanford WA4 1.08%", f"wasted only {wa:.2f}%", "study2/results/s2m10/11_matched_levels.csv")

sec = pd.read_csv(R / "41_secondary_waste.csv"); src = "results/m10/41_secondary_waste.csv"
r = sec[sec.analysis.str.startswith("RQ2") & (sec.policy == "sarima")].iloc[0]
chk("SARIMA vs WA4", f"SARIMA wasted {ab(r.mu)} points less (95% CI {sg(r.ci_lo)} to {sg(r.ci_hi)}; lower in {int(r.years_lower)} of 7 years)", src)
tr = pd.read_csv(R / "41_tradeoff_summary.csv").set_index(["policy", "vs"]); r = tr.loc[("sarima", "so")]
chk("trade-off SARIMA", f"SARIMA's mean gap against the standing order was {sg(r.yr_mean)} points ({sg(r.yr_ci_lo)} to {sg(r.yr_ci_hi)})", "results/m10/41_tradeoff_summary.csv")
r2 = sec[sec.analysis.str.contains("rule R2")]
assert (r2.mu.abs() <= 0.3).all() and ((r2.ci_lo < 0) & (r2.ci_hi > 0)).all()
chk("R2 within ±0.3", "every gap was within ±0.3 points with CIs including zero", src)
r = sec[sec.analysis.str.contains("rule R3") & (sec.policy == "sarima")].iloc[0]
chk("R3 SARIMA", f"SARIMA was {sg(r.mu)} points ({sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
chk("R3 SARIMA (discussion)", f"a larger gap ({sg(r.mu)} points)", src)
oo = pd.read_csv(R / "41_secondary_other_outcomes.csv"); src2 = "results/m10/41_secondary_other_outcomes.csv"
so_rows = oo[oo.vs == "so"]
assert ((so_rows.yr_ci_lo < 0) & (so_rows.yr_ci_hi > 0)).all()
r = oo[(oo.outcome == "lost_units") & (oo.policy == "sarima") & (oo.vs == "so")].iloc[0]
chk("SARIMA lost units", f"{abs(r.yr_mean):.0f} fewer lost units a year (95% CI {abs(r.yr_ci_lo):.0f} fewer to {r.yr_ci_hi:.0f} more)", src2)
sen = pd.read_csv(R / "41_sensitivity_vs_so.csv").set_index(["scenario", "policy"]); src = "results/m10/41_sensitivity_vs_so.csv"
chk("v9 base SARIMA/CB/dGB", f"SARIMA ({sg(sen.loc[('v9base','sarima')].mu)}) and Chronos-Bolt ({sg(sen.loc[('v9base','cb')].mu)}) wasted less than the standing order and detrended gradient boosting wasted more ({sg(sen.loc[('v9base','dgb')].mu)})", src)
assert all(sen.loc[("v9base", p)].ci_hi < 0 for p in ["sarima", "cb"]) and sen.loc[("v9base", "dgb")].ci_lo > 0
r = sen.loc[("cal_tue_sat", "sarima")]
chk("Tue-Sat SO waste + SARIMA", f"the standing order wasted {r.mean_waste_so:.1f}% and SARIMA wasted {ab(r.mu)} points less (95% CI {sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
r = sen.loc[("cal_mon_fri", "sarima")]
chk("Mon-Fri SARIMA", f"SARIMA wasted {ab(r.mu)} points less ({sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
acc = pd.read_csv(R / "42_descriptive_accuracy_mean_2012_2018.csv").set_index("policy")
assert acc.mae_1day.idxmin() == "sarima" and all(acc[c].idxmin() == "sarima" for c in ["mae_2day_total", "mae_3day_total", "mae_4day_total"])
chk("accuracy", f"({acc.loc['sarima'].mae_1day:.2f} units at 1 day and {acc.loc['sarima'].mae_4day_total:.2f} for 4-day totals, against {acc.loc['so'].mae_1day:.2f} and {acc.loc['so'].mae_4day_total:.2f} for the standing order", "results/m10/42_descriptive_accuracy_mean_2012_2018.csv")

d = pd.read_csv(P / "data/public/UKA_Aachen_daily_platelets_2008-2018.csv"); src = "data/public/UKA_Aachen_daily_platelets_2008-2018.csv"
chk("Aachen days", f"({len(d):,} days, no missing dates)", src)
chk("Aachen mean use", f"Mean use was {d.Transfused.mean():.2f} units a day", src)
chk("Aachen waste 10.1%", f"wasted {100 * d.Waste.sum() / d.Transfused.sum():.1f}% of platelet units over 2008–2018", src)
chk("Aachen purchases 6.5%", f"bought {100 * d.Purchase.sum() / d.Transfused.sum():.1f}% as emergency purchases", src)
vy = pd.read_csv(R / "39_validation_per_year.csv")
chk("recorded short days 2012-2018", "(" + ", ".join(str(int(x)) for x in vy.target_short_days[:-1]) + f" and {int(vy.target_short_days.iloc[-1])} in 2012–2018)", "results/m10/39_validation_per_year.csv")


# ---- v11 additions (R5, R6) ----
src = "results/m10/41_sensitivity_vs_so.csv"
r = sen.loc[("cal_tue_sat", "sarima")]
chk("Tue-Sat SARIMA (abstract, R5)", f"the seasonal model wasted {ab(r.mu)} points less ({sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
chk("Tue-Sat SARIMA (conclusion, R5)", f"SARIMA wasted {ab(r.mu)} points less (95% CI {sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
r = sen.loc[("cal_tue_sat", "cb")]
chk("Tue-Sat Chronos-Bolt (3.5)", f"Chronos-Bolt wasted {ab(r.mu)} points less ({sg(r.ci_lo)} to {sg(r.ci_hi)})", src)
assert all(sen.loc[("cal_tue_sat", p)].ci_hi < 0 for p in ["sarima", "cb"])
assert round(abs(sen.loc[("cal_tue_sat", "sarima")].mu)) == 2 and round(abs(sen.loc[("cal_tue_sat", "cb")].mu)) == 2
checks.append(("Tue-Sat: SARIMA and CB both about 2 points less, CIs below zero ('about 2 points less')", "computed", src, "about 2 points less" in txt))
thu_sim, thu_rec = v["sim_shares"][3], v["rec_shares"][3]
chk("Thursday waste share sim vs recorded (3.1)", f"({100 * thu_sim:.1f}% of waste, against {100 * thu_rec:.1f}% recorded)", "results/m10/39_validation_result.json")
assert thu_sim == 0.0
gl = g.loss; n5 = int((gl <= 1.05 * gl.min()).sum()); assert n5 == 1
chk("no other of 2,700 within 5% of best loss", "no other of the 2,700 combinations came within 5% of the chosen one's fit", "results/m10/38_calibration_grid.csv")
assert c["calendar"] == "mon_sat"
src = "study2/results/s2m10/11_primary_stanford.csv"
for p, nm in [("dgb", "detrended gradient boosting"), ("sarima", "SARIMA"), ("cb", "Chronos-Bolt"), ("gb_noclin", "gradient boosting")]:
    rr = st.loc[p]
    chk(f"Stanford t-interval {p} (R6)", f"{nm} {sg(rr.t_ci_lo)} to {sg(rr.t_ci_hi)}", src)
assert int((st.t_ci_hi < 0).sum()) == 3
chk("t-intervals exclude zero for three of four", "excluded zero for three of the four forecasts", src)
rel = st.relative_diff_pct.abs()
chk("Stanford relative 45% to 75% (R6)", f"{rel.min():.0f}% to {rel.max():.0f}% less waste than the standing order", src)

import os, datetime
mt = lambda f: datetime.datetime.fromtimestamp(os.path.getmtime(P / f)).strftime("%H:%M")
nh = sum(1 for l in (P / "paper/osf_prereg_input_hashes.txt").read_text().splitlines() if re.match(r"^[0-9a-f]{64} ", l))
chk("plan/manifest time stamps and count", f"the SHA-256 manifest of {nh} input files is time-stamped {mt('paper/osf_prereg_input_hashes.txt')} and the final plan {mt('paper/osf_preregistration_final.md')}", "file mtimes of paper/osf_prereg_input_hashes.txt and paper/osf_preregistration_final.md")
assert mt('paper/osf_preregistration_final.md') < mt('results/m10/38_calibration_report.md')
checks.append(("plan finalised before calibration report (04:41)", "computed", "file mtimes", True))

# Tables 1 and 2 are generated from the results by scripts/43_tables_v10.py; confirm they are current.
import subprocess, sys
before = {f: (P / "paper/tables" / f).read_text() for f in ["validation_v10.md", "secondary_v10.md"]}
subprocess.run([sys.executable, str(P / "scripts/43_tables_v10.py")], check=True, capture_output=True)
for f, t in before.items():
    checks.append((f"Table from results is current: {f}", "regenerated and compared", "scripts/43_tables_v10.py", t == (P / "paper/tables" / f).read_text()))

# ---- Part B: every numeric token in abstract + body must be covered ----
DESIGN = {  # design constants and plain facts with their source (not results)
    "5": "5 to 7 days storage [coi2024]; 5 of 509 days Stanford target (prereg 2.5)", "7": "7 days storage; 7 test years; df=6 (7−1)",
    "10.5": "Guan et al. reported 10.5% to 3.2% [guan2017]", "3.2": "Guan et al. [guan2017]", "10": "outdating 10% to 20% [flint2020]", "20": "outdating 10–20% [flint2020]; 20 short days (prereg 4.1)",
    "2008": "data start", "2018": "data end", "2012": "test years", "2009": "calibration years", "2011": "calibration years", "2014": "Stanford window", "2015": "Stanford window",
    "2022": "Aachen file public since 2022 [schilling2022]", "2026": "registration date", "14": "registration date (14 November 2026); AI use 13–14 November 2026", "13": "AI use 13–14 November 2026", "37": "scripts 37–42 (analysis code file names)", "10.17605": "DOI prefix of the OSF registration (10.17605/OSF.IO/PHQ42)", "03:41": "input manifest time stamp (file mtime of paper/osf_prereg_input_hashes.txt)", "04:04": "final plan time stamp (file mtime of paper/osf_preregistration_final.md)",
    "04:30": "analysis run window (prereg_deviations.md)", "05:10": "analysis run window", "0.1": "exploratory-study gap (prereg 3.6)", "1": "RQ1; one-week warm-up; 1 to 4 days",
    "4": "1 to 4 days ahead; 4-day order; four presets", "512": "Chronos context (prereg 2.3.1)", "28": "past-28-day mean (prereg 2.3.1)", "6": "k sweep 0 to 6; df 6; ≤6 display items; about 6 bootstrap resampling units (18 blocks / runs of 3)",
    "0": "k sweep 0 to 6", "0.0": "", "0.25": "k step (prereg 4.1)", "2": "two-day lead; 2-, 3- or 4-day orders", "3": "3 usable days; 3 tables", "1.5": "A1 rule (prereg 2.4.5)",
    "25": "A2 rule ±25%; 25% shortfall days; 25 short days Stanford sensitivity", "0.20": "A3 rule (prereg 2.4.5)", "50": "50 short days (prereg 4.1)", "0.5": "MMD (prereg 4.6)",
    "0.05": "alpha (prereg 4.5)", "90": "90% CI equivalence rule (prereg 4.7)", "95": "95% CI", "18": "18 Stanford blocks (prereg 4.4)", "509": "Stanford scored days (prereg 2.5)",
    "35": "Stanford ~35 units a day (prereg 2.5); 35 input fingerprints (osf_prereg_input_hashes.txt)", "8": "8 January scoring start", "31": "31 May 2015; recorded short days", "30": "30 runs; 30–80% filled", "80": "30–80% filled (calibration choice)",
    "0.3": "lag-1 trigger (prereg 4.11); ±0.3 R2 check", "2,700": "grid size", "15": "15 life mixes", "12": "twelve blocks", "1%": "", "22": "22% to 60% [harm2018; ning2023]", "60": "[harm2018; ning2023]",
    "8.25": "recorded calibration target (prereg 2.4.2)", "6.53": "recorded calibration target (prereg 2.4.2)", "4.5": "grid max check", "January": "",
    "40": "recorded short days", "21": "recorded short days", "38": "recorded short days", "42": "recorded short days", "D1": "", "D7": "", "D2": "", "D3": "", "D4": "", "D5": "", "D6": "", "D8": "", "256": "part of the name SHA-256",
    "2013": "D3 years 2013–2018", "2010": "D3 reason", "27": "script 27 (D5)", "November": "", "May": "", "0.17": "Stanford MMD",
}
start = txt.index("# Abstract"); end = txt.index("# Statements")
body = "\n".join(l for l in txt[start:end].split("\n") if not l.startswith("#"))   # headings carry section numbers only
body = re.sub(r"\[@[^\]]+\]", "", body); body = re.sub(r"\{\{TABLE:\w+\}\}", "", body); body = re.sub(r"\(\.\./charts/[^)]+\)\{width=100%\}", "", body)
toks = [t.rstrip(",") for t in re.findall(r"(?<![\w.])[−+]?\d[\d,]*(?:\.\d+)?(?::\d+)?", body)]
covered_text = " ".join(s for _, s, _, ok in checks if ok)
uncovered = []
for t in toks:
    core = t.lstrip("−+")
    if core in DESIGN or t in covered_text or core in covered_text:
        continue
    uncovered.append(t)
uncovered = sorted(set(uncovered))

passed = sum(ok for *_, ok in checks); total = len(checks)
out = [f"# v11 number check", "", f"Draft: `paper/draft_v11.src.md`. Run by `scripts/45_check_v11_numbers.py`.", "",
       f"**Part A: {passed} of {total} checks pass.** Each recomputes a number from the results files and confirms the exact text is in the draft.", "",
       "| # | Check | Text looked for | Source | Pass |", "|---|---|---|---|---|"]
for i, (l, s, so_, ok) in enumerate(checks, 1):
    out.append(f"| {i} | {l} | {s.replace('|', '/')} | `{so_}` | {'yes' if ok else '**NO**'} |")
out += ["", f"**Part B: {len(toks)} numeric tokens in the abstract, body, captions and Table 3; {len(uncovered)} not tied to a check or a listed design constant.**", ""]
out += ["Uncovered tokens: " + (", ".join(uncovered) if uncovered else "none"), "", "Design constants and cited facts (not results), with their source:", ""]
out += [f"- `{k}`: {v_}" for k, v_ in DESIGN.items() if v_]
(P / "paper/refcheck/v11_number_check.md").write_text("\n".join(out) + "\n")
print(f"Part A: {passed}/{total} pass; Part B: {len(toks)} tokens, uncovered: {uncovered}")
for l, s, so_, ok in checks:
    if not ok: print("FAIL:", l, "|", s)
