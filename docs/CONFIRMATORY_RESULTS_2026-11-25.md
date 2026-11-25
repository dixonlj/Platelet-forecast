# Confirmatory results (25 November 2026)

This is a local write-up of the one confirmatory run. It was prepared on the shared box after a Research Reviewer check of the first notes in `docs/osf_package/04_CHECKLIST_AND_AFTER.md`. The frozen plan was not changed. The run output files and their SHA-256 values were not changed. Nothing here has been posted to OSF.

All times below are America/New_York (ET) unless a UTC stamp is also given.

## 1. The primary result

The pre-registered primary test did not show that SARIMA order-up-to wastes fewer platelets than a yearly 90th-percentile par at Aachen: **-1.599 units a year** (95% moving-block bootstrap CI **-4.198 to 0**; p = 0.081). The STAT guard was **-28.58 STAT units a year**, meaning SARIMA used fewer STAT units over the five years taken as a whole. Decision: `not_shown`. The win rule was not met: the interval is not entirely below 0 (it touches 0), and the mean is not at most -10.

Under the pre-registered settings both arms wasted almost nothing (11 vs 3 units over 5 years), so the 10-unit threshold was unreachable; the primary test was uninformative about waste. "Not shown" here does not mean "forecasting does not help." It means this test had almost nothing to find. The whole 8-unit difference came from 4 days. The most SARIMA could have saved in this replay was about 2.2 units a year — well short of the pre-set bar of 10 fewer units a year.

The plan, the 10-unit threshold and the primary test are not being changed because of this. It is a stated limitation, and a lesson for a future, separately registered study.

### Per-year waste and STAT units (Aachen, 2014–2018)

| Year | Waste, SARIMA | Waste, par | Waste gap | STAT units, SARIMA | STAT units, par |
|---|---:|---:|---:|---:|---:|
| 2014 | 3 | 5 | -2 | 102 | 60 |
| 2015 | 0 | 0 | 0 | 162 | 404 |
| 2016 | 0 | 6 | -6 | 294 | 78 |
| 2017 | 0 | 0 | 0 | 90 | 284 |
| 2018 | 0 | 0 | 0 | 253 | 218 |
| **Five-year total** | **3** | **11** | **-8** | **901** | **1,044** |

The pre-specified year-count rule (frozen plan, line 172) is still reported: **0 years lower, 0 years higher, 5 ties**.

The five-year STAT guard passes (-28.58 STAT units a year), but the year-by-year pattern is mixed. SARIMA needed **more** STAT units than the par in 2014 (102 vs 60), 2016 (294 vs 78) and 2018 (253 vs 218), and fewer in 2015 (162 vs 404) and 2017 (90 vs 284). Saying only "fewer STATs with SARIMA" would overstate that.

## 2. Calibration check (promised in the plan)

The frozen plan (line 389) said Aachen recorded waste and emergency purchases would be compared with the new replay as a calibration check, not as a primary outcome. Line 407 said that even with STAT orders and mixed arrival ages, the replay may still sit below the recorded ledger, and that **that gap will be reported, not hidden**.

The recorded figures below are from the public Aachen file `data/UKA_Aachen_daily_platelets_2008-2018.csv` (Schilling et al., 2022), scored years 2014–2018 (1,826 days). The "Purchase" column is the source file's emergency-purchase field. The replay figures are the confirmatory par and SARIMA arms from `report.json` (primary year rows). The replay counterpart to recorded purchases is STAT units. These are related measures, not identical ones.

| Year | Recorded waste | Recorded emergency purchases | Replay waste, par | Replay waste, SARIMA | Replay STAT units, par | Replay STAT units, SARIMA |
|---|---:|---:|---:|---:|---:|---:|
| 2014 | 465 | 197 | 5 | 3 | 60 | 102 |
| 2015 | 452 | 248 | 0 | 0 | 404 | 162 |
| 2016 | 589 | 335 | 6 | 0 | 78 | 294 |
| 2017 | 508 | 593 | 0 | 0 | 284 | 90 |
| 2018 | 742 | 217 | 0 | 0 | 218 | 253 |
| **Five-year total** | **2,756** | **1,590** | **11** | **3** | **1,044** | **901** |
| **Average per year** | **551.2** | **318.0** | **2.2** | **0.6** | **~209** | **~180** |

