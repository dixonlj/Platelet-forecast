# Review 3: Study 2 pre-registration v3 (does the plan match the code?)

**Verdict: Close. The plan and code now match on every earlier item. Fix one wrong sentence about the `--nhsbt` lock (V1), then it is ready to post to OSF.**

- Reviewer: Research Reviewer (AI), third independent check, 18–19 Nov 2026, around midnight ET.
- I judged only from the files. I treated `changes_v2_to_v3.md` as claims and checked each one myself.
- I edited nothing except this file. Nothing was posted, sent or submitted.
- **Nothing was fitted to the NHSBT workbook.** I ran the synthetic test and the lock tests in a throwaway copy in `/tmp`, with no NHSBT file present, then deleted it.

---

## 1. Status of the earlier items

| Item | Status | Evidence (file + line) |
|---|---|---|
| **N1** The script was only building blocks | **Resolved** | `nhsbt_analysis.py`: `read_sheet` (lines 117–163) checks the sheet, columns, 115 months, no gaps and positive values. `to_per_day` (166–170). `run_forecasts` (36 origins; one fit per origin gives 1–3 months). `evaluate` (MAE with CI, secondary metrics, paired differences, HLN-DM). `apply_primary_rule` (Holm, verdict, 7-unit label). `run_pipeline` (418+) runs the primary analysis plus the COVID sensitivity for all 4 products, the Sep–Oct 2025 drop, the red-cell checks, the lag-2 check and the 2021-vs-2019 table, and writes every output listed in plan lines 178–191. My synthetic run produced all 8 run×product combinations and every scoring set. |
| **N2 / R1** Pairing by list position | **Resolved** | `inference.py` `align_by_target` (lines 42–70) joins on target month and reports dropped months. All NHSBT comparisons use `mae_diff_ci_keyed` / `dm_hln_keyed` (`nhsbt_analysis.py`, `evaluate`). The old positional helpers now refuse lists of different lengths (`_check_same_length`). My rerun gives −8.723 (paired by month), against −8.262 for the old method, exactly matching my v2 probe. |
| **R1** The bootstrap itself | **Resolved** | Circular blocks (`circular_block_indices`, `inference.py` 93–105). Block length 3 at one month, h+2 at horizon h (86–90). 10,000 resamples. Seed 20261118, set at every call. Percentile 95% CI (108–117). Differences are resampled as paired loss differentials on the same months. All of this matches plan lines 157–162. |
| **R3** Holm never called | **Resolved** | `apply_primary_rule` (`nhsbt_analysis.py`) stops with an error unless there are exactly 3 confirmatory rows (platelets, primary run, all months, 1 month ahead; ETS/SARIMA/regression vs naive). It feeds their HLN lag-0 DM p-values (non-computable counts as 1) into `holm_adjust`, then into `primary_verdict`, which needs Holm rejection **and** a CI excluding zero. The arithmetic checks out: the synthetic raw p-values 0.028 / 0.037 / 0.058 give Holm p 0.084 for all three, so "couldn't tell them apart". |
| **R4** SARIMA fallback | **Resolved** | See section 2. Plan line 129 and code (`warning_is_failure`, `fit_*`) list the same six criteria. |
| **R6 / N3** COVID regression time | **Resolved** | See section 2. |
| **N4** Flint citation | **Resolved** | README line 47 now gives Flint AW, McQuilten ZK, Irwin G, Rushford K, Haysom HE, Wood EM, *Transfus Med Rev* 2020;34(1):42–50, doi:10.1016/j.tmrv.2019.08.006, PMID 31685352. The quote is "frequently reported at 10% to 20%". All of this matches what I read on PubMed and Crossref in review 2. A correction note is at line 104. |

**Spot-checks of the claimed Recommended and Optional fixes (all real):**
- **N5–N7:** warnings are logged; the check now uses `converged`; the six failure criteria match.
- **N8:** the 7 units/day rule is wired in (see section 2).
- **N9:** line 19 now says only the one-month horizon is confirmatory.
- **N10:** the lag-2 check exists (`lag2_check`, output `dm_lag2_check.csv`).
- **N11:** the bootstrap is circular. A built-in test confirms every month is drawn equally often.
- **N12:** fallbacks are counted per origin (36 each). The synthetic shares (0 in the primary run, 0.25–0.31 in the COVID sensitivity) reproduced exactly.
- **N13:** 62 checks (see section 4).
- **N14:** the line is rewritten.
- **O-a:** Bartlett weights (`inference.py` 160–163).
- **O-b:** Holm-adjusted p-values are reported.
- **O-c, O-d, O-e:** all in the plan text.
- The v2 plan and the archived v2 code are unchanged; their hashes still match draft 2.

## 2. The specific choices you asked me to scrutinise

**"January 2022 stays at position 69."**
- Correct, because counting starts at **0 for April 2016**, which plan line 127 says explicitly. April to December 2016 is positions 0–8, so January 2022 = (2022−2016)×12 + (1−4) = 69. I recomputed it: 69.
- The code uses each month's list index, which starts at 0 (`keep` indices passed to `calendar_regression_forecast`). It doesn't renumber after dropping COVID rows.
- The test regression with no noise recovers the true values exactly, and the old renumbering demonstrably doesn't.

