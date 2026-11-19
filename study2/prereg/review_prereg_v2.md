# Review 2: Study 2 OSF pre-registration, version 2 (plus the Brazil rerun)

**Verdict: Not ready to post yet. The plan text is now mostly right, but the code doesn't fully do what the plan says, and the code that would actually analyse NHSBT doesn't exist yet. Fix the 4 new Required items first.**

- Reviewer: Research Reviewer (AI), second independent check, 18 Nov 2026, about 11:45 PM ET.
- I judged only from the files. I treated `changes_v1_to_v2.md` as claims and checked each one.
- I edited nothing except this file. Nothing was posted, sent or submitted.

**Files read in full:**
- `osf_prereg_study2_draft_v2.md` (248 lines)
- `inference.py` (293 lines)
- `nhsbt_analysis.py` (235 lines)
- `changes_v1_to_v2.md`
- my v1 review
- `brazil_exploratory/README.md` and the relevant parts of `aggregate_and_forecast.py`
- both Brazil charts

**What I ran:**
- The synthetic test, on a temporary copy in `/tmp` (deleted afterwards), on made-up numbers only.
- A small probe on the same made-up numbers to test the pairing, the COVID rules and Holm.
- **I ran nothing on the NHSBT workbook.**

---

## 1. Was a model fitted to NHSBT? No sign of it.

- No `.py` file reads the workbook. The snapshot path appears only inside an error message (`nhsbt_analysis.py` line 227).
- `--nhsbt` stops before opening anything. I checked: it exits with code 1.
- There are no output files, logs or `__pycache__` folders from an NHSBT run.
- The snapshot's modified time (9:43 PM ET) is unchanged, and its hash still matches.
- No script that could fit NHSBT even exists yet; see N1. So there is nothing that *could* have been run.

## 2. Hash and version check

| Item | Hash written in the plan | Hash I computed | Match? |
|---|---|---|---|
| `inference.py` | `6d55e1b1…cb9416` (line 119) | `6d55e1b1acfd17a5c6511c98080ff1480fb2bf66dd20d53e3e5ba313c6cb9416` | **Yes** |
| `nhsbt_analysis.py` | `0f429756…68a30d` (line 119) | `0f429756f03ac9362f87e75eecd554ca7a5bee48f83ac518ff7e2b571268a30d` | **Yes** |
| NHSBT snapshot | `f0e3fbc5…e696` (line 43) | `f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696` | **Yes** |
| Brazil de-identified CSV | `c6c9d4c3…d2a8` (README line 18) | `c6c9d4c3c901a943e9aaaada7a45010b6fadf043e52a4e539b300bc8abf0d2a8` | **Yes** |
| Software (line 119) | Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1 | the same on this box | **Yes** |
| Seed 20261118 | plan lines 119 and 159 | `inference.py` line 20: `SEED = 20261118`, used in every bootstrap call | **Yes** |

Version 1 of the draft is untouched (last modified 9:50 PM ET), as claimed.

**Caution:** a hash only proves the file hasn't changed. It doesn't prove the file does the analysis (see N1).

## 3. The 6 Required items from review 1