The replay sits about two orders of magnitude below the recorded waste: about **551 wasted units a year** in the real ledger versus about **2.2 a year** for the par arm (and 0.6 for SARIMA) — roughly 250 times less. Recorded emergency purchases averaged 318 units a year; the par arm used about 209 STAT units a year, and SARIMA about 180. The simulated hospital is far tidier than the real one. Readers should see that before trusting any waste number from this replay. A waste gap in the simulation is not a real-world saving.

## 3. Network and Holm families (descriptive only)

Because the primary test did not show a difference, the network and three-model Holm family tests are descriptive only, under the fixed testing sequence. They are not confirmatory claims.

### Network (negative binomial minus each hospital's own yearly par)

The forecast wasted **146 more units a year** (95% CI 132–160; mean 145.9, CI 132.3 to 160.2; p = 0.0002) but needed about **1,147 fewer STAT units a year** (STAT gap -1,146.8 units a year). The pre-STAT shortfall gap was -144.5 days a year. These are two different measures; they are not both "STAT shortfalls."

The forecast sat at a different point on the waste-versus-shortage trade-off, so neither arm was simply better. Under the pre-set rule this is **"not shown", not a loss**, because the reverse STAT guard was not met: the waste CI is entirely above 0 and the mean is above +10, but the par needed far more STAT units.

The cushion is matched on past pre-STAT shortfall days. In the scored years, though, the forecast arm ran far "safer": 1,147 fewer STAT units a year against 146 more wasted. The two arms ended up at different safety levels, so their waste cannot be compared like for like. That is a limitation. The cushions were not re-matched after the fact.

By site type, over the seven scored years:

| Site type | Waste, forecast vs par (7-year total) | Waste gap per year | STAT units, forecast vs par (7-year total) |
|---|---|---:|---|
| Small (8 sites) | 2,680 vs 1,888 | +113 | 2,732 vs 3,676 |
| Mid (6 sites) | 442 vs 215 | +32 | 10,144 vs 10,975 |
| Large (2 sites) | 3 vs 0 | +0.4 | 14,181 vs 20,440 |

Most of the extra waste was at the small hospitals.

### Holm family (Aachen; all descriptive, all `not_shown`)

| Contrast | Mean waste gap/yr | 95% CI | p | Holm-p | STAT gap/yr |
|---|---:|---|---:|---:|---:|
| SARIMA minus weekday baseline | +0.400 | 0 to +1.199 | 0.724 | 1.0 | -19.19 |
| ETS minus SARIMA | -0.200 | -0.600 to 0 | 0.724 | 1.0 | +3.80 |
| Negative binomial minus SARIMA | 0.000 | 0 to 0 | 1.0 | 1.0 | -6.40 |

## 4. Pre-specified sensitivities (descriptive)

These outputs are marked `not_in_decision_chain`. None of them is part of the primary decision, the fixed sequence, or the Holm family. They do not rescue the primary result, and they will not change the plan.

### All eight pre-specified Aachen sensitivities

SARIMA minus par, units a year, unless noted.

| Sensitivity | Mean | 95% CI | p | STAT gap/yr | Waste, forecast vs par (5 yr) |
|---|---:|---|---:|---:|---|
| Par at P80 | -1.0 | -2.6 to 0 | 0.26 | -96.5 | 1 vs 6 |
| Par at P95 | -2.0 | -4.8 to 0 | 0.084 | -29.4 | 6 vs 16 |
| No STAT | -2.4 | -5.8 to -0.2 | 0.022 | 0 | 2 vs 14 |
| All arrive with 4 days | -2.2 | -5.0 to -0.2 | 0.018 | -28.6 | 4 vs 15 |
| All arrive with 3 days | -19.6 | -30.6 to -11.2 | 0.0002 | -32.6 | 61 vs 159 |
| Hindsight match (best case) | -1.0 | -3.4 to +0.4 | 0.48 | -21.8 | 6 vs 11 |
| All-history par | +0.2 | 0 to +0.6 | 0.72 | -161.5 | 1 vs 0 |
| Refit every 28 days | -1.6 | -4.2 to 0 | 0.081 | -31.0 | 3 vs 11 |

