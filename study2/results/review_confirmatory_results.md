# Independent review: Study 2 confirmatory results (NHSBT monthly platelets)

**Reviewer:** Research Reviewer (AI), for Liam Dixon
**Date:** 19 November 2026, about 12:05 PM ET
**What I reviewed:** `prereg/osf_prereg_study2_draft_v3.md`, `results/CONFIRMATORY_RESULTS_SUMMARY.md`, everything in `results/nhsbt_confirmatory/`, `results/confirmatory_run_console.log` and the two charts. I also pulled the public OSF registration myself.
**How:** I worked from the files and from my own reruns, not from Transfusion Forecast Lab's (TFL's) description. I wrote only to this file and to `/tmp/study2_rerun/`. I edited none of the author's files and contacted no one.

---

## Bottom line (plain words)

- **The run is clean.** OSF registered the plan at 1:20 AM ET. The analysis started at 11:48:52 AM ET, about 10.5 hours later. The code and data are exactly the registered versions, and I found no sign of an earlier NHSBT run.
- **It reproduces exactly.** I reran the frozen code on a copy in `/tmp`. Every output table came out byte-for-byte identical, including all bootstrap intervals. I also recomputed the three main tests with my own separate code, and they match.
- **The verdict follows the rule.** None of the three models can be called better or worse than "same month last year". That is the correct pre-registered result.
- **The SARIMA blow-up is real but is not in the confirmatory result.** It sits only in the COVID sensitivity analysis, for FFP, red cells and cryo. Platelets are clean there too.
- **What needs fixing is mostly wording.** One sentence in the headline paragraph reads like "they're equally good", which the plan can't claim. The summary also undersells how precise the ETS and SARIMA results actually are, and it describes the SARIMA blow-up only partly.

**Counts:** 1 Required, 6 Recommended, 8 Optional.

---

## 0. Timing and integrity: PASS

| Check | Result |
|---|---|
| OSF registration exists | Yes. `https://api.osf.io/v2/registrations/vrh2u/`: public, not withdrawn, no embargo, not archiving. `doi.org/10.17605/OSF.IO/VRH2U` redirects to `https://osf.io/vrh2u/`. |
| Registration time | `date_registered` = 2026-11-19T06:20:00.7 UTC = **1:20:00 AM ET, 19 Nov 2026** |
| Registered files vs local | I downloaded all 5 attached files through the public API. All 5 SHA-256 hashes match `prereg/osf_upload/` and the summary's table: PDF `986fb521…`, `nhsbt_analysis.py` `dcb2f18c…`, `inference.py` `0e5248d4…`, `FROZEN_CODE.sha256` `e1e20b89…`, `SHA256SUMS.txt` `32e9f1eb…`. |
| Registered plan text vs local plan | I compared the registered PDF's text with `osf_prereg_study2_draft_v3.md` word by word. The match is 97.6%, and every difference is PDF formatting: page footers, spacing before punctuation, hashes split across lines, and the DM formula typeset. **There are no wording changes.** The OSF form fields match the paste sheet word for word, except field 344-4, which is OSF's standard "authors have observed the data" option. |
| Code hashes | The manifest, `FROZEN_CODE.sha256`, plan line 119 and the current files all show `dcb2f18c…` and `0e5248d4…`. `sha256sum -c` passes. |
| Snapshot hash | `f0e3fbc5…6e4696` in the manifest, the plan, `SHA256SUMS.txt` and the current file. |
| Software | Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1, openpyxl 3.1.5, which match both the plan and the manifest. |
| Run after registration | The file **creation** times show the console log was created at **11:48:52 AM ET** (the run start) and the output folder at 11:48:53. All 9 outputs were created at **11:49:58 AM ET** (the end). That puts the start about **10 h 29 min after** registration. |
| Earlier NHSBT run? | **None found.** Every output file's creation time is 11:49:58, so nothing older was overwritten. There were no other `forecasts_long` or `primary_result` files anywhere on the box. The only other copies of the workbook are raw downloads (`/tmp/study2-scout/`, 18 Nov 7:32 PM ET) with no model outputs beside them. The pre-registration structure check (00:19 AM ET) logged that it fitted nothing. There is **no git history**, so this can't be *proven*, but every trace is consistent with a single post-registration run. |

Small timing note: the manifest's `run_at` (11:49:58) is when the run **finished**, not when it started. TFL's message said "started at 11:49:58", but the summary's own wording ("completed") is correct.

