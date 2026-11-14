# Preregistered journal revision: results in plain English

*14 November 2026. These analyses were run exactly as set out in `paper/osf_preregistration_final.md`. **Correction:** the plan was finalised (04:04 ET) and its inputs hashed (03:41 ET) before the analyses, but it was registered on OSF only afterwards, later on 14 November 2026; the earlier note here saying it was registered at about 04:25 ET was wrong (the link was an unsubmitted draft). See deviation D8. Where this summary says "preregistered", read "per the analysis plan". Every deviation is listed in `paper/prereg_deviations.md`. The work is educational and advisory only, uses public data only, and is a simulation, not real ordering. The paper has **not** been rewritten yet.*

## The short version

1. **The simulation failed its own pre-set reality check.** We tuned it on 2009–2011, then checked it on 2012–2018. It came out at 5.2% waste against 9.7% recorded, 5.0 emergency units per short day against 8.8, and a weekday pattern that missed the target (TVD 0.23, limit 0.20). All three checks failed. The plan says this must go in the abstract, and every main result is "conditional on a simulation that failed validation".
2. **Main question (Aachen): did any forecast waste less than last year's standing order?** None was demonstrated, and none was shown to be equivalent either. All four differences are small, with confidence intervals crossing zero. SARIMA came closest: −0.33 points (95% CI −0.88 to +0.22; Holm p = 0.75).
3. **Second hospital (Stanford).** All four forecasts wasted less than the standing order, by about 1.4 to 2.3 points (the standing order wasted 2.9%). The uncertainty is large, though, and none survived the Holm correction (adjusted p 0.10 to 0.22). By the preregistered rule, all four comparisons are a **"consistent null"** across the two sites.
4. **Secondary and sensitivity results** (not confirmatory) mostly lean the same way. SARIMA, and to a lesser extent Chronos-Bolt, tend to waste slightly less than the standing order. The size of that edge depends heavily on the **delivery calendar**. It is large when there is a long 4-day weekend order and small when there is not. None of these results can be used to claim a confirmed benefit.

## 1. Calibration and validation (RQ6), standing order only

- **Calibration.** We tried 2,700 combinations of delivery calendar, shelf life on arrival, logging delay, demand clumping and delivery shortfalls, each with 30 runs. The rules picked:
  - **Mon–Sat deliveries**;
  - every unit arriving with 4 days of life;
  - waste logged 1 day late;
  - single-unit demand;
  - heavy delivery shortfalls (25% of delivery days filled only 30–80%).

  On 2009–2011 this gave 7.7% waste (target 8.25%), 4.0 emergency units per short day (target 6.5) and a weekday TVD of 0.195. No combination got the emergency size above 4.5 units per short day, so none reproduced the size of the hospital's emergency orders. Report: `results/m10/38_calibration_report.md`, saved 04:41 ET and fingerprinted before any other forecast was run.
- **Validation on 2012–2018** (`results/m10/39_validation_report.md`, saved 04:45 ET):

| Check | Simulated | Recorded | Rule | Result |
|---|---|---|---|---|
| A1: overall waste | 5.22% | 9.74% | within 1.5 points | **Fail** |
| A2: emergency units per short day | 5.00 | 8.82 | 6.6 to 11.0 | **Fail** |
| A3: weekday waste pattern (TVD) | 0.226 | — | ≤ 0.20 | **Fail** |
| A4: year-by-year agreement (descriptive) | correlation 0.25; average miss 4.4 points | | | |

In plain words, the simulated hospital is tidier than the real one. It wastes about half as much, and its emergencies are smaller. The settings that fit 2009–2011 did not carry over to later years (exploratory observation E1).

Chart: `charts/m10_calibration_validation.png`, titled "The calibrated simulation failed its pre-set check: it wastes about half as much as Aachen recorded".

## 2. Primary result, Aachen (H1a–d)

Setup: the calibrated simulation, the cushion sized to each order's days (R1), matched to each year's recorded short days, 30 runs, 2012–2018. The model is a mixed model over 84 four-week blocks, with the CI and p from a t distribution with 6 degrees of freedom and Holm correction across the 4 tests. The standing order wasted 5.30% on average.

