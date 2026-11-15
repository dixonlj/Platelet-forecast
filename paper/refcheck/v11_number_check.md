# v11 number check

Draft: `paper/draft_v11.src.md`. Run by `scripts/45_check_v11_numbers.py`.

**Part A: 64 of 64 checks pass.** Each recomputes a number from the results files and confirms the exact text is in the draft.

| # | Check | Text looked for | Source | Pass |
|---|---|---|---|---|
| 1 | validation waste sim vs rec (abstract) | waste 5.22% simulated against 9.74% recorded | `results/m10/39_validation_result.json` | yes |
| 2 | emergency per short day (abstract) | 5.00 against 8.82 emergency units per shortage day | `results/m10/39_validation_result.json` | yes |
| 3 | TVD (abstract) | weekday-pattern distance of 0.226 (limit 0.20) | `results/m10/39_validation_result.json` | yes |
| 4 | all three checks failed | computed | `results/m10/39_validation_result.json` | yes |
| 5 | calibration fit waste | it gave 7.70% waste against 8.25% recorded | `results/m10/38_calibration_choice.json` | yes |
| 6 | calibration fit emergency | 4.00 against 6.53 emergency units per short day | `results/m10/38_calibration_choice.json` | yes |
| 7 | calibration fit TVD | a TVD of 0.195 | `results/m10/38_calibration_choice.json` | yes |
| 8 | chosen setting Mon-Sat, all 4-day life, lag +1, unit demand, heavy shortfalls | computed | `results/m10/38_calibration_choice.json` | yes |
| 9 | 2,700 combinations; none reached 4.5 | No combination of the 2,700 reached 4.5 emergency units per short day | `results/m10/38_calibration_grid.csv` | yes |
| 10 | SO waste 5.30 (abstract) | (standing order waste 5.30%) | `results/m10/41_primary_H1.csv` | yes |
| 11 | SO waste 5.30 (results) | The standing order wasted 5.30% on average | `results/m10/41_primary_H1.csv` | yes |
| 12 | abstract four estimates | seasonal model −0.33 points (95% confidence interval −0.88 to +0.22), pretrained −0.12, detrended boosting +0.07, boosting +0.17 | `results/m10/41_primary_H1.csv` | yes |
| 13 | SARIMA primary full | a difference of −0.33 points (95% CI −0.88 to +0.22; Holm-adjusted p = 0.75; lower in 5 of 7 years) | `results/m10/41_primary_H1.csv` | yes |
| 14 | CB/dGB/GB primary | Chronos-Bolt differed by −0.12 points (−0.74 to +0.50), detrended gradient boosting by +0.07 (−0.61 to +0.75) and gradient boosting by +0.17 (−0.35 to +0.69) | `results/m10/41_primary_H1.csv` | yes |
| 15 | other Holm p = 1.00 | their Holm-adjusted p-values were 1.00 | `results/m10/41_primary_H1.csv` | yes |
| 16 | none equivalent (90% CI beyond ±0.5), none Holm-significant | computed | `results/m10/41_primary_H1.csv` | yes |
| 17 | compatible range 0.9 less to 0.7 more | about 0.9 points less waste to 0.7 points more | `results/m10/41_primary_H1.csv` | yes |
| 18 | lag-1 residual correlation range | was 0.14 to 0.29, below the preset 0.3 | `results/m10/41_primary_H1.csv` | yes |
| 19 | sign/Wilcoxon p >= 0.29 | p ≥ 0.29 for all four | `results/m10/41_primary_H1.csv` | yes |
| 20 | SARIMA years lower 5 (via primary sentence) | lower in 5 of 7 years | `results/m10/41_primary_H1.csv` | yes |
| 21 | Stanford SO window waste | wasting 2.86% over the window | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 22 | Stanford range 1.40-2.29 (abstract) | by 1.40 to 2.29 points | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 23 | Stanford Holm min 0.10 (abstract) | (Holm-adjusted p ≥ 0.10) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 24 | Stanford gb_noclin | gradient boosting by 1.40 points (95% CI −3.58 to +0.75) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 25 | Stanford dgb | detrended gradient boosting by 2.18 (−4.31 to +0.04) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 26 | Stanford sarima | SARIMA by 2.29 (−4.52 to −0.12) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 27 | Stanford cb | Chronos-Bolt by 2.06 (−4.15 to +0.02) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 28 | Stanford SARIMA p and Holm | (p = 0.026; Holm-adjusted p = 0.10) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 29 | Stanford other Holm range | Holm-adjusted p-values for the others were 0.16 to 0.22 | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 30 | only SARIMA's CI excludes zero | computed | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 31 | Stanford MMD 0.17 in caption | (0.17 points) | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 32 | Stanford 1.4 to 2.3 (discussion) | by 1.4 to 2.3 points | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 33 | Stanford WA4 1.08% | wasted only 1.08% | `study2/results/s2m10/11_matched_levels.csv` | yes |
| 34 | SARIMA vs WA4 | SARIMA wasted 0.54 points less (95% CI −1.03 to −0.05; lower in 6 of 7 years) | `results/m10/41_secondary_waste.csv` | yes |
| 35 | trade-off SARIMA | SARIMA's mean gap against the standing order was −0.41 points (−0.85 to +0.02) | `results/m10/41_tradeoff_summary.csv` | yes |
| 36 | R2 within ±0.3 | every gap was within ±0.3 points with CIs including zero | `results/m10/41_secondary_waste.csv` | yes |
| 37 | R3 SARIMA | SARIMA was −0.66 points (−1.11 to −0.20) | `results/m10/41_secondary_waste.csv` | yes |
| 38 | R3 SARIMA (discussion) | a larger gap (−0.66 points) | `results/m10/41_secondary_waste.csv` | yes |
| 39 | SARIMA lost units | 15 fewer lost units a year (95% CI 38 fewer to 8 more) | `results/m10/41_secondary_other_outcomes.csv` | yes |
| 40 | v9 base SARIMA/CB/dGB | SARIMA (−0.79) and Chronos-Bolt (−0.75) wasted less than the standing order and detrended gradient boosting wasted more (+1.16) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 41 | Tue-Sat SO waste + SARIMA | the standing order wasted 14.5% and SARIMA wasted 2.47 points less (95% CI −3.52 to −1.42) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 42 | Mon-Fri SARIMA | SARIMA wasted 1.77 points less (−3.26 to −0.28) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 43 | accuracy | (3.75 units at 1 day and 8.65 for 4-day totals, against 4.07 and 10.53 for the standing order | `results/m10/42_descriptive_accuracy_mean_2012_2018.csv` | yes |
| 44 | Aachen days | (4,018 days, no missing dates) | `data/public/UKA_Aachen_daily_platelets_2008-2018.csv` | yes |
| 45 | Aachen mean use | Mean use was 11.50 units a day | `data/public/UKA_Aachen_daily_platelets_2008-2018.csv` | yes |
| 46 | Aachen waste 10.1% | wasted 10.1% of platelet units over 2008–2018 | `data/public/UKA_Aachen_daily_platelets_2008-2018.csv` | yes |
| 47 | Aachen purchases 6.5% | bought 6.5% as emergency purchases | `data/public/UKA_Aachen_daily_platelets_2008-2018.csv` | yes |
| 48 | recorded short days 2012-2018 | (40, 31, 21, 38, 35, 42 and 31 in 2012–2018) | `results/m10/39_validation_per_year.csv` | yes |
| 49 | Tue-Sat SARIMA (abstract, R5) | the seasonal model wasted 2.47 points less (−3.52 to −1.42) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 50 | Tue-Sat SARIMA (conclusion, R5) | SARIMA wasted 2.47 points less (95% CI −3.52 to −1.42) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 51 | Tue-Sat Chronos-Bolt (3.5) | Chronos-Bolt wasted 2.07 points less (−3.02 to −1.12) | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 52 | Tue-Sat: SARIMA and CB both about 2 points less, CIs below zero ('about 2 points less') | computed | `results/m10/41_sensitivity_vs_so.csv` | yes |
| 53 | Thursday waste share sim vs recorded (3.1) | (0.0% of waste, against 13.2% recorded) | `results/m10/39_validation_result.json` | yes |
| 54 | no other of 2,700 within 5% of best loss | no other of the 2,700 combinations came within 5% of the chosen one's fit | `results/m10/38_calibration_grid.csv` | yes |
| 55 | Stanford t-interval dgb (R6) | detrended gradient boosting −3.96 to −0.40 | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 56 | Stanford t-interval sarima (R6) | SARIMA −4.14 to −0.43 | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 57 | Stanford t-interval cb (R6) | Chronos-Bolt −3.76 to −0.36 | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 58 | Stanford t-interval gb_noclin (R6) | gradient boosting −3.32 to +0.52 | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 59 | t-intervals exclude zero for three of four | excluded zero for three of the four forecasts | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 60 | Stanford relative 45% to 75% (R6) | 45% to 75% less waste than the standing order | `study2/results/s2m10/11_primary_stanford.csv` | yes |
| 61 | plan/manifest time stamps and count | the SHA-256 manifest of 35 input files is time-stamped 03:41 and the final plan 04:04 | `file mtimes of paper/osf_prereg_input_hashes.txt and paper/osf_preregistration_final.md` | yes |
| 62 | plan finalised before calibration report (04:41) | computed | `file mtimes` | yes |
| 63 | Table from results is current: validation_v10.md | regenerated and compared | `scripts/43_tables_v10.py` | yes |
| 64 | Table from results is current: secondary_v10.md | regenerated and compared | `scripts/43_tables_v10.py` | yes |

**Part B: 317 numeric tokens in the abstract, body, captions and Table 3; 0 not tied to a check or a listed design constant.**

Uncovered tokens: none

Design constants and cited facts (not results), with their source:

- `5`: 5 to 7 days storage [coi2024]; 5 of 509 days Stanford target (prereg 2.5)
- `7`: 7 days storage; 7 test years; df=6 (7−1)
- `10.5`: Guan et al. reported 10.5% to 3.2% [guan2017]
- `3.2`: Guan et al. [guan2017]
- `10`: outdating 10% to 20% [flint2020]
- `20`: outdating 10–20% [flint2020]; 20 short days (prereg 4.1)
- `2008`: data start
- `2018`: data end
- `2012`: test years
- `2009`: calibration years
- `2011`: calibration years
- `2014`: Stanford window
- `2015`: Stanford window
- `2022`: Aachen file public since 2022 [schilling2022]
- `2026`: registration date
- `14`: registration date (14 November 2026); AI use 13–14 November 2026
- `13`: AI use 13–14 November 2026
- `37`: scripts 37–42 (analysis code file names)
- `03:41`: input manifest time stamp (file mtime of paper/osf_prereg_input_hashes.txt)
- `04:04`: final plan time stamp (file mtime of paper/osf_preregistration_final.md)
- `04:30`: analysis run window (prereg_deviations.md)
- `05:10`: analysis run window
- `0.1`: exploratory-study gap (prereg 3.6)
- `1`: RQ1; one-week warm-up; 1 to 4 days
- `4`: 1 to 4 days ahead; 4-day order; four presets
- `512`: Chronos context (prereg 2.3.1)
- `28`: past-28-day mean (prereg 2.3.1)
- `6`: k sweep 0 to 6; df 6; ≤6 display items; about 6 bootstrap resampling units (18 blocks / runs of 3)
- `0`: k sweep 0 to 6
- `0.25`: k step (prereg 4.1)
- `2`: two-day lead; 2-, 3- or 4-day orders
- `3`: 3 usable days; 3 tables
- `1.5`: A1 rule (prereg 2.4.5)
- `25`: A2 rule ±25%; 25% shortfall days; 25 short days Stanford sensitivity
- `0.20`: A3 rule (prereg 2.4.5)
- `50`: 50 short days (prereg 4.1)
- `0.5`: MMD (prereg 4.6)
- `0.05`: alpha (prereg 4.5)
- `90`: 90% CI equivalence rule (prereg 4.7)
- `95`: 95% CI
- `18`: 18 Stanford blocks (prereg 4.4)
- `509`: Stanford scored days (prereg 2.5)
- `35`: Stanford ~35 units a day (prereg 2.5); 35 input fingerprints (osf_prereg_input_hashes.txt)
- `8`: 8 January scoring start
- `31`: 31 May 2015; recorded short days
- `30`: 30 runs; 30–80% filled
- `80`: 30–80% filled (calibration choice)
- `0.3`: lag-1 trigger (prereg 4.11); ±0.3 R2 check
- `2,700`: grid size
- `15`: 15 life mixes
- `12`: twelve blocks
- `22`: 22% to 60% [harm2018; ning2023]
- `60`: [harm2018; ning2023]
- `8.25`: recorded calibration target (prereg 2.4.2)
- `6.53`: recorded calibration target (prereg 2.4.2)
- `4.5`: grid max check
- `40`: recorded short days
- `21`: recorded short days
- `38`: recorded short days
- `42`: recorded short days
- `256`: part of the name SHA-256
- `2013`: D3 years 2013–2018
- `2010`: D3 reason
- `27`: script 27 (D5)
- `0.17`: Stanford MMD