## 1. Reproduction: EXACT

- I copied the two scripts, `FROZEN_CODE.sha256`, the plan and the snapshot to `/tmp/study2_rerun/study2/` and ran `python3 -B nhsbt_analysis.py --nhsbt --osf-url https://osf.io/vrh2u/`. The guard passed, and the run took 89 seconds.
- **8 of 9 output files are byte-identical** to the author's: accuracy, comparisons, lag-2 check, fit summary, warning log, forecasts, naive 2021/2019 and primary_result.md. `run_manifest.json` differs only in the input path and the `run_at` time, as expected.
- **Independent check:** I wrote my own code, not using `inference.py`, for the paired MAE, the circular block bootstrap (block 3, seed 20261118, 10,000 reps), DM with HLN and t(35), and Holm. ETS −0.6341 (−5.816 to 3.819), p 0.8014. SARIMA −0.4358 (−5.633 to 4.067), p 0.8649. Regression +7.8295 (0.660 to 15.739), p 0.0223, Holm 0.0669. **These are identical to the reported values.**
- **I also checked the rest of the pipeline:**
  - I rebuilt the calendar regression with statsmodels OLS at all 36 origins. It agrees to within 3×10⁻¹¹.
  - Every seasonal naive forecast equals the value 12 months earlier, exactly.
  - Every "all months" row of the comparisons table has the right n and point difference, with 0 mismatches.
- **Robustness:** across 50 other seeds and block lengths 1–8, the regression's lower CI limit stays between 0.4 and 1.6. It never crosses zero, and the ETS and SARIMA intervals barely move. The intervals don't depend on a lucky seed.

## 2. Decision rule: FOLLOWED EXACTLY

- **The three comparisons:** exactly the three pre-registered ones, at 1 month, on platelets, in the main run: ETS, SARIMA and regression, each against seasonal naive. The code refuses to run unless it finds exactly 3 (`apply_primary_rule`).
- **Signs:** difference = MAE(method) − MAE(naive), so a negative number means the model was more accurate. The tables, summary and chart all use this convention.
- **DM test:** Newey-West lag h−1 = 0 at h = 1, the HLN factor, and a t distribution with 35 degrees of freedom, as planned.
- **Holm:** the sorted raw p-values are 0.0223, 0.8014 and 0.8649. The first is tested at 0.05/3 = 0.0167, and since 0.0223 > 0.0167 nothing is rejected and Holm stops. The adjusted p-values are 0.0669, 1.000 and 1.000. This is correct.
- **Joint rule:** the regression's interval excludes zero, but Holm did not reject, so the verdict is "couldn't tell them apart". That is right, because the plan requires both. ETS and SARIMA fail both checks.
- **7 units/day:** it is used only as the plan says, for a practical label after a declared difference. No difference was declared, so every row correctly gets "no claim".
- The "unreliable" label is applied after the verdict and never changes it. No primary row is labelled unreliable.

## 3. Summary numbers vs output tables: ALL MATCH

I checked every number in `CONFIRMATORY_RESULTS_SUMMARY.md` against the tables:
- the primary table
- the horizon table (12 MAEs)
- the 2- and 3-month differences and their CIs
- the Sep–Oct 2025 sensitivity
- the COVID sensitivity for platelets (including "34 paired, 2 omitted" and "11 of 36 on fallback")
- the secondary products (red cells, FFP, cryo, and the red-cell shift)
- the red-cell split checks (n = 19 and 17, all including zero)
- the unreliable label (red cells, ETS, COVID run, 24/36)
- the blow-up values
- the output-file hashes

**All match, with correct rounding.** For example, 4.8245 → "4.82" and 0.30497 → "0.30". The one wording problem is in issue R3 below.

## 4. Labelling: HONEST, with one wording slip

The confirmatory result is kept separate from everything else. Secondary horizons, other products and sensitivities are all marked "descriptive", and the tables carry `role` = descriptive with "descriptive only" verdicts. **I found no post-hoc outcome-dependent analysis.** The charts and summary came after the run and change no numbers. The suggestion that COVID months cause the regression's poor showing is labelled as an interpretation, and my own check supports it (see O6). The one slip is the "as expected by chance" sentence (R3).

## 5. The SARIMA blow-up: verified, and it's a gap in the rules, not a bug

