# Review v3b — Study 2 OSF pre-registration (draft 3, updated in place) and code follow-ups

**One-line verdict:** All v3 items (V1–V4, O1–O5) are fixed in both plan and code. The hashes match, 78 of 78 synthetic checks pass, and the guard stops every bad case before the snapshot is read. Nothing has been fitted to NHSBT. **Ready to post after two small text edits that don't change any hash** (R-a and R-b below). No Required issues remain.

Reviewer: Research Reviewer. Date: 19 November 2026, about 12:25 AM ET. I judged only from the files and my own reruns. I treated the author's changes log as unverified. I edited nothing except this file. I fitted nothing to the NHSBT workbook.

---

## 1. Item status

| Item | What was asked | Plan | Code | Status |
|---|---|---|---|---|
| V1 | Line 119 must say honestly what the lock does | It now says the URL check is "only a guard against accidental runs" and "cannot check that the URL is a real registration". It says the check "makes a quiet edited rerun visible; it cannot make the run impossible", and that the real protection is the OSF timestamp coming before the run time in the manifest | The docstring (lines 20–30) now says "Guarded, not locked" and makes the same points | **Fixed** |
| V2 | Code-hash self-check | Line 119 describes it | `verify_frozen_code()` compares both scripts with **both** `FROZEN_CODE.sha256` **and** the hashes parsed from plan line 119. `run_nhsbt` runs the checks in this order: URL, then code hashes, then snapshot hash, then `run_pipeline` (lines 959–964) | **Fixed.** Order confirmed by my own tests (section 3) |
| V2 | Circular dependency? | The plan holds the script hashes | Neither script contains its own hash or the plan's hash. The script reads the plan and the manifest at run time, and nothing hashes the plan | **No loop.** The design holds together |
| V3 | Same ">50% unreliable" rule for ETS and SARIMA, in plan and code | Lines 123, 125 and 146: unreliable if more than half of origins were omitted (ETS or SARIMA), or more than half used the fallback (SARIMA) | `summarise_fits` lines 418–428 uses a strict `> 0.5` for both. Exactly half (18 of 36) is "ok" and 19 of 36 is "unreliable", and tests [11] check this | **Fixed: plan = code.** See R-a on when the label is applied |
| V4 | Brazil README provenance | README line 6 says the numbers came from `archive_v2_code/inference.py`, and that the script "does **not** run with the current … (v3) and has not been rerun with it" | The script was unchanged (it still imports the v3 module), as the README says | **Fixed.** Line 5 still has one stale phrase (O-b) |
| O1 | Name the interval method | Line 160: percentile, 2.5th and 97.5th | — | **Fixed** |
| O2 | MAE on paired months in comparisons | Outputs, line ~183 | `mae_method_on_paired_months` and `mae_naive_on_paired_months` (lines 347–348) | **Fixed** |
| O3 | Changes logs add-only | — | `changes_v1_to_v2.md` mtime is 23:53, the same as at review v3. The new v2→v3 section was appended, and the author openly notes the old hash still in its top table | **Fixed** |
| O4 | More tests | — | Tests [10]–[12]: an ETS failure at one origin removes all three horizons and the h=2 comparison pairs 34 months with Aug 2023 listed as dropped. Also covered: "worse" practical labels, and refusals for an edited `inference.py`, a wrong manifest and a wrong snapshot hash | **Fixed.** The tests check real behaviour, not just that the code runs |
| O5 | Save the structure-check output | Line 3 points to the log | `check_structure()` writes the log | **Fixed.** See section 4 |

## 2. Hashes (computed by me, `sha256sum`)

