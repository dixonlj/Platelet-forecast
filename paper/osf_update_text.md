# Text to add to the OSF registration (for Liam to paste himself)

How to use: the registration has not been submitted yet. Either (a) paste the text between the lines into the registration itself before submitting (for example at the end of the "Other" section, or in the deviations/explanation box), or (b) if it is already submitted, file it as an Update or note on the registration straight away. Plain text only; nothing here has been filed. Edit freely.

----------------------------------------------------------------

Note on timing and deviations from the analysis plan

Timing (please read first). This plan was finalised, and SHA-256 fingerprints of its 35 inputs were recorded, before the confirmatory analyses were run. On the analysis computer (US Eastern time, 14 November 2026): input manifest osf_prereg_input_hashes.txt time-stamped 03:41; final plan osf_preregistration_final.md time-stamped 04:04 (SHA-256 58029266d1b75ccdbd786cc6c6c972e24b47f73615f871db286c5f13cba7856a); analyses run 04:30 to 05:10. The plan was registered on OSF later the same day, AFTER those analyses were run, because an unsubmitted OSF draft was mistaken for a submitted registration. This registration therefore cannot by itself show that the plan came before the analyses; that rests on the time stamps and fingerprints above. The plan text registered here is unchanged from the 04:04 version. This is listed as D8 below.

Analyses run: 14 November 2026, 04:30 to 05:10 US Eastern time. D1 to D7 were decided before the primary results were seen (D4 and D5 before any Stanford simulation). None of the eight deviations changes the primary comparator (prior-year standing order), outcome (waste % at each year's recorded short days), ordering rule (R1, cushion sized to each order's days), mixed model, or Holm correction. The primary result was "not demonstrated" for all four forecasts.

D1. Order of work (Section 2.2).
Changed: the Aachen primary, secondary and sensitivity simulations ran in one batch, then Stanford. One script computed all four primary comparisons together.
Why: simpler. No choice depended on sensitivity outputs, and the primary specification was fixed first.
Effect on main test: none.

D2. Authors' LASSO/RNN reference forecasts (Section 5.1, item 6).
Changed: these could not be run under the calibrated Mon–Sat calendar. It needs 3-day order totals, and only 2- and 4-day totals were published. They were run instead in scenarios using only 2- and 4-day orders (v9 base, Tue–Sat, daily), labelled as a substitute.
Why: the data do not allow it ("closest feasible version", Section 6).
Effect on main test: none. These are reference models, not part of H1a–d.

D3. Cushion chosen in advance (sensitivity 5.2.6).
Changed: run for 2013–2018 only (6 years). For each forecast and year, k was set to the mean over 30 runs of the previous year's matched k, and applied by interpolation on the saved k-grid curves, without a new simulation.
Why: 2012 would need 2010 forecasts for SARIMA and Chronos-Bolt, which do not exist, and making them would mean new model fits (not allowed by Section 7). One k per forecast and year mirrors how a hospital would set one cushion; the plan did not say whether k is per run or pooled.
Effect on main test: none. Sensitivity only.

D4. Stanford equivalence label (Sections 4.4 and 4.7).
Changed: the plan did not define a Stanford "practically equivalent" interval. The 90% moving-block bootstrap interval against ±6% of the standing order's waste was used, by analogy with the Aachen rule.
Why: the plan was silent.
Effect on main test: none. No Stanford comparison met the rule.

D5. Stanford detrended gradient boosting features (Section 2.5).
Changed: script 27's features were used, but with US-California holidays instead of German (NRW) holidays. Forecasts were clipped at 0, as for the Stanford GB in S2-1.
Why: German holidays make no sense for a US hospital. Clipping matches the named S2-1 GB settings.
Effect on main test: none on Aachen. Stanford H1b used these forecasts, and its verdict was "not demonstrated" (consistent null).

D6. Life-on-arrival sweep (sensitivity 5.2.3).
Changed: p3 = 0 was not run separately because it equals the calibrated main scenario. The grid values 0.30 and 0.43 were run as named.
Why: it would have duplicated the main scenario.
Effect on main test: none.

D7. Optional NHSBT national-level check (Section 5.3).
Changed: not done. No NHSBT issues data were downloaded.
Why: optional, and nothing needed it.
Effect on main test: none.

D8. Timing of registration (Section 2.2 and the plan's front matter: register before running the analyses).
Changed: the plan was finalised and its inputs fingerprinted before the analyses, but registered on OSF only after them (see "Timing" above).
Why: an unsubmitted OSF draft was mistaken for a submitted registration.
Effect on main test: none on the analyses themselves, which followed the 04:04 plan. It weakens the evidence that the plan came first, and the paper says so as a limitation.

Also reported, as the plan requires: the calibrated simulation failed all three validation criteria. Waste was 5.22% simulated vs 9.74% recorded; emergency units per short day were 5.00 vs 8.82; the weekday-pattern TVD was 0.226 (limit 0.20). All primary results are therefore reported as conditional on a simulation that failed validation, with the v9 base configuration alongside as a sensitivity analysis. No further calibration rounds were run.

----------------------------------------------------------------

Summary for Liam: 8 deviations. D1 to D7 are small and were decided before the primary results; D8 is that the plan was registered after the analyses, not before. None changes the primary test or its answer ("not demonstrated" for all four forecasts). The calibration failure is not a deviation, because the plan said what to do if it failed. It is still stated so that readers of the registration see it. Please do not edit the plan text itself before submitting, other than adding this note, so it still matches the 04:04 fingerprint.