**What I found:**
- The FFP COVID-sensitivity forecast from the **April 2023** origin is **−6.238 × 10¹¹ units/day** at all three horizons. That makes FFP SARIMA's MAE about 1.73 × 10¹⁰.
- **I refitted every SARIMA model** (2 runs × 4 products × 36 origins = 288 fits) and checked the fitted parameters. There are **6 broken fits, all in the COVID sensitivity:** red cells Oct 2023, FFP Apr 2023 and Sep 2023, and cryo Apr 2023, Nov 2023 and Jan 2024.
- **All 6 use the *main* SARIMA specification, not the fallback.** In each one, the seasonal moving-average coefficient came out between 10¹³ and 10¹⁵. A sane value is between −1 and 1. Five of the six also have a residual variance of essentially zero.
- **Why the six failure rules missed it:**
  - No exception and no warning was raised.
  - statsmodels reported `converged = True`.
  - The forecast was a finite number.
  - So rules (a) to (f) all passed. The code applied the rules correctly, which is why I call it **a gap in the rules, not a bug**: the rules check whether the optimiser *says* it worked, not whether the answer makes sense.
- **The likely trigger:** the code fits SARIMA with `enforce_stationarity=False, enforce_invertibility=False`. That lets the coefficient run off to absurd values when 22 months are missing, because seasonal differencing across the COVID gap leaves very little usable data. In `/tmp` I refitted the same 6 origins with statsmodels' default constraints, and all 6 gave sensible forecasts. For example, FFP Apr 2023 gives 478, 468 and 464 units/day against an actual of about 488. These two settings are inside the hashed, registered code, but **the plan's text never mentions them**.

**Does it touch anything confirmatory? No.**
- The main run has no missing months. All 144 main-run SARIMA fits are sane: the largest coefficient is about 1.00, and there are no fallbacks, no omissions and no warnings at all (the warning log has zero main-run rows). ETS had 0 omissions too.
- Holm uses only the three main-run platelet tests.
- **Platelets in the COVID sensitivity are also clean.** The largest coefficient there is 1.36, there are 0 broken fits, and the reported +0.30 (−2.19 to 2.99) is usable.
- The broken fits affect only the COVID-sensitivity SARIMA rows for FFP, red cells and cryo, at all horizons. That includes the red-cell SARIMA COVID MAE of 212.5 against naive's 116.6, which the summary doesn't mention.

**Fallback and unreliable labels:**
- **Main run:** 0 fallbacks and 0 omissions for all products.
- **COVID run, SARIMA fallback:** platelets 11/36, red cells 11/36, FFP 10/36, cryo 9/36. All are under half, so none is labelled unreliable.
- **COVID run, ETS omitted:** platelets 2/36, red cells 24/36 (labelled unreliable, correctly), FFP 12/36, cryo 0/36.

**Is the disclosure adequate?** Partly. The summary flags the right origins and correctly says nothing confirmatory is affected. It doesn't say:
- that the broken fits came from the main specification and reported "converged";
- what the likely cause is, namely the unconstrained estimation the plan text never mentions;
- that the tables still show **"ok"** next to an MAE of 1.7 × 10¹⁰;
- that the COVID platelet SARIMA result is unaffected.

See R4 for suggested wording.

## 6. Overstatement and statistics

- **Equivalence wording.** No equivalence test was pre-registered. Two phrases in the headline paragraph (summary line 13) cross the line: "ETS and SARIMA were almost exactly as accurate as the baseline" and "a one-line baseline is about as good as the standard models". The second one also sweeps in the regression, whose point estimate is 7.8 units/day *worse*. See R1.
- **Informative or underpowered?** For **ETS and SARIMA**, the 95% intervals (−5.8 to 3.8 and −5.6 to 4.1) sit **entirely inside ±7**. Looked at after the fact and only descriptively, the data make a 7-unit/day difference either way unlikely for those two. That is more than the summary's "may not be able to detect a 7 units/day difference" (line 142) gives them credit for. For the **regression**, the interval (0.7 to 15.7) includes 7, so it can't rule out a meaningful *worsening*. Two caveats:
  - The plan doesn't treat a 95% interval inside ±7 as an equivalence test.
  - Percentile bootstrap intervals from 36 points are probably a little too narrow (see R5).
