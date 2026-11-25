# Deviations from the frozen plan (25 November 2026)

This dated deviations file follows the format in `PREREGISTRATION_FROZEN_2026-11-25.md` (lines 340–349). For each deviation it states what changed, why, whether the change was made before or after confirmatory results were seen, and what effect it had, or was expected to have, on the results.

The frozen plan itself was not edited. OSF registrations cannot be edited. Whether to add this file on OSF as a linked project file is Liam's decision; that was not done here.

These notes describe the one confirmatory run of 25 November 2026 (report written 9:24:46 AM ET, America/New_York). They do not change the plan, the 10-unit threshold, or the primary test.

## D1. Python build string

**What changed.** The frozen plan recorded this full `sys.version` string for the confirmatory environment: `3.13.5 (main, Aug 10 2026, 12:06:59) [GCC 14.2.0]`. The confirmatory run used Python 3.13.5 with a different build string: `3.13.5 (main, Jul 23 2025, 00:37:22) [Clang 20.1.4 ]` (a Clang build via uv). The version tuple was the same: `(3, 13, 5)`. All 59 of 59 package pins in `requirements-confirmatory.txt` matched. The runner checks `sys.version_info[:3] == (3, 13, 5)` and the package pins; it does not require the compiler tag or the date in the build string, so the run was allowed.

**Why.** The run was performed on a cloud agent, which provided Python 3.13.5 as a Clang/uv build rather than the GCC build recorded at freeze.

**Before or after results were seen.** Before. The interpreter was the one the run started with. The build string is in `python_version.txt` and in `report.json`, written with the results, but the choice of interpreter happened at the start of the run, not after the numbers were seen.

**Effect.** None detected on the results. The Research Reviewer later built the same Clang 3.13.5 interpreter (`uv` cpython-3.13.5, `[Clang 20.1.4]`, 23 July 2025) and installed `requirements-confirmatory.txt`. Its `pip freeze` was byte-identical to `docs/preregistration_pip_freeze_5f079ce_2026-11-25.txt`, and it matched the run's `pip_freeze.txt` once package-name spellings were normalised. On a copy of the `5f079ce` tree, `backtest_report.py`, `advanced_models_report.py` and `count_models_report.py` rebuilt `results/backtest_summary.md` with SHA-256 `ff2435f90d60241129c9df6dd042519a1f1e3e4bfcacdc152d19a6dd92718be2`, byte-identical to the frozen hash. The runner's exploratory smoke output (no `--confirmatory`) was byte-identical under the GCC and Clang builds. **Limit:** that check exercises the same models, simulator and bootstrap libraries, but not the confirmatory code path itself. The confirmatory path was not re-run as part of that check. A later, separate seed check, after results were seen, regenerated seed `20261121` once with Liam's go-ahead; that check is recorded under D2 and did not re-run the confirmatory analysis.

## D2. Hand-made on-disk copy of seed 20261121

**What changed.** The confirmatory runner draws seed `20261121` **in memory and writes nothing to disk**. It did not need a network file to score the network contrast. Separately, an on-disk copy of that seed was made by calling `make_network(confirmatory_caller=True)` by hand (six files, in the layout of `write_network`). The main CSV has SHA-256 `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb`. The frozen plan (line 86) says the confirmatory demand seed "must not be generated or opened by running the generator by hand." That hand call is therefore a deviation from the plan. An earlier write-up said the file was written "because the CLI refuses that seed" and "That is how the runner is designed." The second sentence was wrong and is withdrawn. The runner is designed to draw the seed in memory, under `--confirmatory` only, and to write nothing to disk.

**Why.** The on-disk files appear to have been kept as a provenance copy, so the network could be hashed and archived beside the run. That does not authorise a hand call of the guarded generator.

**Before or after results were seen.** The time of the original hand-made on-disk copy, relative to the confirmatory run, is still unverified. The generating agent's own logs were not used to fix that time, or to say whether anyone opened the file before the run. File times on the stored copies are copy times, not proof of when the first draw happened. The later seed-check described below was done **after** the confirmatory results were seen, with Liam's own go-ahead at 11:01 AM ET (America/New_York) on 25 November 2026.

**Later verification (25 November 2026, after results).** With that go-ahead, a cloud agent regenerated seed `20261121` once. The confirmatory analysis was not re-run. `confirmatory_run.py` was not executed; `results/confirmatory/` was not modified. The check's report is `results_seed_check_2026-11-25/seed_check_2026-11-25.md` (SHA-256 `8f7d5d4452272f66ebf2ba574800d2e8bea03ba19324075374e2ae61d287675f`). Verdict: **MATCH**.

The runner's only network draw is `load_confirmatory_network`, which calls `make_network(20261121, confirmatory_caller=True)` (`confirmatory_run.py` lines 837–850; `NETWORK_SEED` at line 159) and writes nothing to disk. A fresh draw, written with the generator's `_write_csv`, has the same SHA-256 as the saved long CSV: `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb` (58,432 rows; all columns equal). `generator_parameters.json` is byte-identical (SHA-256 `04c01fcb259f8a86f2c4dfca8aa051b725751953782d21a9eefefeaadd65757d`). The wide, expected-rate, shared-factor and site files also match byte for byte. The runner's own `load_confirmatory_network(confirmatory=True)`, imported and called directly, not through `main`, matches the saved CSV on dates, `units_issued` and `site_type` for all 16 sites.

**Caveat.** The original confirmatory process did not save its in-memory arrays. This check is a new draw of the same function, seed, flag, commit (`5f079cee3da55e9727f204f74aa2db45fe8654ad`) and pinned packages. It is not a bit-for-bit replay of the arrays held in memory during the confirmatory run itself.

**Effect.** None on the decision, because the runner drew its own in-memory copy and does not read the on-disk files. The seed check supports that the saved on-disk copy is the same series that function would draw again under those conditions, subject to the caveat above. The practical risk is low: the runner is hard-coded, with no options to steer the draw, so a peek at a file could not easily have changed the result. The hand call remains a deviation, because this is the step the plan's guard was built to prevent.

## D3. Wrapper clock offsets of three seconds

**What changed.** Nothing in the analysis. Four clocks from the same run differ by three seconds: `run_start_utc.txt` is 13:50:04Z and the wrapper log START line is 13:50:07Z; the report `written_at` is 14:24:46Z and `run_end_utc.txt` is 14:24:49Z. The `START`, `EXIT:0` and `DONE` lines in `confirmatory_run.log` come from the wrapper, not from the runner.

**Why.** Bookkeeping by a wrapper around the runner. This is recorded so the timestamps are not mislabelled.

**Before or after results were seen.** These stamps are from the run itself, not a later change.

**Effect.** None. They do not change any number, decision, or file hash.