| Hypothesis | Forecast minus standing order (points of waste) | 95% CI | p | Holm p | Years lower (of 7) | Label |
|---|---|---|---|---|---|---|
| H1a Gradient boosting | **+0.17** | −0.35 to +0.69 | 0.44 | 1.00 | 4 | Not demonstrated |
| H1b Detrended GB | **+0.07** | −0.61 to +0.75 | 0.82 | 1.00 | 4 | Not demonstrated |
| H1c SARIMA | **−0.33** | −0.88 to +0.22 | 0.19 | 0.75 | 5 | Not demonstrated |
| H1d Chronos-Bolt | **−0.12** | −0.74 to +0.50 | 0.65 | 1.00 | 5 | Not demonstrated |

- **Answer to RQ1 (preregistered wording): "Not demonstrated."** No forecast met "waste reduction demonstrated". None was "practically equivalent" either, because every 90% CI reaches beyond ±0.5 points. So we cannot say "no difference". The honest summary is that the data are compatible with anything from about 0.9 points less waste to 0.7 points more.
- **Checks reported alongside, as the plan requires.**
  - Year-level means: +0.21, +0.16, −0.24 and −0.04 points.
  - Sign and Wilcoxon tests: all p ≥ 0.29.
  - The two-stage bootstrap gives the same picture (SARIMA −0.78 to +0.12).
  - All four mixed models converged without a singular fit, so no fallback was needed.
  - Block-to-block residual correlation was 0.14 to 0.29, below the 0.3 trigger.
- The plan predicted this outcome in advance: with only 7 years, differences near 0.5 points can't be resolved (Section 4.6).

Chart: `charts/m10_primary_vs_standing_order.png`, titled "Aachen: no forecast clearly wasted less than last year's standing order".

## 3. Stanford replication (RQ5)

Setup: Stanford public `pip` data, 8 Jan 2014 to 31 May 2015 (509 days), 3-day shelf life, daily orders, matched to shortages on 5 days (1%). The statistics use a moving-block bootstrap over 18 four-week blocks, with Holm correction across 4 tests. The minimum meaningful difference is 6% of the standing order's waste, which is 0.17 points here.

| Forecast minus standing order | Mean block difference (points) | 95% bootstrap CI | p | Holm p | Blocks lower (of 18) | Whole-window waste: forecast vs SO |
|---|---|---|---|---|---|---|
| Gradient boosting | **−1.40** | −3.58 to +0.75 | 0.22 | 0.22 | 9 | 1.58% vs 2.86% |
| Detrended GB | **−2.18** | −4.31 to +0.04 | 0.054 | 0.16 | 11 | 0.83% vs 2.86% |
| SARIMA | **−2.29** | −4.52 to −0.12 | 0.026 | 0.10 | 11 | 0.72% vs 2.86% |
| Chronos-Bolt | **−2.06** | −4.15 to +0.02 | 0.061 | 0.16 | 10 | 0.94% vs 2.86% |

- **Labels.** All four are "Not demonstrated". SARIMA's interval excludes zero only before the Holm correction.
- **Replication verdict (preregistered rule).** All four are a **consistent null**, because neither site shows a Holm-significant difference.
- **Honest context.** At Stanford, the standing order was the weakest method. It needed a buffer of +55 units to hold shortages at 5 days, against +37 to +42 for the others. Even the simple 4-week weekday average wasted only 1.08%. The point estimates there clearly favour the forecasts, but 18 blocks are too few to be sure.
- **Stanford sensitivity results (secondary).**
  - At 25 short days, all four forecasts again wasted less (−0.6 to −0.9 points). Only Chronos-Bolt's CI excluded zero, and that is unadjusted.
  - At 0 short days, the results were mixed (detrended GB +1.67; Chronos-Bolt −2.27; both CIs include zero).
  - The clinical-data reference models (lasso and Guan LP) also wasted less than the standing order (−1.8 to −2.5 points).

Chart: `charts/m10_stanford_vs_standing_order.png`, titled "Stanford: forecasts wasted less than the standing order, but the evidence is too uncertain to count".

## 4. Secondary results, Aachen