- **n = 36 and autocorrelation.** The one-step loss differences for ETS and SARIMA show almost no autocorrelation (lag-1 −0.04). For the regression, the lag-1 autocorrelation is +0.24, so the lag-0 DM test is slightly too generous to it. The pre-registered descriptive lag-2 check (p = 0.053) shows this. It can't change the verdict, because a larger p only makes "not rejected" more certain.
- **Is the regression's poor result a bug?** No. My independent OLS matches to within 10⁻¹¹. It is a misfit: the fitted trend runs downhill, −0.3 to −0.8 units/day per month, pulled down by 2016–2020 and the COVID dip, while 2022–2025 levelled off. It **under-forecast in 33 of 36 months**, by an average of 21 units/day. Dropping the COVID rows brings its MAE from 22.9 to 13.1.
- **Charts.**
  - Chart 1 is honest and shows one idea, with numbers that match.
  - Chart 2 is honest and labelled descriptive. It shows no intervals, though, and n changes by horizon (36, 35, 34). Its title states point estimates as a finding.
  - Neither chart overstates the result.

---

## Issues

### Required (fix before anything is made public)

**R1. The headline paragraph implies equivalence.**
*Where:* `CONFIRMATORY_RESULTS_SUMMARY.md` line 13, the sentences "ETS and SARIMA were almost exactly as accurate as the baseline (less than 1 unit/day apart…)" and "on this smooth national monthly series, a one-line baseline is about as good as the standard models."
*Problem:* this is "they're the same" language, and no equivalence test was pre-registered. It also lumps in the regression, which looked *worse*, not similar. A journal reviewer will flag it straight away, and it's the sentence most likely to be quoted.
*Fix:* use something like: "ETS and SARIMA differed from the baseline by less than 1 unit/day on average (95% intervals about −6 to +4), and the regression was 7.8 units/day worse on average, but under the pre-registered rule none of the three could be told apart from 'same month last year'. Not being able to tell them apart is not proof that they are equal." Fix the same phrasing anywhere it appears in the abstract or preprint.

### Recommended

**R2. Report precision, not just "maybe underpowered".**
*Where:* summary line 142 (Limits) and the primary-result section.
*Fix:* add a clearly labelled **post-hoc, descriptive** sentence: "The 95% intervals for ETS and SARIMA lie entirely within ±7 units/day, so differences as large as the pre-stated smallest meaningful difference look unlikely for these two methods. This was not a pre-registered equivalence test, and bootstrap intervals from 36 months may be somewhat too narrow. The regression's interval (0.7 to 15.7) does not rule out a meaningful worsening." My chart `/tmp/study2_rerun/review_chart.png` shows this.

**R3. "As expected by chance" is wrong.**
*Where:* summary line 80.
*Problem:* 20 of 141 descriptive intervals exclude zero, about 14%, against the roughly 5% you'd expect from chance alone. Only 7 of the 141 have a raw p below 0.05. The pattern isn't random: 10 of the 20 are the regression or SARIMA being *worse* on platelets or FFP (mostly the regression, across all three horizons), 6 are ETS or SARIMA doing *better* on red cells, and 4 are COVID-sensitivity cryo rows.
*Fix:* "Twenty of 141 descriptive intervals exclude zero. These tests overlap heavily and are not corrected for multiple testing, so none is a finding; the recurring pattern (the regression trailing the baseline, and the models' error growing at 2–3 months) is described, not claimed."

**R4. Make the SARIMA blow-up disclosure complete.**
*Where:* summary lines 66–72, plus the "ok" labels in `comparisons_vs_naive.csv` and `primary_result.md` for the COVID-sensitivity SARIMA rows (FFP, red cells, cryo).
*Fix:* without changing any frozen output, add to the summary or write-up that:
- (a) 6 COVID-sensitivity SARIMA fits broke: red cells Oct 2023, FFP Apr and Sep 2023, cryo Apr, Nov 2023 and Jan 2024;
- (b) all 6 used the **main** specification and reported `converged = True`, with a seasonal MA coefficient of 10¹³–10¹⁵ and near-zero variance;
- (c) the likely cause is the frozen code's unconstrained estimation (`enforce_stationarity=False, enforce_invertibility=False`), which the plan text didn't state;
- (d) **COVID-sensitivity SARIMA results for FFP, red cells and cryo are not interpretable at any horizon, despite their "ok" label**;
- (e) the COVID-sensitivity *platelet* SARIMA result is unaffected.