**SARIMA fallback, six criteria.**
- Plan line 129, (a)–(f): exception; ConvergenceWarning; "converge" in the message; "failed to" + "optim"; non-finite forecast; `mle_retvals['converged']` is False.
- The code has exactly these: `warning_is_failure` covers (b)–(d); the `fit_*` functions cover (a), (e) and (f).
- Warnings are captured with `simplefilter("always")`, used to decide failure, and saved. In the synthetic log there are 74 ConvergenceWarnings and 74 `converged=False` entries (failures), plus 24 EstimationWarnings logged but correctly *not* counted as failures.
- `converged` is a key statsmodels 0.15.0 really sets. In review 2 I checked the keys on this box: converged, fcalls, fopt, gopt, iterations, warnflag.
- The fallback has its constant (`trend='c'`). A built-in test forces the primary to fail and confirms the fallback runs with the constant.

**7 units/day.**
- Plan line 155 says honestly that it is a judgement call, with no planning standard behind it and no power calculation.
- It is applied only after the verdict (`practical_label`). It never creates a claim on its own: no verdict means "no claim".
- It is symmetric for "better" and "worse", and it checks the end of the interval nearest zero.
- Plan line 170 and the code agree, and all branches are tested.

**Circular bootstrap.**
- Block lengths 3 / 4 / 5, 10,000 resamples, seed 20261118, percentile CI, paired by target month. All match the plan (lines 157–162).

**The `--nhsbt` lock (tested without fitting anything).**
- No URL: refuses, exit 1, the snapshot is not opened.
- `https://example.com/x`: refuses, exit 1.
- `https://osf.io/fake`, with a dummy file of the wrong hash in place: stops at the hash check ("does not match … Stopping"), exit 1. Nothing was fitted.
- **But `https://osf.io/fake` passes the URL check.** Any text starting with `https://osf.io/` is accepted (`_osf_url_ok`). The code never checks that the registration exists, is public, or was posted first. With the real snapshot in place, the full model run would start.
- So the lock is a speed bump, not a lock. Any lock in your own code can be removed by editing the code anyway. **The real protection is the OSF timestamp**: the registration must be dated before `run_at` in `run_manifest.json`.
- Plan line 119 says the run "refuses to start unless it is given the URL of the posted OSF registration". That is not true as written. See V1.

**End to end.** Yes. See N1 in the table above. One small gap is in V3.

## 3. Hash check

| File | Hash in the plan | Hash I computed | Match? |
|---|---|---|---|
| `nhsbt_analysis.py` | `d56b1c00…741359a` (v3 line 119) | `d56b1c00c33cbfd3ae791cc31f4aab95f6b678b34abecf6d76b0ce386741359a` | **Yes** |
| `inference.py` | `0e5248d4…0bf64` (v3 line 119) | `0e5248d473a0bb216f1d1e20d7536f0c3401b4e04e11bb3033f66a0528e0bf64` | **Yes** |
| NHSBT snapshot | `f0e3fbc5…e696` (v3 line 43; also in the code, line 53) | `f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696` | **Yes** |
| `archive_v2_code/inference.py` | `6d55e1b1…cb9416` (v2 line 119) | the same | **Yes** |
| `archive_v2_code/nhsbt_analysis.py` | `0f429756…68a30d` (v2 line 119) | the same | **Yes** |
| Software (v3 line 119) | Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1, openpyxl 3.1.5 | the same on this box | **Yes** |

## 4. Synthetic tests

- I reran `--synthetic-test` in a `/tmp` copy. Result: **62 passed, 0 failed**.
- My log is identical to the author's `SYNTHETIC_test_log.txt`. My `accuracy`, `comparisons_vs_naive`, `forecasts_long` and `fit_summary` CSVs are byte-identical to the author's. So the run is reproducible and the author's outputs weren't touched up by hand.
- **Are the tests meaningful? Mostly yes.** They check real behaviour, not just "it ran":
  - the loader refuses a sheet with a missing month;
  - leap-year February is divided by 29;
  - target counts are 36/35/34 with the correct dates;
  - dropping one forecast pairs correctly and matches a hand calculation;
  - Nov and Dec 2022 use 2019 values in the sensitivity;
  - the regression with no noise is exact;
  - the red-cell shift switches on in July and not June, at exactly 15 origins;
  - Holm step-down and its adjusted p-values are correct;
  - every verdict branch works;
  - a forced SARIMA failure falls back, and `converged=False` and ConvergenceWarning both count as failures;
  - the bootstrap draws every month equally often and is reproducible.
- Gaps are in O4.

## 5. Any sign of an NHSBT fit? None.

