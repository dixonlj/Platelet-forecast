# Review: Study 2 OSF pre-registration draft (+ Brazil exploratory README)

**Verdict: Fix the 6 Required items, then it's ready to post. The honesty and framing are good. The statistics section is still too loose to lock in.**

- Reviewer: Research Reviewer (AI), independent check, 18 Nov 2026, about 10 PM ET
- Files reviewed (read in full, not edited):
  - `study2/prereg/osf_prereg_study2_draft.md` (206 lines)
  - `study2/brazil_exploratory/README.md` (78 lines), plus its script `aggregate_and_forecast.py` and both charts
  - the NHSBT snapshot `.xlsx`
- Nothing was posted, sent or submitted. I wrote only this file.

**Hard rules:** no breach found.
- Every dataset named is public, or it is listed as "not used".
- No employer is named.
- No vendor name appears in either file.
- The hospitals that are named (Aachen, Stanford, Tema General, Hamilton) are public data sources or published studies. Naming them is normal citation. It is not a leak.

**On "no model fitted yet":** I found nothing that contradicts it.
- No script on the box (`.py`, `.R`, `.ipynb`) reads the NHSBT workbook.
- The draft's "looking at structure" section (lines 47–54) lists only counts and number-format checks.
- It also openly says (lines 49 and 182) that an earlier review looked at averages.
- I can't prove a negative. The only real proof is posting the pre-registration on OSF, which timestamps it, before any model is run.
- To keep it clean, I did **not** compute any forecast or forecast error on the NHSBT series. My own look was limited to counts, number formats, and platelets per day over all 115 months: mean about 682 a day, range 509 to 740.

---

## 1. Reference check

| Citation (where) | Real? Link works? | Described accurately? |
|---|---|---|
| **Nandi AK, Roberts DJ, Nandi AK.** "Prediction paradigm involving time series applied to total blood issues data from England." *Transfusion* 2020;60(3):535–543. doi:10.1111/trf.15705. PMID 32067239 (draft line 150) | **Yes.** Crossref confirms the authors, title, journal, volume, issue and pages. doi.org goes to Wiley. | **Mostly yes.** The abstract says: *"We used daily aggregates of RBC units issued from 2005 to 2011 from the National Health Service Blood and Transplant… derived the average blood issues per week over 4-week periods… The four time-series methods… gave very similar results and predicted mean RBC issues with a standard deviation of the percentage error of 3.0% for 4 weeks ahead and 4.0% for 24 weeks ahead."* Three small slips: (1) it is the average per week over 4-week blocks, not "4-weekly totals"; (2) the draft leaves out that they tuned window size and model order; (3) their error measure (SD of % error) can't be compared with this study's MAE. See Recommended M6. |
| **Ejohwomu OA, Too J, Edwards DJ.** "A resilient approach to modelling the supply and demand of platelets in the United Kingdom blood supply chain." *Int J Management Science and Engineering Management* 2021;16(2):143–150. doi:10.1080/17509653.2021.1892548 (line 152) | **Yes.** It resolves to Taylor & Francis. A free author copy is on the University of Manchester repository. | **Vague and partly misleading.** It is a **simulation study** (agent-based plus discrete-event modelling) of **platelet** stock levels at UK Stock Holding Units. The data were "collected from typical UK SHUs" and are not public. "Open" fits the free paper, not the data. It is also about platelets, which makes it the closest UK platelet prior work, and the draft undersells that. No DOI is given. See M5. |
| **Turkulainen EV, Wemelsfelder ML, Janssen MP, Arvas M.** "A robust autonomous method for blood demand forecasting." *Transfusion* 2022;62(6):1261–1268. doi:10.1111/trf.16870 (line 177) | **Yes.** It is open access (CC BY-NC), PMC9325496. | **Yes.** Weekly red-cell demand: Finland 2014–2021 and the Netherlands 2009–2020. Their code repo (github.com/FRCBS/production_forecasts) says: *"Unfortunately, no data is made public due to its confidential nature."* So "data not made public" is true. No DOI is given in the draft. |
| **Azlin NS, Nor ME.** "Time Series Modelling of Daily Blood Donations in Malaysia." *Enhanced Knowledge in Sciences and Technology* 2026;6(1):426–436. doi:10.30880/ekst.2026.06.01.049 (line 171) | **Yes.** It resolves to the journal (UTHM). Crossref lists only Azlin. The journal page lists both authors. | **Yes.** The full text says the data came from DOSM at data.gov.my/data-catalogue/blood_donations_state, January 2019 to February 2025. That matches "part of the same official file". No DOI is given in the draft. |
| Aachen data, Study 1 (line 162). Source paper: Schilling et al., *JMIR Med Inform* 2022, doi:10.2196/29978 | Yes | No reference is given in the draft. Add it. |
| "Guan-style lasso" (line 163): Guan et al., *PNAS* 2017;114:11368–11373, doi:10.1073/pnas.1714097114 | Yes | No reference is given in the draft. Add it. |
| Stanford `pip` (line 163): github.com/bnaras/pip | Yes (HTTP 200) | Fine. Add the URL and version or commit. |
| svenlatham scraper (line 169): github.com/svenlatham/nhsbt-blood-levels | Yes (HTTP 200) | Fine. |
| **NHSBT Parliamentary Questions page** (line 30) | **Yes** (HTTP 200). It links the same file. No licence is printed. It has the "could be revised… will not be reissued" warning the draft quotes. | Accurate. |
| **NHSBT workbook link** (line 30) | **Yes** (HTTP 200, 87,440 bytes). I downloaded it today. **Its SHA-256 matches the snapshot exactly.** The server says the file was last modified 28 Oct 2026, 10:49 AM ET. | Accurate. |
| Hamilton TRUST / Motamedi / Li, PEI, JRC, Tema Ghana, Kaggle, CDC/WHO (lines 170–180) | Listed as "not used" | No full references. That's acceptable for a "not used" list. Optional: add links. |