These are not confirmatory: unadjusted, with intervals given only for context.

- **RQ2: compared with the 4-week weekday average.**
  - SARIMA: −0.54 (−1.03 to −0.05), lower in 6 of 7 years.
  - Chronos-Bolt: −0.33 (−0.70 to +0.05).
  - GB: −0.03.
  - Detrended GB: −0.11.
  - The standing order itself: −0.21 (−1.09 to +0.67).
- **RQ3: the trade-off across 20–50 short days a year.** This is the mean gap against the standing order, with no levels excluded.
  - SARIMA: −0.41 (−0.85 to +0.02).
  - Chronos-Bolt: −0.21.
  - GB: +0.09.
  - Detrended GB: +0.06.
  - Against the weekday average, SARIMA was −0.49 (−0.87 to −0.11) and lower in all 7 years.
  - Chart: `charts/m10_tradeoff_curves.png`, titled "Accepting more short days cuts waste for every method; the methods differ by less than one point".
- **RQ4: other ordering rules, compared with the standing order.**
  - Constant cushion (R2): every gap is within ±0.3 points, and every CI includes zero.
  - Age-aware rule (R3): SARIMA −0.66 (−1.11 to −0.20, lower in 6 of 7 years) and Chronos-Bolt −0.37 (CI includes zero).
  - The standing order's own waste was 5.30% under R1, 4.79% under R2 and 5.54% under R3.