- `study2/results/nhsbt_confirmatory/` does not exist.
- There are no `__pycache__` folders and no NHSBT outputs anywhere.
- The snapshot's modified time (9:43 PM ET) and hash are unchanged.
- Every output file present is labelled SYNTHETIC and lists the made-up workbook as its input.
- The plan (line 3) and the changes log say a `--check-structure` pass read the real snapshot. That mode reads values to validate them but prints only the sheet name, columns, counts and dates. No output from it was saved, so I can't confirm what it printed (O5). Reading values for checks is not modelling.

## 6. Graded new and remaining issues

### Required

**V1. The plan overstates the `--nhsbt` lock.**
- *Where:* plan line 119 ("refuses to start unless it is given the URL of the posted OSF registration"); the same claim is in the `nhsbt_analysis.py` docstring (lines 23–25) and `changes_v2_to_v3.md` line 21.
- *Problem:* I showed that `https://osf.io/fake` is accepted. A pre-registration shouldn't state a safeguard that doesn't exist.
- *Fix (wording, in the plan):* "The confirmatory run requires an `https://osf.io/` address, which it records in the run manifest, and it checks the snapshot hash. It cannot confirm that the registration exists or was posted first; the safeguard is that the OSF registration timestamp must precede the run time in `run_manifest.json`."
- If you change the code instead, re-hash both scripts and update line 119.

### Recommended

**V2. Make the lock a little stronger.**
- *Where:* `run_nhsbt` in `nhsbt_analysis.py`.
- *Problem:* the run records the scripts' own hashes but doesn't compare them with the pre-registered ones before starting.
- *Fix:* before fitting, check that both scripts' SHA-256 match the values in the plan, and refuse if not. Optionally, ask the user to type the registration date and save it. This doesn't make the lock unbreakable, because nothing in your own code can be; it makes a quiet edited rerun visible.

**V3. ETS dropping origins in the COVID sensitivity has no "unreliable" rule.**
- *Where:* plan line 146 (rule exists for SARIMA only) and `summarise_fits` (flags SARIMA only).
- *Evidence:* on the made-up data, the state-space ETS was **omitted at 25 of 36 red-cell origins** (and 4 of 36 for cryo) in the COVID sensitivity. Those comparisons rest on only 11 months, with no warning label.
- *Fix:* apply the same rule to omitted origins for any method: if more than half are omitted, label that product's result unreliable. Show `n_paired` next to every sensitivity result.

**V4. The Brazil README still implies it runs with the current code.**
- *Where:* `brazil_exploratory/README.md` line 6, "(uses `study2/prereg/inference.py`)"; `aggregate_and_forecast.py` line 31 imports from `prereg/`, which is now the v3 code.
- *Problem:* the README's own line 105 rightly says the numbers came from the v2 code. But if anyone runs the script now, it imports v3:
  - its warning summary (lines 327–328) reads the new logs in the old tuple format and would crash;
  - the bootstrap is now circular, so any numbers would differ.
- *Fix:* change line 6 to "numbers produced with `prereg/archive_v2_code/inference.py` (v2); not reproducible with the current `inference.py`". Then either point the import at the archive folder, or update the script and rerun it (exploratory only).
- This doesn't block posting the OSF plan.

### Optional

- **O1.** Name the CI method ("percentile") in plan lines 157–162. The code uses percentile.
- **O2.** `accuracy.csv` computes each method's MAE on its own months. If ETS drops months, its MAE and naive's cover different months. The comparisons table is correctly paired; add a note to the accuracy table or a paired-months MAE.
- **O3.** `changes_v1_to_v2.md` was edited after review 2 (11:53 PM ET), with clearly marked corrections. That's fine, but keep old records add-only from now on.
- **O4.** A few branches have no test: an ETS failure omitting all horizons at one origin; the "worse, practically meaningful" label; and the hash-mismatch stop (I tested that by hand; it works).
- **O5.** Save the `--check-structure` console output to a file, so "printed no values" can be checked later.

**Count: 1 Required, 3 Recommended, 5 Optional.**

## 7. What improved (briefly, honestly)

- This is the first version where the plan and the code genuinely match.
- The analysis runs end to end, it's reproducible to the byte on made-up data, and the tests check real behaviour.
- Every fix I asked for in review 2 is real, not just claimed.
- The 7 units/day threshold is now an honest judgement call that is actually used.
- The Flint citation is right, and the error was openly corrected.

## 8. Is it ready to post to OSF?

**Yes, after V1.** That is a one-sentence wording fix in the plan; if only the plan text changes, the code hashes stay valid. V2–V4 are worth doing but don't block posting. If any code changes (for example V2), re-hash both scripts, update line 119, and rerun `--synthetic-test` before posting.

Then, in this order:
1. Liam reads it.
2. Liam posts it on OSF himself.
3. Only after that, run `--nhsbt` with the real registration link.

Don't run anything on NHSBT before the OSF timestamp exists.

---

*This is an AI review. It does not replace review by a human statistician (especially the bootstrap, DM and Holm details), a transfusion-medicine specialist, and someone who knows data licensing (NHSBT's missing licence and the CC BY-ND chart question).*