| # | Item | Status | Evidence |
|---|---|---|---|
| R1 | Block bootstrap | **Partly** | The plan (lines 155–162) and code (`inference.py` lines 23–96) match: moving blocks of 3 / h+2 months, 10,000 resamples, seed set, percentile 95% CI, and differences resampled as paired loss differentials. The block length is reasonable: a common rule of thumb for n≈36 gives about 3. **But** "paired by the same target months" is done by **position in a list**, not by month. If any model skips an origin, every later pair is mismatched. See N2. |
| R2 | DM test with HLN correction | **Resolved** | `inference.py` lines 99–143. Lag h−1 (0 at one month). The correction factor is √((n+1−2h+h(h−1)/n)/n). The p-value comes from a t distribution with n−1 degrees of freedom. A zero or negative variance is treated as "not computable". The formula is the standard Harvey–Leybourne–Newbold one, and the HLN DOI resolves to IJF 1997;13(2):281–291. Small notes are in O-a and N10. The pairing problem (N2) applies here too. |
| R3 | Holm on the 3 primary tests | **Partly** | The plan (lines 166–170) is good: Holm on exactly the 3 one-month platelet DM p-values (HLN-corrected), and "better" only if Holm rejects **and** the CI excludes zero. In code, `holm_adjust` and `primary_verdict` (lines 146–180) are correct; my test with p = 0.01, 0.02, 0.04 gave the right step-down answer. **But nothing ever calls them.** No script feeds them the three NHSBT p-values. See N1. |
| R4 | SARIMA fallback | **Partly** | The constant on the fallback is present (`trend='c'`, line 251). Warnings are now captured instead of silenced, and a convergence warning does trigger the fallback (lines 255–279). **But:** (a) the captured warnings are thrown away (`_logs`, `nhsbt_analysis.py` lines 146 and 151), and the COVID-sensitivity ETS keeps no log at all (lines 172–193). That contradicts plan line 129, "every warning … will be logged". (b) The `mle_retvals['success']` check can never fire: in this statsmodels version the key is `converged`, not `success` (I checked). (c) The code adds a criterion the plan doesn't list ("failed to" + "optim", `inference.py` line 197). See N5–N7. |
| R5 | ETS trend stated | **Resolved** | Plan line 123 says no trend, additive season, period 12, starting values estimated, fitted by least squares (SSE). The code matches (`inference.py` lines 217–224, `trend=None`). The Brazil script uses the same function. |
| R6 | COVID sensitivity | **Partly** | The plan (lines 137–147) is now clear. ETS and SARIMA treating the COVID months as missing is implemented. The seasonal-naive switch to 2019 is implemented, and I confirmed on made-up data that Nov and Dec 2022 used Nov and Dec **2019**. It applies only to those months and only uses past data, so there is no leakage. **But** plan line 144 says the regression keeps each month's real time position. The code renumbers time after dropping the 22 COVID months (`calendar_regression_forecast` uses `np.arange(n)`, line 46). That squeezes the trend: on made-up data the Nov 2022 forecast came out 671.4 instead of 673.9. See N3. |

**Summary: 2 Resolved (R2, R5), 4 Partly (R1, R3, R4, R6), 0 Not resolved.** The plan text deals with all six. The code falls short on four.

## 4. Graded issues (new, or left over)

Key:
- **Required** = fix before posting.
- **Recommended** = should fix.
- **Optional** = polish.

### Required

**N1. The analysis script can't actually run the pre-registered analysis.**
- *Where:* plan line 119 ("The fitting and inference code is in…", "frozen before posting"), and all of `nhsbt_analysis.py`.
- *The problem, plainly:* the hashed script contains building blocks only. It has:
  - no code to read the NHSBT sheet;
  - no conversion from monthly totals to units per day (`days_in`, line 30, is never used);
  - no step that runs the three primary tests through Holm and `primary_verdict`;
  - none of the secondary products, the Sep–Oct 2025 sensitivity, or the red-cell checks;
  - no output tables.
- The `--nhsbt` option just stops. So after posting, someone would still have to write the real analysis code, and that code would never have been frozen. The hash then proves very little. It's like sealing an empty envelope and calling it the sealed answers.
- *Fix:* Write the whole runner now:
  - load the sheet, convert to per day, run every pre-registered analysis, and write tables;
  - keep the NHSBT path switched off with a flag;
  - make the synthetic test run the **whole** pipeline on made-up numbers;
  - re-hash and update line 119.
- Or, if you don't do that, reword line 119 to say honestly that only the helper functions are frozen.

**N2. Forecasts are paired by list position, not by month, which breaks the comparison if any fit fails.**
- *Where:* `inference.py` lines 77–82 and 111–116 (the code just truncates both lists to the shorter length); `nhsbt_analysis.py` lines 146–155 (a failed ETS or SARIMA fit is skipped, but seasonal naive still gets a forecast for that month).
- *The problem, plainly:* if ETS fails at even one origin, its 6th forecast gets compared with naive's 6th forecast, but those are now different months. I tested this by dropping one forecast from the made-up data: **30 of 35 pairs became mismatched months**, and the MAE difference changed (−8.26 instead of the correct −8.72).
- This matters because the plan *allows* failures ("that origin is omitted for ETS", line 123).
- *Fix:* Store the target month with every forecast. Compare methods only on months where both have a forecast (a join by month). Report how many months were dropped. Add a test that drops one origin.

