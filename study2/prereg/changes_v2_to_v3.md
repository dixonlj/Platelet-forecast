# Changes from draft 2 to draft 3 (Study 2 pre-registration)

18 November 2026, late evening (America/New_York). Made in response to Research Reviewer's second review, `review_prereg_v2.md` (not edited). Draft 2 (`osf_prereg_study2_draft_v2.md`) is unchanged. The v2 code is kept, unchanged, in `archive_v2_code/` so the draft-2 hashes can still be checked.

**Nothing was fitted to, forecast from, or scored on the NHSBT workbook.** The only contact with the snapshot was a structure-only check (`--check-structure`): hash, sheet name, column names, 115 rows, April 2016 to October 2025, no gaps. It printed no values. Nothing was posted, published, committed or pushed.

## New hashes (draft 3, line 119)

| File | SHA-256 |
|---|---|
| `nhsbt_analysis.py` | `d56b1c00c33cbfd3ae791cc31f4aab95f6b678b34abecf6d76b0ce386741359a` |
| `inference.py` | `0e5248d473a0bb216f1d1e20d7536f0c3401b4e04e11bb3033f66a0528e0bf64` |
| NHSBT snapshot (unchanged) | `f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696` |

## Item-by-item

### Required (new)

| Item | Fix | Where |
|---|---|---|
| **N1** Script was only building blocks | `nhsbt_analysis.py` is now the whole analysis: `read_sheet` (checks sheet, columns, 115 months, no gaps, positive numbers) → `to_per_day` → `run_forecasts` (naive, ETS, SARIMA, regression, plus red-cell shift regression; 36 origins; one fit per origin gives h = 1–3) → `evaluate` (MAE + CI, secondary metrics, paired differences, HLN-DM) → `apply_primary_rule` (Holm on exactly the 3 one-month platelet tests, then `primary_verdict` and `practical_label`) → COVID sensitivity (all 4 products), Sep–Oct 2025 drop, red-cell start-April-2024 and before/from split, seasonal naive 2021 vs 2019 table, descriptive lag-2 DM check → output tables, warning log, manifest. `--synthetic-test` runs this whole pipeline on a made-up workbook in the same layout, then 62 checks. `--nhsbt` stays locked: it needs the posted `https://osf.io/` URL and re-checks the snapshot hash. | `nhsbt_analysis.py`; plan line 119 and new **Outputs** section |
| **N2** Pairing by list position | Every forecast is stored as `{target_month: value}`. `inference.align_by_target` joins two methods by month and reports which months were dropped. All bootstrap and DM calls on NHSBT go through `mae_diff_ci_keyed` / `dm_hln_keyed`. The old positional helpers (still used by the Brazil script) now refuse lists of different lengths instead of truncating. Test: dropping one ETS forecast gives 35 month-matched pairs, 1 dropped month reported, and a difference equal to the hand calculation (−8.723 on the made-up data; the v2 position-based code would have given −8.262, matching the reviewer's probe). | `inference.py`; plan line 160 |
| **N3** COVID regression renumbered time | **Code changed to match the plan.** The regression's time variable is now each month's real position in the series (0 = April 2016) in training and forecasting; dropping COVID rows no longer renumbers it. Plan line 144 kept in meaning and made explicit (example: January 2022 stays at position 69). Test: on a noise-free trend-plus-season series the COVID-dropped regression is exact; the v2 renumbering is shown not to be. | `calendar_regression_forecast`; plan lines 127, 144 |
| **N4** Flint citation | Checked against Crossref and PubMed (PMID 31685352) on 18 Nov 2026: Flint AW, McQuilten ZK, Irwin G, Rushford K, Haysom HE, Wood EM. *Transfus Med Rev* 2020;34(1):42–50, doi:10.1016/j.tmrv.2019.08.006. Quote now matches the abstract: "frequently reported at 10% to 20%". One more detail fixed: the abstract speaks of platelet outdating reported in published studies, not specifically "hospital outdate rates", so the README wording was changed. A correction note was added to the README and to `changes_v1_to_v2.md`. | `brazil_exploratory/README.md` line 47 and new end note; `changes_v1_to_v2.md` lines 156, 167 |

### Partly resolved v1 items

| Item | Fix |
|---|---|
| **R1** Bootstrap pairing | Fixed as N2; bootstrap is now circular (N11). |
| **R3** Holm never called | `apply_primary_rule` calls `holm_adjust` and `primary_verdict` on exactly three rows and raises an error if there are not exactly three. Synthetic run confirms it. |
| **R4** SARIMA fallback | (a) warnings and failures from every fit (ETS, state-space ETS, SARIMA primary and fallback) are returned and written to `fit_warning_log.csv` with run, product, method, origin and spec; (b) the check is now `mle_retvals['converged'] is False`, also applied to the state-space ETS; (c) the "failed to" + "optim" criterion was kept and **added to the plan**, so plan and code list the same six criteria, (a)–(f). |
| **R6** COVID regression | Fixed as N3. |

### Recommended

| Item | Fix |
|---|---|
| **N5** Save warning logs | Done (see R4). The state-space ETS now returns its warnings too. |
| **N6** Dead `success` check | Done (see R4); plan line 129 corrected. |
| **N7** Criteria mismatch | Done (see R4). |
| **N8** 7 units/day unused | **Wired into the decision rule.** New `practical_label`: "practically meaningful" only if declared better/worse **and** \|diff\| ≥ 7 **and** the whole interval is ≥ 7 from zero; "may be smaller than what matters" if the point estimate is ≥ 7 but the interval includes smaller values; "below the smallest meaningful difference" otherwise. Plan now calls 7 a judgement call with no planning-standard source, and says "may not be able to" detect it (no power calculation). |
| **N9** Research question | Line 19 now says one month ahead is the only confirmatory horizon; 2 and 3 months are descriptive. Also "at most one" regression → "one" regression. |
| **N10** Lag 0 vs runs of errors | Plan line 164 now says the bootstrap-interval requirement is the safeguard. Descriptive lag-2 check added (`dm_lag2_check.csv`). |
| **N11** Non-circular bootstrap | Switched to a **circular** moving-block bootstrap (`circular_block_indices`, vectorised). Test: with n = 10 and blocks of 5, every month is drawn equally often (within 0.5 percentage points). Brazil README now warns its 2–3 month CIs rest on very few distinct resamples (8 and 6 block starts). |
| **N12** SARIMA fallback share | ETS and SARIMA are fitted once per origin, so fallbacks are counted per origin (36 per run and product). Fallback share reported; a product's SARIMA result is labelled unreliable if more than half its origins fell back (pre-stated in the COVID section). On the made-up data the COVID-sensitivity shares were 0.25–0.31 per product (0 in the primary run). |
| **N13** Weak synthetic test | 62 checks now, covering: loader (round trip; refuses a gap), units per day (leap Feb), target counts 36/35/34 and dates, every output file, SYNTHETIC labelling, Holm on exactly 3 rows, all other rows descriptive, all runs/products/scoring sets, Sep–Oct drop gives 34 targets ending Aug 2025, red-cell shift both ways, pairing after a dropped forecast, 2019 substitution (Nov/Dec 2022) and Jan 2022 kept, real time index, red-cell shift switch (June vs July 2024; exactly 15 origins), Holm step-down and adjusted p-values, all verdict and practical-label branches, forced SARIMA primary failure → fallback with constant, `converged=False` → failure, ConvergenceWarning → failure, clean fit kept, warning-rule (d), per-origin fallback counts, circular bootstrap uniformity and seeding, and the `--nhsbt` lock. |
| **N14** Garbled line 155 | Rewritten: "circular overlapping moving-block bootstrap", with the reason. |

### Optional

| Item | Fix |
|---|---|
| **O-a** Equal-weight lags | Now Bartlett (Newey–West) weights, matching the plan's wording. No change at lag 0 (the confirmatory tests). |
| **O-b** Holm-adjusted p | `holm_adjust` returns `p_holm`; reported in `primary_result.md` and `comparisons_vs_naive.csv`. Test: (0.01, 0.02, 0.04) → 0.03, 0.04, 0.04. |
| **O-c** 2019 substitute is older | Stated at line 145. |
| **O-d** HLN hedge | I re-checked the DOI on Crossref (IJF 1997;13(2):281–291) and replaced the hedge. |
| **O-e** 7 units/day scale | Plan says the 682 mean includes test months and is "for scale only". |

## Other changes

- New **Outputs** section lists every table. `forecasts_long.csv` and `naive_2021_vs_2019.csv` contain actual NHSBT values, so they are now in `.gitignore` and the plan says they stay with the snapshot.
- Software line adds openpyxl 3.1.5 (used by the loader).
- Red-cell, Sep–Oct and split checks are scored on the primary run's forecasts (no refit); the plan now says so.
- `primary_verdict` now takes the direction from the interval side (identical whenever the interval excludes zero).
- The legacy positional helpers keep their names for the Brazil script, but now use the circular bootstrap and refuse mismatched lengths.

## Not done, or left open

- **Brazil script not updated or rerun.** `aggregate_and_forecast.py` still pairs by position, and its warning-summary code expects the old tuple log format, so it would error with the v3 `inference.py`. Its published numbers came from the v2 code; the README now says so. Updating it is optional and was not requested.
- **Real-repo `.gitignore`:** the box copy is not a git repository; check the new lines in the clone you push from.
- **Human review** by a statistician, a transfusion-medicine specialist and someone who knows data licensing is still needed. An AI review is not a substitute.
- **Next step per the reviewer:** one more plan-matches-code check by Research Reviewer before Liam decides about posting.


## Post-review text fix (19 Nov 2026, after review_prereg_v3.md)
- V1 (Required): line 119 reworded. The `--nhsbt` URL check is described as a guard against accidental runs only; the protection is that the OSF registration timestamp precedes the run time in the manifest. Plan text only; code and hashes unchanged.
- V4 (Recommended): the Brazil README now says its numbers came from the archived v2 code and that the script does not run with the current inference.py.

## Code follow-ups after review 3 (19 Nov 2026, about 12:20 AM ET; approved by Liam)

Appended only; nothing above was edited (O3). Note that the table at the top of this file still shows the earlier v3 hashes for `nhsbt_analysis.py`; the current hashes are below and in plan line 119.

**New hashes**

| File | SHA-256 |
|---|---|
| `nhsbt_analysis.py` | `dcb2f18cf590505db266574b317368cf2d719126644e6d2f064aaf07404354ac` (was `d56b1c00…741359a`) |
| `inference.py` | `0e5248d473a0bb216f1d1e20d7536f0c3401b4e04e11bb3033f66a0528e0bf64` (unchanged) |

| Item | Change |
|---|---|
| **V1** (kept) | Plan line 119 wording from the earlier text-only fix is kept. One sentence added about the new code-hash check. The `nhsbt_analysis.py` docstring, which also overstated the lock, now says "guarded, not locked" and lists what it can and cannot check. Line 21 of this file (above) still has the old wording; this entry supersedes it. |
| **V2** code-hash check | Before reading the snapshot, `--nhsbt` now runs `verify_frozen_code()`: it hashes `nhsbt_analysis.py` and `inference.py` and stops unless both match **both** (a) the new manifest `FROZEN_CODE.sha256` (sha256sum format, checkable by hand with `sha256sum -c`) and (b) the hashes in plan line 119, parsed from `osf_prereg_study2_draft_v3.md`. **Why this design:** a script cannot contain its own hash (editing it changes the hash), so the expected values are kept in files the scripts never hash. Requiring the manifest and the plan to agree means an edited script, an edited manifest, or a plan/code mismatch each stops the run. Order: URL check → code hashes → snapshot hash → analysis. Limit: anyone can edit all three files, so this makes a quiet rerun visible rather than impossible. The verified hashes are written into `run_manifest.json`. **If the plan is renamed when posted** (for example to a final file name), update `PLAN_FILE` in the script, which changes its hash, so re-hash and update line 119 and the manifest. |
| **V3** ETS unreliable rule | `summarise_fits` now reports `omitted_share` for ETS and SARIMA, plus one `reliability` label: unreliable if more than half of origins were omitted (ETS or SARIMA), or more than half used the fallback (SARIMA). The label is copied to every comparison row (`method_reliability`) and shown in `primary_result.md`. Plan lines 123, 125 and the COVID-sensitivity bullet updated to match. On the made-up data, red-cell COVID-sensitivity ETS was omitted at 0.69 of origins (25 of 36, as the reviewer found) and is now labelled unreliable; cryo was 0.11. |
| **V4** (kept) | Brazil README text fix from the earlier edit kept. The Brazil script itself still imports the v3 helpers and was not changed. |
| **O1** | Plan names the interval method: percentile 95% (2.5th and 97.5th percentiles). |
| **O2** | `comparisons_vs_naive.csv` now gives each method's and naive's MAE on the paired months; `accuracy.csv` rows carry a note that each method is scored on its own months. Plan Outputs updated. |
| **O3** | This log is add-only from now on; this section was appended. |
| **O4** | New tests: an ETS failure at one origin (June 2023) removes its 1-, 2- and 3-month forecasts, counts one omitted origin, logs it, and the h=2 comparison pairs 34 months with Aug 2023 reported as dropped; "worse, practically meaningful" and "worse, may be smaller" labels; hash-mismatch stops (edited `inference.py`, a wrong manifest, a wrong snapshot hash). |
| **O5** | `--check-structure` now saves its console output to `study2/results/nhsbt_structure_check/check_structure_log.txt`, including the script hashes and the line "No data values were printed or saved. No forecasts, errors or tests were computed." It was rerun once at 12:19 AM ET on 19 Nov 2026 to create that log (structure only). |

**Tests:** `--synthetic-test` now runs the full pipeline plus 78 checks: **78 passed, 0 failed** (log: `synthetic_test_output/SYNTHETIC_test_log.txt`). Plan line 119 now says 78 checks.

**Still open:** the Brazil script is unchanged (see V4); the real-repo `.gitignore` check; human expert review; and, if Liam wants, one last quick plan-matches-code look by Research Reviewer at this code change.


## Text edits after review_prereg_v3b.md (19 Nov 2026)
- R-a: the plan states that the unreliable label is reported beside the verdict and never changes it.
- R-b: the status line and Version section are updated, with the fixed-file-name note added.
- Optional: the Brazil README line 5 now says the v2 bootstrap was non-circular. Note: the hash table near the top of this file shows the older nhsbt_analysis.py hash (d56b1c00...); the current hash is dcb2f18c... (see the section above and FROZEN_CODE.sha256).
- Plan text only; neither script changed.