**Bottom line:** every citation is real. None is invented. Two are described loosely (Nandi a little, Ejohwomu more). Four have no DOI.

---

## 2. Data-claim check (my own numbers, using openpyxl)

| Claim | Result |
|---|---|
| SHA-256 = f0e3fbc5…e696 | **Yes, it matches**: `f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696`. Today's live download matches too. |
| Sheet "Blood Products Issued by Month" with a "Platelets" column | **Yes.** The columns are Month, Red Blood Cells, Platelets, Fresh Frozen Plasma, Cryoprecipitate. |
| 115 months, Apr 2016–Oct 2025, no gaps | **Yes.** 115 rows from 2016-04 to 2025-10. Every step is one month. No blank cells in any product column. |
| Platelets on a quarter-unit grid, 88/115 not whole numbers | **Yes.** All 115 are on the quarter grid, and 88 are not whole numbers, starting April 2016 (21,337.75). |
| Red cells 15/115 fractional, starting Apr 2024; May–Aug 2024 whole numbers | **Yes.** The fractional months are Apr 2024, then every month Sep 2024–Oct 2025 (15 in total). |
| FFP and cryo fractional from 2020 | **Yes.** FFP: 19 months, Apr 2020–Aug 2022. Cryo: 48 months, from May 2020. Cryo is not on a quarter grid. |
| Title says "Apr 2016 – Aug 2025" but the rows run to Oct 2025 | **Yes.** Row 1 of the sheet and the Data Notes both say "April 2016 - August 2025". The Data Notes also say "Period Covered: 2016 - 14/11/2025", and the extract date is 12/11/2025. There is also a "#VALUE!" error cell at the top of the Data Notes, which suggests the sheet was assembled by hand. |

**Is it OK to use all 115 months?** Yes, if three things are true: the hash is fixed, the gap between the title and the rows is disclosed (it is, at line 29), and a sensitivity check covers the two extra months. That check matters because **September and October 2025 are scored test months**: they are the last two one-month-ahead targets. If they are provisional, they directly affect the result. See M3.

---

## 3. Graded issues

Plain-words key:
- **Required** = fix before posting to OSF.
- **Recommended** = should fix; the plan is weaker without it.
- **Optional** = polish.

A pre-registration exists to lock every choice *before* the results are seen. So anything vague here is a problem: vague wording is a choice you can still make later, after seeing the results.

### Required

**R1. The confidence intervals will be too narrow unless the bootstrap uses blocks.**
- *Where:* draft lines 138–139, "95% bootstrap confidence interval".
- *Problem:* The draft doesn't say which bootstrap. The Brazil script (`aggregate_and_forecast.py`, `bootstrap_mae` and `bootstrap_diff`, about lines 366–399) uses the plain kind, which picks single months at random. That will probably be reused for NHSBT.
- Forecast errors on a smooth monthly series come in runs: a miss this month makes a miss next month more likely. For the 2- and 3-month horizons this is built in, because neighbouring forecasts overlap.
- A plain bootstrap ignores those runs. It makes the interval look tighter than it really is, which makes a "winner" look more certain than it is.
- *Fix:* Pre-specify a **moving-block (or stationary) bootstrap**:
  - a fixed block length chosen now (for example 3 months for the 1-month horizon, and h + 2 months for horizon h);
  - 10,000 resamples and a fixed seed;
  - for differences, resample the **same target months** for both methods (paired).