**N3. The COVID-sensitivity regression doesn't do what the plan says.**
- *Where:* plan line 144 vs `nhsbt_analysis.py` lines 159–166 and 45–46.
- *Fix:* Use each month's real position in the series as the time variable (e.g. `months.index(ym)`) in both training and forecasting. Or change the plan text. One of the two has to change so they agree.

**N4. The Flint citation in the Brazil README has the wrong authors, wrong pages, and a "quote" that isn't the abstract's wording.**
- *Where:* `brazil_exploratory/README.md` line 47, repeated in `changes_v1_to_v2.md`.
- *What's actually true:* PubMed 31685352 and Crossref give **Flint AW, McQuilten ZK, Irwin G, Rushford K, Haysom HE, Wood EM.** "Is Platelet Expiring Out of Date? A Systematic Review." *Transfus Med Rev* 2020;34(1):**42–50**. The README instead lists "Flint, McQuilten, Wood, Hudson and Wood" and pages 42–58. "Hudson" is not an author, and the second "Wood" is invented.
- The abstract's wording is "high rates of outdating frequently reported at 10% to 20%". The README's quote, "greater than 10% … 20%", doesn't appear in the abstract; I could not check the full text.
- This isn't in the OSF plan itself, so it doesn't strictly block posting. But a citation with made-up co-authors must be fixed before the README is shared anywhere.
- *Fix:* Use the real authors and pages, and quote the abstract exactly.

### Recommended