In the all-3-days sensitivity the forecast wasted 19.6 fewer units a year (95% CI 11.2 to 30.6 fewer), though it wasted more in 2 of 5 years (year-by-year waste gaps: -48, **+12**, -71, **+16**, -7). Under that setting the par wasted 159 units in 5 years, so this is a different, harsher world from the primary, where the par wasted 11. This is descriptive and hypothesis-generating only. It does not rescue the primary result and will not change the plan. Any follow-up on a harsher shelf-life setting would be a new, separately registered study.

### Other pre-specified descriptive outputs

- **Margin sensitivities** (win bar at 5 and at 20 units a year): the primary, the network and all three Holm contrasts were `not_shown` at both bars.
- **Weekday-specific par, Aachen:** -2.0 units a year (95% CI -4.4 to -0.2; p = 0.028; STAT gap -73.2 units a year). Descriptive only.
- **Network, daily delivery (vs the weekdays-only confirmatory setting):** +6.3 units a year (95% CI -3.0 to +16.1; STAT gap -119.5 units a year). Descriptive only.
- **Rotation versus par (network):** +24.6 units a year (95% CI 11.8 to 39.7; STAT gap -1,315 units a year). Descriptive only.
- **Central ordering versus par:** 0.0 units a year (STAT gap -3,489 units a year). Descriptive only.

## 5. How the run was done

- OSF registration: https://osf.io/tuj9p , DOI 10.17605/OSF.IO/TUJ9P. Registered at **8:34:04 AM ET** on 25 November 2026 (`date_registered` 2026-11-25T13:34:04Z), before any confirmatory data were generated. It is public, not embargoed.
- Frozen plan SHA-256: `eb20a51ebedc4b8e468a74dd77068944406121dc39ec1fada0be16842545d74b` (81,492 bytes). That hash matches the file on the box and the file attached on OSF.
- Repository PR #15 was merged at **8:43:35 AM ET**; `main` was at `8f1234e`.
- The analysis was run once, on a detached checkout of `5f079cee3da55e9727f204f74aa2db45fe8654ad`, with a clean git tree (untracked files included). `git_status_before_run.txt` is empty.
- Python 3.13.5. The version tuple matched the pre-registered requirement (`sys.version_info[:3] == (3, 13, 5)`). The full build string on the run was `3.13.5 (main, Jul 23 2025, 00:37:22) [Clang 20.1.4 ]` (a Clang build via uv). The frozen plan recorded a different build string: `3.13.5 (main, Aug 10 2026, 12:06:59) [GCC 14.2.0]`. This is a deviation in the build string only (see D1 in `docs/DEVIATIONS_2026-11-25.md`). The runner checks the version tuple, not the compiler tag, so the run was allowed.
- All 59 of 59 package pins in `requirements-confirmatory.txt` matched.
- The runner draws seed `20261121` **in memory and writes nothing to disk**. Its only network draw is `load_confirmatory_network`, which calls `make_network(20261121, confirmatory_caller=True)` (`confirmatory_run.py` lines 837–850; `NETWORK_SEED` at line 159) and writes nothing. The on-disk network copy (SHA-256 `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb` for the main CSV) came from a hand call of `make_network(confirmatory_caller=True)`. The frozen plan (line 86) says that seed must not be generated or opened by running the generator by hand. When that original on-disk copy was made, relative to the run, is still unverified. Whether it matches the runner's draw was checked later: after the confirmatory results were seen, and with Liam's go-ahead at 11:01 AM ET (America/New_York) on 25 November 2026, a cloud agent regenerated seed `20261121` once (no analysis re-run). The fresh draw matched the saved CSV (58,432 rows, all columns equal; `generator_parameters.json` and the other generator files also matched). The runner's own `load_confirmatory_network(confirmatory=True)`, imported and not run through `main`, matched on dates, `units_issued` and `site_type` for all 16 sites. **Caveat:** the original confirmatory process did not save its in-memory arrays, so this is a new draw of the same function, seed, flag, commit and pinned packages, not a replay of the arrays held during the run itself. The report is in `results_seed_check_2026-11-25/seed_check_2026-11-25.md`. The practical risk to the decision is low, because the runner did not read the file; it drew its own copy. This is recorded as deviation D2.
- Wrapper start in `run_start_utc.txt`: 13:50:04Z (8:50:04 AM ET). Wrapper log START: 13:50:07Z (8:50:07 AM ET). The `START`, `EXIT:0` and `DONE` lines in `confirmatory_run.log` come from the wrapper; the runner itself prints no START line. The report was written at 14:24:46Z (9:24:46 AM ET; folder `results/confirmatory/20261125T142446Z`). Wrapper end in `run_end_utc.txt`: 14:24:49Z (9:24:49 AM ET). The run started 16 minutes after the OSF registration. These times come from the run's own clocks; there is no independent timestamp.
- The run exited 0. Nothing from this run was committed to the repository. A copy of the 17 output files, plus a `SHA256SUMS` file, is in `advisory_tool/results_confirmatory_2026-11-25/` on the shared box.