**R2. The Diebold–Mariano test isn't fully specified.**
- *Where:* line 140, "a lag consistent with the forecast horizon".
- *Problem:* That phrase leaves room for choices later. The Brazil script uses Newey–West with h−1 lags and a normal-distribution p-value, with no small-sample correction. With only 34–36 errors, the normal p-value is too generous.
- *Fix:* State all of these:
  - Newey–West variance with h−1 lags (lag 0 at 1 month ahead);
  - the **Harvey–Leybourne–Newbold small-sample correction**, with p-values from a t distribution with n−1 degrees of freedom;
  - absolute-error loss, two-sided;
  - what happens if the variance estimate comes out zero or negative (for example: report "test not computable" and count it as "could not tell apart").

**R3. Many comparisons, and no correction.**
- *Where:* lines 136–144, especially line 144: "the same rule will be used for secondary products and for the two- and three-month horizons".
- *Problem:* The primary question alone has **3 tests** (ETS, SARIMA and the regression, each against seasonal naive). Across the whole plan there are 3 methods × 3 horizons × 4 products = **36 tests**. The COVID sensitivity doubles that, and the red-cell sensitivity, red-cell split and 3 secondary metrics add more: well over 100 comparisons.
- At a 5% threshold, a few will come out "significant" by luck alone. The rule that both the CI and the DM test must agree helps, but doesn't fix this.
- *Fix:*
  1. Apply a **Holm correction to the 3 primary tests**.
  2. Say plainly that all secondary, horizon and sensitivity results are **descriptive**: no "significant" or "better" wording, and no winner declared from them.
  3. State the total number of comparisons in the paper.

**R4. "Fails to converge" for SARIMA (and "fails to estimate" for ETS) is undefined. As coded, it wouldn't match the text.**
- *Where:* line 116 (SARIMA fallback) and line 114 (ETS).
- *Problem:* The fallback order is fine as a single reserved option. But *when* it kicks in is a hidden choice. In the Brazil script the fallback runs only if the software crashes. Convergence warnings are silenced (`warnings.simplefilter("ignore")`), so a model that "didn't converge" but still produced a number would never trigger the fallback.
- *Fix:* Define failure exactly. For example: a crash, OR a statsmodels ConvergenceWarning, OR a forecast that isn't a finite number. Then also state:
  - whether a fallback, once used, applies only to that origin;
  - that the fallback (1,0,1)(1,0,1)12 includes a constant (it has no differencing, so without a constant it forecasts toward zero);
  - that the number of fallback origins will be reported.
- Also log, without silencing, every warning at every origin.

**R5. "Additive Holt–Winters" could mean two different models.**
- *Where:* line 114.
- *Problem:* Textbook Holt–Winters has a trend term. The Brazil script fits **no trend** (`trend=None`), which is a different model: level plus season only. Choosing between them after seeing the results is exactly the kind of freedom a pre-registration must remove.
- *Fix:* State all of these:
  - the trend: none, additive, or damped additive;
  - the season: additive, period 12;
  - initial values estimated;
  - fitted by maximum likelihood;
  - the software and version (for example Python 3.x, statsmodels 0.14.x, `ExponentialSmoothing`).

**R6. The COVID sensitivity analysis can't be run as written, and the baseline already uses COVID months.**
- *Where:* lines 126–128.
- *Problem 1:* ETS and SARIMA need an unbroken monthly series. "Excluding March 2020–December 2021 from the training windows" doesn't say how: treat those months as missing, cut them out and join the ends, or start training in January 2022? The last option leaves only 10 months at the first origin, which isn't enough for a 12-month season.
- *Problem 2:* Line 126 says the COVID window "sits entirely inside the training history". That's true. But the **seasonal naive forecasts for the first two test months (November and December 2022) are simply the November and December 2021 values**, which are inside the COVID window. So COVID months directly feed two baseline forecasts.
- *Fix:*
  - For ETS and SARIMA (state-space models), treat the COVID months as **missing values**.
  - For the regression, drop those rows.
  - For seasonal naive in the sensitivity, use the "most recent same calendar month outside the COVID window" (for November and December 2022 that means 2019).
  - Add a sentence to line 126 noting that the baseline uses November and December 2021.

### Recommended