| File | Computed SHA-256 | Plan line 119 | FROZEN_CODE.sha256 | Claimed in brief |
|---|---|---|---|---|
| `nhsbt_analysis.py` | `dcb2f18cf590505db266574b317368cf2d719126644e6d2f064aaf07404354ac` | match | match | match |
| `inference.py` | `0e5248d473a0bb216f1d1e20d7536f0c3401b4e04e11bb3033f66a0528e0bf64` | match | match | match (unchanged) |
| NHSBT snapshot `.xlsx` | `f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696` | match (and the script's `NHSBT_SHA256`) | n/a | match, unchanged since the start |

`sha256sum -c FROZEN_CODE.sha256` gives OK for both entries. The manifest has only these two entries.

## 3. Guard tests

I made throw-away copies of `study2/prereg` in `/tmp` with **no** `data/` folder, so no real snapshot was anywhere in reach. I ran `run_nhsbt()` through a harness that logs every file hash and makes any call to `read_sheet` or `run_pipeline` fail loudly. Two cases were also run from the command line.

| Case | Result | Reached a read or fit? |
|---|---|---|
| A. No URL | Refused at the URL check | No (nothing hashed) |
| B. `https://example.com/x` | Refused at the URL check | No |
| C. Fake `https://osf.io/fake`, clean code | The code check passed, then the run crashed when hashing the missing snapshot (`FileNotFoundError`) | No: `read_sheet` and the pipeline were never called |
| D. Tampered `nhsbt_analysis.py` + fake URL | Refused: "actual … != manifest … / != plan" | No (snapshot never hashed) |
| E. Tampered `inference.py` + fake URL | Refused at the code check | No |
| F. Wrong hash on plan line 119 + fake URL | Refused: "actual … != plan" | No |
| G. Wrong manifest + fake URL | Refused: "actual … != manifest" | No |
| H. Plan file renamed | Crashed with `FileNotFoundError` on the plan | No (nothing hashed) |
| I. Dummy snapshot with the wrong hash | Refused at the snapshot hash check | No |
| J. Script tampered **and** manifest and plan edited to match | **Passed the code check** and went on to the snapshot check | Only stopped because no snapshot existed |

**Judgement.** The order is URL, then code, then snapshot, then analysis, as claimed. Every bad case stopped before any read or fit. Case J shows the limit honestly: someone who edits all three files gets through. So "a quiet edited rerun becomes visible, not impossible" is an **honest** description. The edited hashes would be written into `run_manifest.json` and would not match the plan text frozen on OSF. That is only visible if someone compares the two, but the plan says exactly that.

**Plan-filename dependency (case H).** This is low risk. OSF stores whatever file you upload, under any name, and the local file does not have to be renamed. If the local file is renamed, the script stops safely, but `PLAN_FILE` would then need changing, which changes the script hash and forces line 119 and the manifest to be redone. A one-line note is enough (R-b).

## 4. O5: the structure check on the real NHSBT file

- **Code path** (`check_structure`, lines 938–957, plus `read_sheet`). It hashes the snapshot, then `read_sheet` loads the months and values to check them: the sheet exists, the header and columns are present, the dates are real dates with no gaps, every value is numeric and positive, and the span is right. The only things written out are: the time stamp, both script hashes, the snapshot hash and whether it matches, the sheet name, the column names, the count, first and last month, "no gaps", and "all 4 product columns numeric and positive". The `read_sheet` error messages give the month or column but never a value.
- **The log** (`check_structure_log.txt`, 6 lines, run at 12:19:01 AM ET on 19 Nov 2026) has exactly those lines. **It has no platelet values and no summary statistics** (no mean, minimum, maximum or totals). It has no forecasts, errors, tests or model fits. It does **not** record whether values are fractional. That fractional-value finding comes only from the earlier descriptive look, which the plan discloses at lines 49–56, along with the reviewer's look at the mean of about 682 units a day.
- **Does it matter for the pre-registration?** No. It reveals less than what the plan already discloses.
- **Other results or cached runs.** I found no `study2/results/nhsbt_confirmatory/` folder, no `primary_result.md` and no `run_manifest.json` other than the SYNTHETIC ones, and no `__pycache__`. `study2/results/` holds only `nhsbt_structure_check/` and the older study-1 folders `s2m1`/`s2m10` (dated 18 Nov, 10:59 AM ET). I searched the whole box for files with "nhsbt" in the name. All I found were raw source downloads and scrapes, the archived v2 code, and the author's text-edit scripts in `/tmp`. None contains forecasts. The snapshot hash is unchanged (section 2).

## 5. Synthetic tests

I reran `--synthetic-test` on a `/tmp` copy that had no `data/` folder. The result was **78 passed, 0 failed**, with the message "NHSBT file was not read". My log matches the author's apart from the timestamp and path lines. `SYNTHETIC_accuracy.csv`, `comparisons_vs_naive.csv`, `forecasts_long.csv`, `fit_summary.csv` and `primary_result.md` are byte-identical to the author's, so the seeded run reproduces exactly. The author's test log (00:18:54) is later than the current script (00:17:52), so it came from this code. I deleted all `/tmp` copies afterwards.

## 6. Remaining issues

### Required
None.

### Recommended (text edits only; they don't change any hash)

**R-a. The plan doesn't say whether "unreliable" changes the confirmatory verdict.**
*Where:* plan lines 123, 125 and the practical-importance rule (~line 170). Code: `run_pipeline` lines 472–475 attaches `method_reliability` to each row, and `apply_primary_rule` / `primary_verdict` ignore it.
*Problem:* The label is applied **after** the verdict and sits next to it. It never changes the verdict. That is a reasonable choice, but the plan doesn't state it. Suppose primary SARIMA "beats" naive while more than half of its origins used the fallback. As written, you could later argue either way about whether that counts. That is a small leftover freedom in the main result.
*Fix:* Add one sentence: "The unreliable label is reported alongside the confirmatory verdict and does not change it; a verdict for an unreliable method will be described as such in the abstract." Or, if Liam prefers the stricter rule, say the method's primary test is reported as "not assessable". That second option would need a code change and new hashes.

**R-b. Status lines and file name at posting time.**
*Where:* plan line 3 ("DRAFT ONLY … has not been posted"), the Version section at the end, line 119, and `PLAN_FILE` on script line 65.
*Problem:* The posted plan should not say it is an unposted draft. Also, nothing in the plan says the local file must keep its name, or that only line 119's hash text has to stay intact.
*Fix:* Before uploading, update the status and version text. This is safe because the plan is not hashed and the parser only needs the two "`study2/prereg/<file>` (SHA-256 `…`)" strings. Add to line 119: "The local plan file must keep the name `osf_prereg_study2_draft_v3.md`, because the script reads it; the OSF upload may use any name." Rerun `--synthetic-test` once after editing to confirm that check [10] still passes.

### Optional

**O-a.** If the snapshot or plan file is missing, the script crashes with a raw `FileNotFoundError` traceback instead of a clean "Refusing: …" message (cases C and H). It still stops safely. A friendlier message would need a code change and new hashes, so only do it if the code is being changed anyway.

**O-b.** The Brazil README, line 5, still says the rerun was "aligned with the revised pre-registration (moving-block bootstrap …)". That is true of draft 2, but draft 3 now uses a circular bootstrap. Reword it to "aligned with draft 2 of the pre-registration".

**O-c.** The top table of `changes_v2_to_v3.md` still shows the superseded `d56b1c00…` hash. The author flags this and supersedes it below, which is acceptable under add-only. The phrase "approved by Liam" in that log can't be checked from the files.

## 7. Ready to post?

**Yes, after R-a and R-b are done.** These are text-only edits that don't change any hash. The plan and the code agree on every point I checked. The hashes match. The guard behaves as honestly described. Nothing has been fitted to the NHSBT series. Posting is Liam's decision, and nothing has been posted on my say-so. After posting, record the OSF URL and timestamp, and run `--nhsbt` only after that.

---

*Caveat: this review was produced by an AI reviewer working from the files and reruns on this box. It is not a substitute for review by a human statistician or a transfusion-medicine expert, and it may have missed problems.*