## 6. Deviations

See `docs/DEVIATIONS_2026-11-25.md` for the three recorded deviations (D1 Python build string, D2 hand-made network copy, D3 wrapper-clock offsets), in the plan's four-part format.

OSF registrations cannot be edited. A results summary or the deviations file can be added later as a linked project file or update. That was not done here. Whether to add anything on OSF is Liam's decision.

## 7. Limits

- This study uses one long real public series (Aachen) and a synthetic 16-hospital network from a generator this project designed. A confirmatory result on that network confirms behaviour inside that simulated world, not in real hospitals.
- Only one confirmatory demand seed (`20261121`) and one arrival-age seed (`20261122`) were used.
- The Aachen replay sits far below recorded waste (section 2).
- The confirmatory bootstrap interval does not include uncertainty from choosing the par or the cushion (frozen plan, E6 in the Limits section).
- This is not a clinical trial and gives no ordering advice. It is a retrospective simulation. No clinical decisions follow from it.

## 8. No post-hoc changes

There is no change to the frozen plan, the 10-unit threshold, or the primary test because of these results. Any follow-up (for example a study in a harsher shelf-life setting) would be a new, separately registered study.

## 9. Approvals

Approvals for the freeze, the OSF posting, generating seed `20261121`, and the confirmatory run are Liam's to confirm in his own words. This write-up records what the files and the public OSF registration show. It does not itself stand in for those approvals.

## 10. Source files

- Run report: `results_confirmatory_2026-11-25/results/confirmatory/20261125T142446Z/report.json` (SHA-256 `ca9a1e134e9a1bba2ccb9c98b6c82f0998fdc42b1650561441ebcf7d62d0d005`)
- Run summary: `…/summary.md` (SHA-256 `c511fd72940d4fbab5a1a42c7aa33edca3f2760f11f61f7c111144fc0e4c83b6`)
- Network CSV (on-disk provenance copy; see D2): SHA-256 `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb`
- Seed check (after results; Liam's go-ahead 11:01 AM ET): `results_seed_check_2026-11-25/seed_check_2026-11-25.md` (SHA-256 `8f7d5d4452272f66ebf2ba574800d2e8bea03ba19324075374e2ae61d287675f`); verdict MATCH, with the caveat that this is a new draw of the same function, not a saved copy of the run's in-memory arrays
- Frozen plan: `docs/PREREGISTRATION_FROZEN_2026-11-25.md` (SHA-256 `eb20a51ebedc4b8e468a74dd77068944406121dc39ec1fada0be16842545d74b`)
- Deviations: `docs/DEVIATIONS_2026-11-25.md`