**N5. Actually save the warning logs.**
- *Where:* `nhsbt_analysis.py` lines 146, 151 and 172–193.
- *Fix:* Write every warning to a log file with its origin, horizon and method. Make the state-space ETS return its warnings too. (The Brazil script does keep a log, lines 300–313, so it's possible.)

**N6. Fix the dead `mle_retvals` check.**
- *Where:* plan line 129 and `inference.py` lines 271–274.
- *Fix:* Check `mle_retvals['converged'] is False` instead, and correct the plan text to match.

**N7. Plan and code list different failure criteria.**
- *Where:* `inference.py` line 197 adds "failed to … optim"; plan line 129 doesn't mention it.
- *Fix:* Add it to the plan or remove it from the code.

**N8. The 7 units/day threshold is stated but never used.**
- *Where:* plan line 153 vs line 166.
- *The problem, plainly:* as written, a method could be called "better" for a 3 units/day gain that the plan itself says wouldn't matter. "About 1% of the mean" is also a round-number judgement with no planning source behind it. And "this study is unlikely to detect them" has no power calculation behind it.
- *Fix:*
  - Add: "A difference is called practically meaningful only if the method is declared better under the rule above **and** its MAE is at least 7 units/day lower. If the interval includes −7, we will say the gain may be smaller than what matters."
  - Name the planning reason for 7, or say plainly that it is a judgement call.
  - Change "unlikely" to "may not be able to".

**N9. The research question still reads as if one to three months are all being tested.**
- *Where:* line 19, vs line 100 (two and three months are descriptive) and line 166 (only one month is confirmatory).
- *Fix:* "…forecast one month ahead (primary; two and three months reported descriptively)…"

**N10. The one-month DM test assumes the errors don't run together, but the plan says they do.**
- *Where:* line 164 (lag 0 at one month) vs lines 162 and 166 ("errors come in runs", "are correlated").
- *Why it matters:* lag 0 is the textbook choice. But by the plan's own words it may make the test too willing to call a difference. The joint rule (the CI must also exclude zero) partly protects against this.
- *Fix:* Add one sentence saying that the block-bootstrap requirement is the safeguard against this. Optionally, pre-specify a descriptive check with lag 2.

**N11. The bootstrap gives the first and last months less weight.**
- *Where:* plan line 155 and `inference.py` lines 30–39.
- *The problem, plainly:* in this non-circular version, the first and last months land in fewer blocks. For NHSBT the last months are Sep and Oct 2025, the possibly provisional ones the plan worries about. In the Brazil rerun (n=10, block length 5) there are only 6 possible block starts, so the intervals become nearly meaningless. Examples: SARIMA − naive at 3 months, 6.3 (CI 2.2 to 6.7); expiry SARIMA − naive at 3 months, HLN p = 0.000.
- *Fix:* Use a **circular** block bootstrap, which wraps around so every month gets equal weight, and say so in the plan. Also add to the Brazil README that its CIs at 2–3 months rest on very few distinct resamples.
- Also fix the garbled phrase "circular-no, non-circular" at line 155.

**N12. In the COVID sensitivity, SARIMA will mostly be the fallback model.**
- *Where:* plan lines 125 and 143.
- *Evidence:* on the made-up data, SARIMA fell back in **27 of 105 fits** in the COVID sensitivity, against 0 in the primary run. Fallbacks are also counted per (origin, horizon) fit, while the plan says "per origin".
- *Fix:* Count fallbacks per origin (or change the text to say per fit). Pre-state that the SARIMA sensitivity result will be reported with its fallback share, and treated as unreliable if more than half the fits fell back.

**N13. The synthetic test checks too little.**
- *Where:* `nhsbt_analysis.py` lines 196–216.
- *The problem:* it checks only the count of 36. The 2019 substitution is a comment, not a check (lines 212–213). Fallback, Holm, `primary_verdict`, the red-cell switch, and pairing after a failure are never tested.
- *Fix:* Add an assert for each of those. My own probe showed the 2019 rule works; the others need tests.

**N14. Wording at line 155.**
- "circular-no, non-circular" is garbled. Rewrite it once N11 is decided.

### Optional

- **O-a.** `inference.py` lines 126–128 uses equal weights for the lags (the original DM/HLN style), which is not the Newey–West (Bartlett) weighting the plan names. This makes no difference at one month (lag 0). Rename it, or apply Bartlett weights for the descriptive horizons.
- **O-b.** Report Holm-adjusted p-values, not just reject yes/no.
- **O-c.** The 2019 substitution uses a value from three years earlier. That makes naive's job harder than the models', which see 2022 data. That's acceptable for a descriptive sensitivity, but say it in line 145.
- **O-d.** Line 236 says the HLN paper wasn't re-opened. I confirmed the DOI resolves to Harvey, Leybourne & Newbold, *IJF* 13(2):281–291 (1997), and that the code's formula is the standard one. You can keep or drop that hedge.
- **O-e.** The 7 units/day figure is scaled from a mean that includes the test months. It's harmless and disclosed, but say "scale only".

**New-issue count: 4 Required, 10 Recommended, 5 Optional.**

## 5. Brazil rerun

- **Still exploratory and separate:** yes (README lines 3 and 99–100). Every result is labelled descriptive, and the "no winner" rule is followed.
- **De-identified file only:** yes. The script reads only `private_data/brazil/hemoprod_nacional_deident.csv` (line 36), and the hash matches. No data files are written. The charts show no names or IDs.
- **CC BY-ND respected:** yes. No derived data file is published. The panel chart now carries a footnote ("should stay private until a licensing check is done"), and I confirmed it is on the image.
- **M12 (conflicting tests explained):** handled (line 74), and honestly. Add the N11 caveat.
- **M13 (outdate-rate source):** a source was added, but it is mis-cited. See N4.
- **M14:** handled.

## 6. What improved (honestly)

- Real progress. Every v1 item is addressed in the text, and the plan is now specific where it was vague: block lengths, HLN, Holm, "both must agree", no-trend ETS, a constant on the fallback, and the COVID rules.
- The disclosures are good. It now says the Brazil runs came first and explains the method swap. It admits the red-cell date was a mild leak. It states the calendar limits.
- The DM and Holm functions are correct, the seed and versions are real, and the hashes match.
- The `--nhsbt` lock really works.
- The references in the plan itself (as opposed to the Brazil README) now carry correct DOIs.

## 7. Is it ready to post to OSF?

**No, not yet.** The plan reads well, but a pre-registration that points to frozen code has to point to code that **does the analysis exactly as written**. Right now:

1. the real NHSBT runner doesn't exist (N1);
2. a failed fit would silently mis-pair months (N2);
3. the COVID regression doesn't match the text (N3).

These are about a day's work. After that:
- re-hash both scripts;
- fix the Flint citation in the Brazil README (N4);
- ideally do N5–N9;
- have one more quick check that plan and code match.

**Then it is ready to post.** Fit nothing to NHSBT until it is posted.

---

*This is an AI review. It does not replace review by a human statistician (especially the bootstrap, DM and Holm details), a transfusion-medicine specialist, and someone who knows data licensing (NHSBT's missing licence and the CC BY-ND chart question).*