Optionally, add a clearly labelled **exploratory** rerun with statsmodels' default constraints, kept in a separate folder and never replacing the registered numbers. In any future plan, add a plausibility rule, for example "a forecast outside 0.5× to 2× the last observed value counts as a failure".

**R5. Say that the bootstrap intervals may be a bit narrow.**
*Where:* the summary's limits section.
*Problem:* in 13 of the 20 descriptive rows where the interval excludes zero, the DM test's p is 0.05 or above. That points to percentile block-bootstrap intervals from 34–36 points running somewhat narrower than the DM test, a known small-sample behaviour. The confirmatory verdict is protected, because the rule requires both checks. But the "hint that the regression was worse" (line 32) leans on the interval.
*Fix:* add one line saying this, and keep the regression wording as "a hint, not a finding".

**R6. Spell out the timeline: start time, and a run that can't be proven unique.**
*Where:* the summary's timeline table (lines 95–100) and `run_manifest.json`.
*Problem:* the manifest only records the **finish** time. The file creation times show a start of 11:48:52 AM ET. There is no git history, so "only one run" rests on file timestamps.
*Fix:* in the summary, add "run started 11:48:52 AM ET (console-log creation time), finished 11:49:58 AM ET". Before any public release, put the outputs and hashes under version control, or attach `SHA256SUMS` of the outputs to the OSF project as a timestamped file. That needs Liam's OK, since it's public.

### Optional

- **O1.** `confirmatory_run_console.log` is one line ("Done."). For future runs, log the guard's pass lines and the start time.
- **O2.** Mention in the write-up that the authors had seen the workbook's values, including test-period months, before registration (the 682 units/day "descriptive mean" in the plan, line 155). It is already disclosed on OSF (field 344-4) and in the plan, but readers of a preprint won't see it.
- **O3.** In the main run, one SARIMA MA coefficient sits on the invertibility boundary (about −1.00) at most origins. That usually means the seasonal pattern is fixed, so seasonal differencing is more than needed. The forecasts are sane. Worth one line for statisticians.
- **O4.** Chart 2: add the n per horizon (36, 35, 34) and say in the caption that the lines are point estimates, with no intervals shown. Consider making the title neutral ("Average error by horizon").
- **O5.** Chart 1: label the −7 line as well as the +7 line. The x-axis could stop at about 20 to remove empty space.
- **O6.** Strengthen the regression interpretation (line 62) with the facts: it under-forecast in 33 of 36 months, by an average of 21 units/day, because the fitted trend points downhill. It's still an interpretation.
- **O7.** Mention that COVID-sensitivity FFP ETS left out 12 of 36 origins (33%). It isn't labelled unreliable, but it's sizeable.
- **O8.** OSF study type is "Simulation study" (a judgement already noted in the paste sheet). In a preprint, describe it as "a pre-registered retrospective forecasting comparison" to avoid confusion.

---

## Verdicts

- **Preprint: Minor revision.** Fix R1, which is one paragraph, plus R2–R4 ideally. The analysis is pre-registered, timestamped, reproducible to the byte and correctly decided. It's an honest null.
- **Journal: Major revision as it stands.** The analysis itself needs nothing re-run. What exists is a results summary, not a manuscript. A journal would also want:
  - R1–R5 handled;
  - the COVID-sensitivity SARIMA problem shown with a labelled exploratory re-estimate;
  - placement against prior work (Nandi, Roberts & Nandi, Transfusion 2020);
  - a frank statement that 36 monthly errors from one national series give limited evidence.

  With those, I'd expect it to land at minor revision. This is a small, careful, null methods comparison, so aim for a journal that publishes pre-registered null results.

**A reminder:** this is an AI review. It does not replace a human statistician (especially for the bootstrap and DM points and the SARIMA estimation question) or a transfusion-medicine specialist (on whether 7 units/day and national monthly issues are the right yardsticks). Making anything public, including posting to OSF or a preprint server, is Liam's own decision.

---

### Reviewer's working files (in /tmp only, not shared)
- `/tmp/study2_rerun/study2/results/nhsbt_confirmatory/`: full rerun outputs
- `/tmp/study2_rerun/indep/indep.py`, `reg.py`, `scan.py`, `blowup.py`, `sarima_scan.csv`: independent checks
- `/tmp/osf_dl/`: the OSF files and registered form fields, downloaded publicly
- `/tmp/study2_rerun/review_chart.png`: one chart showing the three 1-month differences with 95% intervals against the ±7 units/day band