**M1. Say in advance what size of difference would matter.**
- *Where:* line 142.
- *Problem:* The honesty is consistent. Lines 142, 187–188 and 87 all say the test window is small and a tie is likely. I found no hidden claim that contradicts this. But "can't tell apart" is more useful if readers know how big a difference the study could have seen.
- *Fix:* Pre-state a smallest difference that would matter for supply planning, chosen from planning judgement and **not** from the data. For example: 1% of typical daily issues, about 7 units a day. Say the study is unlikely to detect differences smaller than that.

**M2. The red-cell "April 2024" switch was found by looking at test-period months.**
- *Where:* line 73.
- *Problem:* The date was spotted in the format of numbers that fall inside the test window. Before April 2024 shows up in the training data, a forecaster could not have known about it, and the switch can't be estimated. That is a mild information leak, though it's about number format, not results, and it is disclosed.
- *Fix:* Add the switch only once at least, say, 3 months after April 2024 are in the training window. Report the red-cell regression both with and without it.

**M3. Check the two months the sheet's own title leaves out.**
- *Where:* line 29.
- *Fix:* Add a pre-specified sensitivity that drops September and October 2025 as scoring targets, since they fall outside the sheet's stated period and may be provisional.

**M4. Drop the word "replication".**
- *Where:* line 152, "an **extension and replication**".
- *Problem:* A replication repeats the same question on similar data. This study changes the product, the time grain, the period and the methods.
- *Fix:* Call it "an extension". *(Note: an earlier review from this reviewer suggested "extension and replication". On a closer look, "replication" overstates it. That's my correction.)*

**M5. Describe Ejohwomu et al. correctly.**
- *Where:* line 152.
- *Fix:* For example: "Ejohwomu, Too and Edwards (2021, doi:10.1080/17509653.2021.1892548) simulated **platelet** stock levels at UK Stock Holding Units (agent-based and discrete-event modelling). It is the closest UK platelet work, but it is a simulation, not a forecasting-method comparison, and its data are not public."

**M6. Tighten the Nandi sentence.**
- *Where:* line 150.
- *Fix:*
  - Say "average weekly issues over 4-week periods" instead of "4-weekly totals".
  - Add "with tuned window size and model order".
  - Add that their SD of % error cannot be compared directly with this study's MAE.

**M7. Give full references with DOIs.**
- *Where:* lines 150–177.
- *Fix:* Add the DOIs from the table in section 1 for Turkulainen, Azlin & Nor, Ejohwomu, Schilling (Aachen), Guan, and the `pip` URL and commit.

**M8. The affiliation names an AI agent as if it were a lab.**
- *Where:* line 7, "(Platelet Forecast Lab)".
- *Problem:* That is the old name of an AI assistant, now called Transfusion Forecast Lab. On OSF it reads like a research institution.
- *Fix:* Use "Independent researcher". The AI help is already disclosed honestly at line 200.

**M9. Disclose that the Brazil results already existed when the exact model settings were written down.**
- *Where:* "Methods" (lines 108–120) and lines 156–182.
- *Evidence:* From file times on the box (ET):
  - the Brazil script and charts were written at 9:48 PM;
  - the pre-registration at 9:50 PM;
  - the exact SARIMA orders and fallback appear first in these two files;
  - the earlier review (8:53 PM) suggested a "12-month seasonal average" and "at most one ML model", which this draft replaced with the calendar regression.
- I see no sign of tuning toward the Brazil results. The draft kept SARIMA even though SARIMA did worst in Brazil. But readers should be told.
- *Fix:* Add one sentence: "The exploratory Brazil forecasts (seasonal naive, ETS, SARIMA, same orders) had been run before this plan was finalised. The method list was not changed after seeing them." Add one more giving the reason for swapping the seasonal average for a calendar regression.

**M10. Say "expanding window".**
- *Where:* lines 82–85.
- *Fix:* Say whether the training window grows by one month at each origin (expanding) or stays a fixed length (rolling).

**M11. Per-day scaling fixes month length, not working days.**
- *Where:* line 101.
- *Problem:* Dividing by days in the month is sound. But issues follow hospital working days, and the number of weekdays and bank holidays (and when Easter falls) changes from year to year. That affects the seasonal naive baseline too.
- *Fix:* Keep the primary metric as it is. Add this as a stated limitation.

**M12. Brazil README, lines 51 and 61: explain the conflicting test results, and don't call Brazil "pre-specified".**
- *Problem:* SARIMA at 2 months has "DM p=0.01" while the bootstrap interval still included no difference. That conflict comes from the plain bootstrap and an uncorrected DM test on 11 points. Separately, "pre-specified order" at line 51 suggests Brazil was pre-registered, and it wasn't.
- *Fix:* Add "with 10–12 points neither test is reliable; the bootstrap ignores runs of errors and the DM p-value has no small-sample correction". Change "pre-specified" to "fixed in advance (the same orders planned for NHSBT); the Brazil analysis itself was not pre-registered".

**M13. Brazil README, line 47: a claim with no source.**
- *Problem:* "roughly 10–20% hospital outdate rates often quoted in the literature" has no citation.
- *Fix:* Cite a source or delete the sentence.

**M14. Brazil chart vs. the no-derivatives licence.**
- *Where:* README line 20 and `chart_panel_transfusions_expiry.png`.
- *Problem:* The chart plots all 36 monthly panel totals, which is essentially the derived dataset drawn as a picture. Charts are generally treated differently from data files, but under CC BY-ND this is a grey area.
- *Fix:* Before anything goes public, ask someone who knows licensing. Keep the chart private until then.

**M15. Name the software and freeze the code.**
- *Where:* add to "Methods".
- *Fix:*
  - List the Python and statsmodels versions and the random seed.
  - Ideally, write the NHSBT analysis script before posting and include its SHA-256 in the pre-registration.
  - The script should be tested only on made-up data or Brazil data, never on NHSBT.

### Optional

- **O1. Line 102 (MAPE).** The stated reason for making MAPE secondary is weak here. Daily platelet issues never fall below about 509, so MAPE isn't unstable. MAPE on the per-day series is also identical to MAPE on the monthly totals. Harmless; reword if you like.
- **O2. Line 142.** Add: "If seasonal naive is reliably *better*, we will say so plainly."
- **O3. Line 37.** The workbook was first downloaded for scouting at about 7:32 PM ET (copies in `/tmp/study2-scout/`) before the snapshot was saved. Say "first downloaded … for scouting; snapshot saved …". The hashes match, so nothing changed.
- **O4. Line 31.** Mention the internal date mismatch (extract date 12/11/2025 vs. "Period covered 2016 – 14/11/2025") and the "#VALUE!" cell in Data Notes, as signs of a hand-assembled file.
- **O5. Line 45.** `.gitignore` does list `study2/data/public/` and `private_data/`. But `/workspace/platelet-forecast` on the box is not itself a git repo. Check the ignore rule in the real repo clone before any push.
- **O6. Brazil README, line 9.** "0 rows with those city names" is true for exact names. The only partial matches are 6 rows for "São Paulo das Missões", a small town in Rio Grande do Sul. I spot-checked 14 other São Paulo and Rio de Janeiro state cities (Campinas, Niterói, etc.) and found 0 rows each. Say the check was by city, since the file has no state column.
- **O7. Housekeeping.** `/tmp/country-survey/` still holds a copy of the de-identified CSV (same hash) and a state-level ANVISA 2021 xlsx (no identifiers). The raw file with IP addresses is gone, as Liam asked. Consider keeping only the `private_data/` copy. I deleted nothing.

---

## 4. What's genuinely good (briefly)

- The framing is honest and consistent: a national supply-planning question, "not hospital daily ordering". That appears in lines 21, 33, 95 and 188. The title can't reasonably be read as a hospital ordering study.
- It lists what has already been looked at and what has already been run (lines 156–182), including the Stanford results that favoured SARIMA. That is unusually open.
- One primary series. Secondary series named up front and "reported whatever they show". A short, closed method list with no machine learning.
- A dated snapshot with a hash that I confirmed. No redistribution of unlicensed data.
- "If we can't tell them apart, we'll say so" is the right rule.
- The Brazil README is clearly labelled exploratory. It uses only the de-identified copy (no IP, CNPJ, CNES or address columns; I checked the hash and headers). It doesn't redistribute data. It states its limits plainly (no São Paulo or Rio, a growing set of reporting sites, a weak site key, unverified expiry) and says it must not drive method choice.

## 5. Recommendation

**Post after the Required fixes. It doesn't need major rework.**

The six Required items all tighten the statistics: the bootstrap type, DM details, multiple testing, the fallback trigger, the ETS form, and how the COVID sensitivity works. Each is a sentence or two. Without them, the plan still leaves choices open that could be made after the results are in, which defeats the point of pre-registering.

Do the Recommended items in the same pass if possible, especially M4, M5, M8 and M9. Then re-check the final text once more before it goes on OSF. Fit nothing to NHSBT until it is posted.

---

*This is an AI review. It does not replace review by a human statistician (for the bootstrap and DM details especially), a transfusion-medicine specialist, and someone who knows data licensing (for NHSBT's missing licence and the CC BY-ND chart question).*