- **Other outcomes.** Lost units, emergency units, emergency units per short day and cost (350 per wasted unit and 700 per emergency unit, the data file's weights) all point the same way as waste. Against the standing order, no CI excludes zero; SARIMA, for example, had −15 lost units a year (−38 to +8). Against the weekday average, SARIMA and Chronos-Bolt had fewer lost units and lower cost, with CIs excluding zero.
- **Fixed shortage targets (pre-declared sensitivity).**
  - At 20 short days a year: SARIMA −0.82 (−1.60 to −0.04) and Chronos-Bolt −0.57 (−1.33 to +0.19) against the standing order.
  - At 50 short days a year: SARIMA −0.39 (−0.74 to −0.04).
  - GB and detrended GB were within about ±0.05 at both targets.
- **LASSO/RNN reference forecasts.** These could not be run under the calibrated Mon–Sat calendar (deviation D2). Under the v9 base configuration, RNN was −0.68 (−1.26 to −0.10) and LASSO +0.23 (CI includes zero).

## 5. Sensitivity analyses, Aachen (forecast minus standing order, R1, recorded short days)

| Scenario | GB | Detrended GB | SARIMA | Chronos-Bolt | SO waste |
|---|---|---|---|---|---|
| Main (calibrated) | +0.17 | +0.07 | −0.33 | −0.12 | 5.3% |
| v9 base configuration | +0.51 | **+1.16** | **−0.79** | **−0.75** | 11.5% |
| Calendar Tue–Sat (documented) | +0.99 | +1.22 | **−2.47** | **−2.07** | 14.5% |
| Calendar Mon–Fri | +1.29 | +1.26 | **−1.77** | −0.74 | 15.2% |
| Calendar Tue–Sun | +0.13 | −0.11 | −0.47 | −0.26 | 5.3% |
| Calendar every day | −0.01 | −0.35 | −0.37 | −0.23 | 4.3% |
| No shortfalls / 10% shortfalls | ≈ +0.05 to +0.09 | ≈ 0 | −0.49 / **−0.44** | −0.26 / −0.23 | 3.7–3.9% |
| Patient episodes (mean 2 units) | +0.10 | +0.11 | **−0.46** | −0.15 | 7.6% |
| No blood groups (pooled stock) | +0.03 | +0.15 | −0.12 | −0.05 | 0.7% |
| Shorter life on arrival (p3 0.1 → 1.0) | +0.19 → +0.50 | +0.12 → **+1.38** | −0.38 → −0.14 | −0.12 → +0.21 | 6.0% → 11.9% |

**Bold** marks a 95% CI that excludes zero (unadjusted, sensitivity only).

What this shows:

- SARIMA's point estimate is below the standing order's in every scenario.
- The gap is large only when the calendar includes a long weekend order (Tue–Sat or Mon–Fri). It is small with deliveries that cover 2–3 days at a time, which is the kind of calendar the calibration chose.
- Detrended GB gets clearly worse as shelf life on arrival shortens.
- With a cushion chosen in advance (2013–2018), every method's results swing too much from year to year to say anything (`41_cushion_in_advance_summary.csv`).

**Results that differ from v9, stated plainly as the plan requires.** In v9 (constant cushion, uncalibrated), SARIMA, Chronos-Bolt and GB were within about 0.1 points of the standing order. Re-run on the same v9 configuration with the order-sized cushion, SARIMA and Chronos-Bolt waste about 0.8 points less and detrended GB about 1.2 points more, each with a CI that excludes zero. The order-sized cushion also raises the standing order's own waste under Tue–Sat, from about 8.5% to 11.5% (exploratory observation E2). The ordering rule and the delivery calendar matter at least as much as the forecast.

## 6. Forecast accuracy (descriptive only; already known)

Average MAE for 2012–2018, in units:

| Forecast | 1-day | 2-day total | 3-day total | 4-day total |
|---|---|---|---|---|
| SARIMA | 3.75 | 5.58 | 7.18 | 8.65 |
| Chronos-Bolt | 3.82 | 5.68 | 7.32 | 8.88 |
| Detrended GB | 3.85 | 5.79 | 7.52 | 9.07 |
| Gradient boosting | 3.85 | 5.93 | 7.79 | 9.54 |
| Standing order | 4.07 | 6.40 | 8.54 | 10.53 |
| Weekday average | 4.17 | 6.12 | 7.87 | 9.45 |

The source file is `results/m10/42_descriptive_accuracy_mean_2012_2018.csv`.

## 7. Where everything is

- **Code** (all in `scripts/`):
  - `lib_m10.py`;
  - `37_m10_selftest.py`: tested on the synthetic series, with an exact match to the old simulator;
  - `38_m10_calibration.py`, `39_m10_validation.py`, `40_m10_run_comparisons.py`, `41_m10_stats.py` and `42_m10_charts_descriptive.py`;
  - for Stanford, `study2/scripts/10_m10_forecasts.py`, `10b_m10_chronos.py` and `11_m10_stanford_replication.py`.
- **Results.**
  - `results/m10/`, including `41_primary_H1.csv`, `41_primary_summary.json`, `41_secondary_*.csv`, `41_tradeoff_*.csv`, `41_sensitivity_vs_so.csv`, `41_bookkeeping.csv` and `41_residual_plots.png`.
  - `study2/results/s2m10/`, including `11_primary_stanford.csv`.
  - Earlier results were not touched.
- **Charts:** `charts/m10_calibration_validation.png`, `m10_primary_vs_standing_order.png`, `m10_stanford_vs_standing_order.png` and `m10_tradeoff_curves.png`.

## 8. Decisions needed from Liam before the 3,500-word Transfusion rewrite

1. **How to frame the failed calibration.** The plan requires the abstract to say it, and the primary result has to be described as conditional on it. The honest headline is probably: "a forecast advantage over a standing order was not demonstrated at either hospital, and the simulation could not be calibrated to the hospital's own record". Do you agree with leading on that?
2. **How much weight to give the calendar finding.** The size of the forecast advantage depends mostly on the delivery calendar, and the real Aachen calendar is uncertain. Should it be a main point of the discussion, or stay as a sensitivity result?
3. **File the OSF Update.** The deviations (D1–D7 in `paper/prereg_deviations.md`) need to be posted as an Update to your registration. Only you can do that, from your OSF account.
4. **Send the registration link or DOI** so the paper can cite it.
5. **Any exploratory follow-up?** For example, a labelled exploratory look at why the calibration fails. The plan allows this only if it is labelled exploratory. My suggestion is to **skip it** for this submission and say so.
6. **Journal fit.** A null result plus a failed calibration is honest but a harder sell for Transfusion. Do you still want Transfusion, or would you consider a methods-friendly or null-result-friendly transfusion journal?
7. **GitHub.** Should the new m10 code and results be pushed to your private repo? Nothing has been pushed.
