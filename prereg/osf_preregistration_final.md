---
title: "OSF preregistration: Do demand forecasts reduce simulated platelet waste compared with a standing order? A calibrated, preregistered re-analysis of public data from a German university hospital, with a replication on public US data"
author: "Liam Dixon (ORCID 0009-0003-0610-197X)"
date: "Final version, 14 November 2026. Not yet registered on OSF. Not submitted to a journal."
---

> **Status: FINAL, ready for the author to register on OSF.** Nothing in this file has been registered, posted or shared. The author will register it himself on osf.io. No new analysis, simulation or model fit was run to write or finalize it. The only computations were descriptive counts from the public Aachen file (the Section 2.4.2 targets, which match figures already in preprint draft v9 and were rechecked against that file when this version was prepared), a standard power calculation, and SHA-256 fingerprints of input files (`paper/osf_prereg_input_hashes.txt`, rechecked for this final version; all 35 fingerprints were unchanged).
>
> Personal, educational, advisory-only project. Public data only. It is not a clinical tool, not ordering advice for any blood bank, and nothing will be deployed.

**How this plan maps onto OSF.** The headings follow the current **OSF Preregistration** template (schema version 4, read from the live OSF API on 14 November 2026; see `paper/osf_how_to.md`). That is the template to use. Its pages are *Overview*, *Research Design*, *Sampling*, *Variables*, *Analysis Plan* and *Other*. Title, description and contributors go in OSF's separate metadata step. Because this is a secondary-data study, Section 3 also answers the questions of OSF's **Secondary Data Preregistration** template (datasets, access date, prior knowledge, unit of analysis), so that template can be used if preferred; this file covers both. The full file should also be uploaded as an attachment.

---

# 0. Metadata (OSF "metadata" step)

**Title.** Do demand forecasts reduce simulated platelet waste compared with a standing order? A calibrated, preregistered re-analysis of public data from a German university hospital, with a replication on public US data.

**Author.** Liam Dixon, independent researcher (medical laboratory technician). ORCID 0009-0003-0610-197X. Contact: dixonlj1993@gmail.com.

**Description (for the OSF description box, about 120 words).** Platelets last only a few days, so blood banks trade waste against shortages. An exploratory study of public daily platelet counts from University Hospital Aachen (2008–2018) found that, at the hospital's recorded shortage frequency, newer forecasts (SARIMA, gradient boosting, Chronos-Bolt) did not clearly waste less than simple rules, and that a "standing order" based on last year's weekday averages did about as well. Independent reviewers asked for a simulation calibrated to the hospital's record, the standing order as the main comparator, a fairer ordering rule, stronger statistics and a second site. This plan fixes those analyses before they are run. The data are public and have already been analysed extensively; Section 3 discloses exactly what has been seen.

**Suggested tags.** platelet inventory; demand forecasting; blood bank; waste; simulation; time series; secondary data; preregistration.

**Suggested subject.** Medicine and Health Sciences, then Pathology / Laboratory medicine, or Operations research.

**Licence for the registration text.** CC BY 4.0.

**Funding.** None. **Competing interests.** The author works in a hospital blood bank. This work is done independently, on personal time and equipment, using only public data. No employer data, systems or resources are used.

**Visibility / embargo.** The registration will be made **public immediately, with no embargo**, so that OSF can issue a DOI on release.

## 0.1 Decisions locked on 14 November 2026

The choices below are final for this registration. Options that were still open in the draft are marked "chosen when finalizing"; they follow the same conservative line as the author's locked choices.

| Topic | Locked choice |
|---|---|
| Aachen shortage target (primary) | Match each test year's recorded short days in the scoring window (2012–2018: 40, 31, 21, 38, 35, 42, 31). |
| Fixed shortage targets | **20 short days a year** is a pre-declared **sensitivity analysis**. A fixed 50 short days a year is an additional sensitivity, as already reported in preprint draft v9. |
| Smallest meaningful waste difference (Aachen) | **0.5 percentage points.** |
| Main ordering rule | **Horizon-scaled cushion (R1):** the cushion is sized to each order's days of coverage. The constant (fixed) cushion (R2) is the comparison. The age-aware rule (R3) remains secondary. |
| Second hospital | **Keep Stanford** `pip` (https://github.com/bnaras/pip) as the replication site (RQ5). |
| Registration visibility | **Public immediately, no embargo.** |
| Licence | CC BY 4.0 (chosen when finalizing; this was the draft's suggestion). |
| Foreknowledge (OSF required question) | "Authors have observed the data, but have not performed the proposed analyses," with the full disclosure in Section 3.6 (chosen when finalizing; this was the draft's recommended, accurate option). |
| Stanford matching target | Shortage on **1% of scored days (5 of 509 days)**. Targets of 0 and 25 days (5%) are sensitivities. Stanford has no recorded short-day series comparable to Aachen (chosen when finalizing). |
| Stanford minimum meaningful difference | **6% of the standing order's Stanford waste** at the matched point, in relative terms. An absolute 0.5-point bar would be meaningless at Stanford's typical 1–4% waste; 6% of Aachen's roughly 8.5% is 0.5 points, so the relative bar is aligned (chosen when finalizing). |
| NHSBT monthly issues | May be used only as a **labelled exploratory national-level check** (Section 5.3). It is not a primary or secondary analysis and not a third site (added when finalizing). |

**Filled in before registering:** the Aachen and Stanford first-download dates (13 November 2026, Section 3.1), the preprint DOI status (not yet posted, Section 3.7), and the NHSBT access date (not yet downloaded, Section 5.3). The author should confirm these are correct before submitting.

Do not start the preregistered analyses until the registration has been submitted on osf.io.

---

# 1. Overview

## 1.1 Research questions and hypotheses

**Primary research question (RQ1).** In a simulation calibrated to the hospital's record, and at a matched shortage frequency, does any of four past-use forecasts waste fewer platelet units than the **prior-year standing order**? The four forecasts are gradient boosting, detrended gradient boosting, SARIMA and Chronos-Bolt. The data are public daily counts from University Hospital Aachen, with test years 2012–2018.

Each of the four forecasts is one **primary comparison** against the standing order, so there are 4 comparisons in all. The hypotheses are two-sided:

- **H1a.** Gradient boosting (original, as in v9) wastes a different percentage of units than the standing order.
- **H1b.** Detrended gradient boosting wastes a different percentage than the standing order.
- **H1c.** SARIMA wastes a different percentage than the standing order.
- **H1d.** Chronos-Bolt wastes a different percentage than the standing order.

The null for each is no difference in mean waste (percentage points). Our honest expectation, given the exploratory v9 results in Section 3.6, is **a small or no difference**: within about ±0.3 points under the documented calendar. The question is therefore whether that impression holds once the simulation is calibrated and the ordering rule is fairer. It is not a test of a predicted big win.

**Secondary research questions** (not confirmatory; Section 5.1):

- **RQ2.** The same comparisons against the **4-week weekday average**, which was the comparator in preprint v9.
- **RQ3.** Does the answer change across the whole **waste-versus-shortage trade-off**, not just at one matched point?
- **RQ4.** Do the answers change under the **constant cushion** used in v9, or under an **age-aware** ordering rule?
- **RQ5.** **Replication:** does the primary comparison give the same answer on the public Stanford example data (two Stanford hospitals, 2014–2015)?
- **RQ6.** How well does the calibrated simulation reproduce the hospital's recorded waste, emergency purchases and weekday waste pattern in years it was not fitted to?

## 1.2 Foreknowledge of data or evidence (OSF required question)

**Answer (locked):** *"Authors have observed the data, but have not performed the proposed analyses."* The OSF wording reads in full: "At least some of the data that will be used for this analysis plan has been accessed and observed by the authors. The authors have sufficiently observed relevant evidence to influence their analysis decisions or conclusions. However, the authors have not yet performed any of the proposed analyses in this plan and will not do so until after this plan is registered."

This is accurate for the primary and secondary analyses as defined here, which use a calibrated simulation, the horizon-scaled cushion and the mixed model. None of them has been run. Two caveats are disclosed in Section 3.6:

1. Closely related **uncalibrated** versions of several secondary and sensitivity analyses have been run.
2. Forecast accuracy (MAE) on Aachen is already known. It is therefore reported as **descriptive only** and is not listed as a tested outcome.

The explanation box on OSF should be filled from Section 3.6 in full, including the table.

---

# 2. Research design

## 2.1 Study type

**Simulation study** (OSF option: "Using existing or synthetic data to assess performance of a model, mimic operation of an existing or proposed system…"). It is driven by real, public, historical daily usage. No people are studied. No randomisation of subjects takes place. Random numbers are used only inside the simulation, and their seeds are fixed (Section 2.6).

**Intention for causal interpretation.** "No causal relationship inferred" about real hospitals. Comparisons are between policies *inside a model*.

**Blinding.** No blinding is involved (OSF option 1). Additional safeguards are listed in Section 3.6.

## 2.2 Design overview (the order of work is part of the plan)

1. **Freeze inputs.** The SHA-256 fingerprints of the data, the existing forecast files and the current code are recorded in `paper/osf_prereg_input_hashes.txt` and attached to the registration.
2. **Write and test the new code on the synthetic teaching series only** (`data/SYNTHETIC_daily_platelet_demand.csv`, clearly labelled example data). The new code is the horizon-scaled cushion, the calibration loop, block-level outputs and the mixed model. A timing test on Aachen may run the **standing order only**.
3. **Calibrate** the simulation on Aachen 2009–2011 using the **standing order only** (Section 2.4).
4. **Validate** the chosen calibration on Aachen 2012–2018, again with the **standing order only**. Write and save a dated calibration report, including pass or fail against the criteria in Section 2.4.5, **before any forecast is run through the new simulation.**
5. **Run the primary and secondary comparisons** on Aachen 2012–2018 (Sections 4 and 5).
6. **Run the Stanford replication** (Section 2.5).
7. **Run the sensitivity analyses** (Section 5.2), then write up.

## 2.3 Policies compared (the "manipulated variables")

### 2.3.1 Forecasts

All Aachen forecasts are **reused unchanged** from the v9 analysis. No forecast model is refitted, retuned or added. Each forecast is made at the end of a day for days +1 to +4, using only data known that day.

| Label | Role | What it is | Source in project |
|---|---|---|---|
| **SO** | **Primary comparator** | Standing order: for each target day, the previous calendar year's mean use on that weekday (about 52 observations per weekday) | `scripts/09_reality_check.py::standing_order_fc` |
| WA4 | Secondary comparator | 4-week weekday average: mean of the same weekday over the past 4 weeks | `scripts/02_aachen_real_data.py` baselines |
| GB | Primary forecast | `HistGradientBoostingRegressor`, calendar/lag/holiday features, fixed settings, expanding window | `scripts/08_multiyear_test.py` (deterministic, fixed `random_state`) |
| dGB | Primary forecast | Detrended gradient boosting: forecasts the difference from the past-28-day mean, same settings | `results/m9/27_gb_detrended_forecasts_*.csv` |
| SARIMA | Primary forecast | Weekly seasonal ARIMA, order chosen by AIC from 4 pre-set candidates on earlier years only | `results/m6/12_sarima_forecasts_*.csv` |
| CB | Primary forecast | Chronos-Bolt small (`amazon/chronos-bolt-small`), as published, 512-day context, mean forecast, not fine-tuned | `results/m5/chronos_forecasts_2010-12-31_2018-12-30.csv` |
| LASSO, RNN | Reference only | The source authors' published 2- and 4-day forecasts (they used clinical inputs) | public data file |

A caveat on Chronos-Bolt: its training corpus is not public, and the Aachen file has been public since 2022, so it may have seen these data.

### 2.3.2 Ordering rules

All rules use the existing order-up-to logic in `scripts/lib_m4.py::simulate`. On each ordering day the order is: forecast use over the *n* days the order must cover, plus a safety cushion, minus units on hand, minus units already in transit (never negative). The lead time is 2 days, and issuing is oldest first.

- **R1, horizon-scaled cushion: PRIMARY rule (locked).** Cushion = *k* × σ_m(*n*). Here σ_m(*n*) is forecast *m*'s out-of-sample mean absolute error of *n*-day totals over the calendar year **before** the test year, and *n* is the number of days that order covers (2, 3 or 4, depending on the calendar). A 4-day weekend order therefore gets a cushion sized to 4-day errors. One *k* applies per forecast, year and simulation run. It is implemented with the existing `safety_daily` argument (a constant series per *n*).
- **R2, constant cushion (the v9 rule): secondary.** Cushion = *k* × σ_m(2) for every order.
- **R3, age-aware rule: secondary.** R1's cushion, plus `order_rule="expiry_aware"` (already in `lib_m4.py`). Units on hand or in transit that are projected, by oldest-first depletion against the point forecast, to expire before they can be used are not counted as stock. This rule was tried briefly in 2017–2018 under the v4-era simulation and did not help (Section 3.6). Here it is pre-declared and run across all years. If it cannot be run with the calibrated configuration (for example, it is not supported with pooled stock), that will be reported, not silently dropped.

**Why R1 is primary.** Both independent reviews (v7 M4, v8 M4) found that the constant cushion gives a 4-day weekend order the same margin as a 2-day order, so rankings partly reflect each forecast's bias by order type. R1 is the minimal fix. This choice was made **before** any R1 result exists.

**Cushion for the standing order in calibration year 2009.** σ needs the previous year's errors, and the standing order for 2008 would need 2007 data, which do not exist. For 2009 only, σ_SO(*n*) is therefore taken from 2009 itself. This does not affect matched results, because *k* is re-chosen to hit the target, but it is disclosed.

## 2.4 Simulation calibration (done before any forecast comparison)

### 2.4.1 Fixed parts (not calibrated)

The following are kept exactly as in v9:

- the 2-day lead time;
- oldest-first issuing;
- ABO/RhD shares and substitution order;
- an emergency purchase fills any gap;
- starting stock of 20 units;
- the one-week warm-up;
- scoring windows of 8 January to 18 December;
- 30 paired runs.

### 2.4.2 Calibration targets (recorded, from the public file, scoring windows only)

| Target | Definition | Calibration years 2009–2011 (pooled) | Validation years 2012–2018 (pooled) |
|---|---|---|---|
| **T1. Yearly waste** | 100 × wasted units ÷ units transfused | 8.25% | 9.74% |
| **T2. Emergency units per short day** | emergency units ÷ days with ≥1 emergency unit | 6.53 | 8.82 |
| **T3. Weekday waste distribution** | share of wasted units logged on each weekday, Monday to Sunday | 21.9, 12.9, 33.9, 14.8, 13.6, 1.8, 0.9% | 29.4, 19.4, 28.2, 13.2, 6.8, 1.0, 2.0% |

Recorded per-year values (scoring windows):

| Year | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 |
|---|---|---|---|---|---|---|---|---|---|---|
| Waste % | 11.55 | 8.78 | 5.57 | 7.62 | 6.45 | 11.03 | 8.57 | 12.91 | 9.07 | 12.30 |
| Short days | 25 | 26 | 40 | 40 | 31 | 21 | 38 | 35 | 42 | 31 |
| Emergency units per short day | 5.36 | 5.27 | 8.07 | 8.55 | 9.19 | 8.19 | 5.68 | 8.40 | 13.64 | 7.00 |

In every calibration and validation run, the cushion multiplier *k* is matched by interpolation (Section 4.1) so that simulated short days equal the recorded short days in that year.

### 2.4.3 Parameters allowed to vary (pre-declared grid)

| Parameter | Values | Why it might matter |
|---|---|---|
| C. Delivery calendar (days on which deliveries arrive; 2-day lead; each order covers the days until the next delivery) | Tue–Sat (documented); Mon–Fri; Mon–Sat; Tue–Sun; every day | The recorded weekday waste pattern fits no simulated calendar under v9 |
| L. Usable life on arrival {2, 3, 4 days}: shares p2, p3, and 1 − p2 − p3 | p2 ∈ {0, 0.10, 0.20}; p3 ∈ {0, 0.15, 0.30, 0.45, 0.60} | Only "4 days left" is sourced; the 70/30 split is an assumption |
| G. Expiry logging lag (affects only T3, the weekday share) | 0 days; +1 day; +2 days; "next Monday-to-Friday working day" | Almost no recorded waste falls on weekends, which suggests delayed logging |
| E. Demand clustering | unit-level demand (v9); patient episodes with mean 2 units; mean 4 units | Simulated emergencies are smaller than recorded ones (5 vs 8.8 units per short day) |
| S. Delivery shortfalls | none; 10% of delivery days filled 50–90% (v9); 25% of days filled 30–80% | Unknown in the record |

The grid is 5 × 15 × 4 × 3 × 3 = 2,700 combinations. The logging lag G is applied after simulation, so only 675 distinct simulations are needed per year. **Compute rule:** if the full grid at 30 runs would take more than 48 hours, every combination is first screened with 10 runs (seeds 1000–1009), and the 20 best by loss are re-run with all 30 runs, with the final choice made from those.

### 2.4.4 Fitting method

Calibration runs the **standing order only**, under the primary rule R1, with *k* matched per year and run to recorded short days. Pooled over 2009–2011 and averaged over runs, the loss is:

L = ((W_sim − 8.25) / 1.0)² + ((E_sim − 6.53) / 1.5)² + (TVD / 0.10)²

- W_sim is the pooled simulated waste in percent.
- E_sim is the pooled emergency units per short day.
- TVD = ½ Σ |simulated share − recorded share| over the 7 weekdays, after applying the logging lag.

The denominators (1 point, 1.5 units, 0.10) are the tolerances we consider "close enough". The combination with the lowest L is chosen.

**Tie rule:** among combinations with L within 5% of the minimum, choose the one with the fewest departures from the v9 base (Tue–Sat, p2 = 0, p3 = 0.30, no lag, unit demand, 10% shortfalls), then the lowest L.

**Calibration never looks at any forecast's performance.** The chosen combination, its loss and the full grid table are saved and time-stamped (file hash recorded) before step 5 of Section 2.2.

### 2.4.5 Validation and acceptance criteria (2012–2018, standing order only, R1, recorded short days)

| Criterion | Pass if |
|---|---|
| A1. Mean waste | pooled simulated waste within ±1.5 points of recorded 9.74% |
| A2. Emergency size | pooled emergency units per short day within ±25% of recorded 8.82 (6.6 to 11.0) |
| A3. Weekday pattern | TVD between simulated and recorded weekday waste shares ≤ 0.20 |
| A4 (descriptive, no pass/fail) | yearly correlation and mean absolute error between simulated and recorded waste; per-year emergency units |

- **Calibration passes** if A1, A2 and A3 all pass.
- **Whatever happens, the primary analysis runs on the chosen calibrated configuration.** If calibration fails, the paper will say so in the abstract. The primary result will then be described as "conditional on a simulation that failed pre-declared validation on [criteria]", and the v9 base configuration will be reported alongside as a sensitivity analysis.
- No further calibration rounds are allowed after validation has been seen, except as a labelled exploratory analysis.

## 2.5 Second site: Stanford public example data (replication, RQ5)

**Data.** The example dataset in Stanford's public `pip` R package (github.com/bnaras/pip, GPL-2 or later), which accompanies Guan et al., *PNAS* 2017 (doi:10.1073/pnas.1714097114). It has 880 days of daily platelet units transfused at two Stanford hospitals (about 35 a day), plus 35 standardised clinical covariates. It has no stock, expiry, order, blood-group or emergency data. Usage dates were established in milestone S2-1 as 2 January 2013 to 31 May 2015: each row's usage belongs to the day before its weekday label.

**Shelf-life and ordering rules.** These are unchanged from the S2-1 simulator, a Python port of the authors' `pip::compute_prediction_statistics` (`study2/scripts/lib_s2.py`):

- daily ordering;
- units decided on day *i* arrive on day *i* + 3 and are usable on that day and the next two (3 usable days);
- oldest first;
- unmet demand counted as shortage units and a shortage day;
- no blood groups, shortfalls or randomness;
- order-up-to: stock + pipeline = forecast of the next 3 days + a constant buffer *b*.

Every order covers the same horizon, so R1 and R2 coincide at this site. R3 is not run.

**Test window.** Scoring runs from **8 January 2014 to 31 May 2015** (509 days), with simulation starting 1 January 2014. This window is chosen because the standing order needs a full previous calendar year: 2013 for 2014, and 2014 for 2015.

**Forecasts.**

- Already produced in S2-1, reused unchanged with weekly retraining as in S2-1: SO (new to this site; previous-calendar-year weekday mean), WA4, SARIMA and GB without clinical data.
- **New runs with fixed settings declared here:** Chronos-Bolt (same model, mean forecast, all available history up to 512 days) and detrended GB (script 27 feature construction, S2-1 GB settings, weekly retraining).
- Reference only (secondary): the clinical models from S2-1 (Guan-style lasso, GB with clinical covariates, the Guan LP replication), using the "strict" timing.

**Matching target, primary (locked):** shortage on **1% of scored days, i.e. 5 days**. *b* is matched by linear interpolation between integer buffers (grid −40 to +80). Sensitivity targets: 0 days and 25 days (5%). Stanford has no recorded short-day series comparable to Aachen, so a recorded-short-day target cannot be used here.

**Primary analysis at Stanford.** Each of the 4 forecasts minus SO, for waste % (expired ÷ transfused × 100) at the matched point, with Holm correction across the 4. Inference is in Section 4.4.

**What counts as replication (per forecast):**

- **Replicated benefit:** Aachen shows a Holm-significant waste reduction against SO, and Stanford also shows a Holm-significant reduction.
- **Consistent null:** neither site shows a Holm-significant difference.
- **Discordant:** any other pattern, reported as such without choosing a favourite site.
- **Stanford's minimum meaningful difference (locked):** 6% of SO's Stanford waste at the matched point, in relative terms. Stanford waste levels (about 1–4%) are far below Aachen's, so 0.5 points absolute would be meaningless there. 6% matches 0.5 points on Aachen's roughly 8.5%.

## 2.6 Random numbers and seeds

- Aachen simulation: seeds 1000–1029 (`SEED0 = 1000`, 30 runs). These are common random numbers: every policy sees the same demand split, delivery shortfalls and shelf-life draws in run *s*.
- Bootstrap seeds: 20261114 (Aachen) and 20261115 (Stanford).
- Gradient boosting `random_state` is as in the existing code.
- Chronos-Bolt mean forecasts are deterministic.

---

# 3. Sampling (data)

## 3.1 Datasets used

1. **Aachen.** Daily platelet counts from University Hospital Aachen, 1 January 2008 to 31 December 2018 (4,018 days, no missing dates). Columns used: units transfused, units discarded as outdated, emergency purchases. Source: Multimedia Appendix 1 of Schilling et al., *JMIR Medical Informatics* 2022, released under CC BY 4.0. The source authors removed 305 mislabelled records (0.66%) before release.
2. **Stanford.** The `pip` package example data (Section 2.5), GPL-2 or later.

**Data availability:** both datasets are publicly available. **Identifiers:** see the SHA-256 manifest. Both are hospital-day totals with **no patient-level data**.

**Access dates (required by OSF; the author fills these in from his own records before registering).** Use the date you first downloaded each file for this project, not a later copy date on the shared box.

- Aachen public file first downloaded: 13 November 2026 (downloaded to the project computer by the author's AI assistant at the author's request)
- Stanford `pip` example data first downloaded: 13 November 2026 (downloaded to the project computer by the author's AI assistant at the author's request)

## 3.2 Data collection procedures

No new data are collected. No hospital system is contacted or connected, and no employer, patient-level or non-public data are used. The source authors will not be contacted as part of this plan.

## 3.3 Sample size

- **Aachen:** 7 test years, 2012–2018. Calibration uses 2009–2011, and 2008 provides the first standing order and history.
- **Stanford:** 509 scored days in 18 four-week blocks.

## 3.4 Sample size rationale

The sample size is fixed by the public data, not chosen. See the precision statement in Section 4.6.

## 3.5 Starting and stopping rules

None apply. All years and days are analysed once, as specified. There are no interim looks at forecast comparisons.

## 3.6 Prior knowledge of the data (honest disclosure)

This is a **secondary-data preregistration of analyses on data the author has already analysed extensively.** It cannot make the earlier study "preregistered". What it can do is fix the *new* calibration, rule, comparator and statistics before their results exist.

**Already seen on Aachen (2008–2018), across drafts v1 to v9 of an exploratory study (preprint planned on medRxiv, not yet posted at the time of drafting):**

- **Accuracy.** Forecast accuracy (MAE, bias, Diebold–Mariano tests) for all forecasts in this plan, at 1, 2 and 4 days, for every year. SARIMA had the lowest average error, and detrended GB removed most of GB's weekend under-forecast.
- **Primary-like results.** Waste, lost and emergency units at each year's recorded short days in the **uncalibrated** v9 simulation, under the constant cushion, against WA4. GB, CB and SARIMA each wasted less in 4 of 7 years (8.6%, 8.4%, 8.4% vs 8.9%), and no CI excluded zero.
- **Standing order (exploratory).** At the documented calendar it wasted 8.5%. SARIMA, CB and GB were within about 0.1 points of it (−0.10, −0.09, +0.09) at recorded short days, and about 0 at 20 short days a year. Under four other calendars, SARIMA was 0.28–0.41 points below it (CI excluded zero only for Mon–Sat).
- **Service targets (exploratory).** At 20 short days a year, SARIMA and CB wasted less than WA4 in all 7 years. At 50, no forecast won more than 4 of 7.
- **Delivery calendars (exploratory).** Five calendars were run. Calendars without a 4-day order roughly halved waste. **Tue–Sun came closest to the recorded Monday share of short days.** No calendar reproduced the recorded Wednesday waste peak or the size of emergencies.
- **Detrended GB (exploratory).** It was more accurate at 2 and 4 days, but wasted more than WA4 under the documented calendar (9.6%) and less with daily deliveries.
- **Reality check.** Standing order vs record: 8.5% vs 9.7% waste, correlation 0.47, single years from 2.0 points too high to 5.1 points too low. About 5 vs 8.8 emergency units per short day. Recorded weekday waste pattern: Wed 28%, Sat 1%, Sun 2%. A 43% share of 3-day units matched average waste.
- **Other sensitivity runs.** Life-on-arrival sweeps (0–100%), heavy shortfalls (all three forecasts beat WA4 in every year), no blood groups, patient episodes, a prior-year cushion, cost weights, a US-rules scenario for 2018, a day-by-day uncertainty cushion, and an **expiry-aware ordering rule tried in 2017–2018 only** (no help).
- **Recorded data.** The figures in Section 2.4.2 were computed from the public file while drafting this plan. They reproduce figures already reported in v9.

**Already seen on Stanford (milestone S2-1):**

- the row/date alignment;
- next-day and 3-day accuracy of WA4, SARIMA, GB with and without clinical data, Guan-style lasso and simple baselines, scored days 201–880 (about 21 July 2013 to 31 May 2015);
- a replication of Guan et al.'s LP (3.5% vs published 3.2% waste);
- simulated waste at 0, 2, 6 and 14 shortage days. The linear clinical models wasted least, and SARIMA wasted more than WA4 at zero shortage days but was about tied at a few short days.

The new Stanford window (8 January 2014 to 31 May 2015) lies inside that period, so aggregate waste for WA4, SARIMA and GB on most of it has been seen. **Not seen:** the standing order, Chronos-Bolt and detrended GB on Stanford, and any forecast-vs-standing-order comparison there.

**What is genuinely confirmatory, and what is not:**

| Element | Status |
|---|---|
| Calibration grid, loss, choice and validation result | Confirmatory in the sense that the procedure is fixed before running it. But the author already knows which calendars and life shares fit some targets better (for example Tue–Sun and the Monday share, or 43% short-life and average waste), so the *choice* is partly predictable. |
| H1a–d (forecast vs SO, calibrated simulation, R1, recorded short days) | **Confirmatory with partial foreknowledge.** No result exists for this combination. Under the uncalibrated v9 simulation and R2, the analogous gaps were about −0.1 to +0.1 points, and the author knows SARIMA kept a small edge under some non-documented calendars. If calibration selects such a calendar, a small SARIMA edge would be partly anticipated. |
| Stanford comparisons vs SO, especially CB and dGB | **Closest to genuinely confirmatory.** Never run. |
| Everything vs WA4, the 20 and 50 targets, calendars, life share, shortfalls | **Secondary/sensitivity**, with uncalibrated analogues already seen. |
| Forecast MAE on Aachen | **Already known.** Descriptive only. |

**Safeguards.**

1. New code is developed on the synthetic series.
2. Calibration uses only the standing order and is mechanical (fixed grid, loss and tie rule).
3. The calibration report is saved and fingerprinted before any forecast enters the new simulation.
4. The primary table is produced by one script that computes all four comparisons together, with no partial looks.
5. Every deviation is logged (Section 6).
6. The primary result is reported in the abstract whatever it shows.

## 3.7 Prior publication or dissemination

An exploratory manuscript (draft v9, "Do better forecasts reduce platelet waste? A simulation over seven test years of public data from a German university hospital") and its code are prepared, and a medRxiv preprint and a GitHub/Zenodo code release are planned. **Preprint DOI, if posted before registration:** not yet posted.

---

# 4. Analysis plan

## 4.1 Matching rule (how "matched shortage frequency" is computed)

For each policy, year and run, the simulation is run across *k* = 0 to 6 in steps of 0.25. Simulated short days fall as *k* rises. *k* is chosen by linear interpolation between the two grid points that bracket the target (the existing `lib_m5.match_at` logic), and every outcome is interpolated with the same weight.

- If the target is not reached at *k* = 6, the grid is extended to *k* = 10 for that policy and year.
- If simulated short days are already below the target at *k* = 0, the *k* = 0 values are used and flagged.
- Any run still unmatched is dropped, and the number dropped is reported per policy and year.

**Primary matching target, Aachen (locked):** each test year's **recorded short days** in the scoring window (2012–2018: 40, 31, 21, 38, 35, 42, 31). This continues the v9 primary outcome and ties the comparison to the hospital's own service level. A fixed target of **20 short days a year is a pre-declared sensitivity analysis**. A fixed 50 short days a year is an additional sensitivity, as in v9.

## 4.2 Outcomes and exact definitions

**Primary outcome.** W = 100 × (wasted units ÷ units transfused) in the scoring window (8 January to 18 December) of test year *y*, at the matched point, averaged over the 30 runs. "Wasted" means units that reach the end of their usable life unused. "Transfused" means the recorded daily demand.

**Primary contrast.** D_m,y = W_m,y − W_SO,y, in percentage points. Negative means forecast *m* wasted less than the standing order.

**Secondary outcomes** (each forecast vs SO, and vs WA4):

1. **Lost units** per year: wasted plus emergency units at the matched point.
2. **Emergency units** per year, and emergency units per short day.
3. **Trade-off summary.**
   - For each policy, year and run, waste % is interpolated at every integer short-day level from 20 to 50.
   - The summary is the **mean waste gap against SO across levels 20–50**, averaged over runs and then years. This equals the area between the two trade-off curves divided by the 30-level width.
   - Pooled curves (mean over years) will be plotted.
   - A level a policy cannot reach in a year is excluded for that year and policy pair, and the exclusion is reported.
4. **Waste at a fixed 20 short days a year (sensitivity)** and, as an additional sensitivity, at 50 short days a year.
5. **W under R2 and R3**, at recorded short days.
6. **Cost** = 350 × wasted + 700 × emergency units, using the data file's own weights.

**Descriptive only (already known, not tested):** forecast MAE at 1 day and for *n*-day totals, and bias by order type.

## 4.3 Statistical model, Aachen primary analysis

- **Unit of inference.** The test year is the cluster. Within each year, the scoring window is cut into **12 blocks**: blocks 1–11 are 28 days each starting 8 January, and block 12 runs from day 309 to 18 December (37–38 days).
- **Block outcome.** d_y,b = mean over runs of (block waste % for forecast *m* − block waste % for SO), using the same interpolation weights as the yearly match.
- **Model, fitted separately for each of the 4 comparisons:** linear mixed model d_y,b = μ + u_y + ε_y,b, with a random intercept u_y ~ N(0, τ²) per year and residual ε ~ N(0, σ²). It is fitted by REML with `statsmodels` `MixedLM.from_formula("d ~ 1", groups="year")`.
- **Estimate, CI and test.** μ̂ is the estimate. The 95% CI is μ̂ ± t(0.975, df = 6) × SE(μ̂). The two-sided *p* uses the *t* distribution with 6 degrees of freedom (7 years − 1), which is deliberately conservative.
- **Fallback (pre-declared).** If the mixed model fails to converge, or gives a singular-fit warning, the **year-level paired *t*-test** on the 7 yearly D_m,y (df = 6) is used for that comparison instead, and the substitution is reported.
- **Always also reported**, for continuity with v9: the 7-year mean of D_m,y (yearly %), its *t*-based 95% CI, the number of years lower out of 7, and exact sign and Wilcoxon signed-rank *p*-values.
- **Secondary precision check (not for inference).** A two-stage bootstrap: resample 7 years with replacement, then the 12 blocks within each sampled year with replacement, 10,000 times, seed 20261114. Percentile 95% CI. This method is known to give CIs that are too narrow with only 7 clusters, so it never replaces the primary CI.

## 4.4 Statistical model, Stanford

- d_b = block waste % for forecast *m* − block waste % for SO, over the 18 four-week blocks (the last block includes the 5 extra days). The simulation is deterministic, so there is no averaging over runs.
- **Primary:** mean of d_b, with a 95% CI from a **moving-block bootstrap** (blocks of 3 consecutive four-week blocks, 10,000 resamples, seed 20261115). The two-sided *p*-value is the share of centred bootstrap means (bootstrap mean minus observed mean) whose absolute value is at least the absolute observed mean. Holm correction across the 4 forecasts.
- **Also reported:** a *t*-interval over blocks, and the number of blocks lower out of 18.

## 4.5 Multiplicity

- **One family, pre-declared:** the 4 primary Aachen comparisons (H1a–d), with **Holm** correction at family-wise α = 0.05 (two-sided).
- The Stanford replication family (the same 4 comparisons) gets its own Holm correction.
- All secondary and sensitivity results are reported **without** adjustment and are labelled secondary or exploratory. They are never used to claim a confirmed effect.

## 4.6 Effect size, minimum meaningful difference and precision

- **Effect size:** μ, in percentage points of waste (units wasted per 100 transfused).
- **Minimum meaningful difference (MMD, locked): 0.5 points.** At Aachen's 2012–2018 volume (about 4,600 transfused per scoring window) this is about 23 units a year. It is roughly the size of the standing order's advantage over WA4 in v9 (0.45 points).
- **Precision statement.**
  - In v9, the between-year SD of yearly waste gaps against WA4 was 0.72–1.02 points (`results/m9/29_power.csv`). Gaps against SO are expected to be of similar size, but that has not been computed.
  - With 7 years, a *t*-based 95% CI has half-width 0.925 × SD, so about **0.67–0.94 points**.
  - For 80% power at α = 0.05, the true gap must be about 1.27 × SD (about 0.9–1.3 points). At the strictest Holm level (α = 0.0125) it must be about 1.72 × SD (about 1.2–1.8 points).
  - **Detecting a 0.5-point difference with 80% power would need a between-year SD of about 0.29–0.39 points**, which is unlikely.
  - The block-level mixed model uses within-year information, but with only 7 years the between-year variance will usually dominate. So **the primary analysis is expected to be inconclusive for differences near 0.5 points** unless gaps are unusually stable across years. This is stated in advance so that a null result is not over-read.

## 4.7 Inference criteria (applied to each primary comparison)

| Result label | Rule |
|---|---|
| **Waste reduction demonstrated** | Holm-adjusted *p* < 0.05 and μ̂ < 0 |
| …and **practically meaningful** | in addition, μ̂ ≤ −0.5 points |
| **Waste increase demonstrated** | Holm-adjusted *p* < 0.05 and μ̂ > 0 |
| **Practically equivalent** | the 90% CI (μ̂ ± t(0.95, 6) × SE) lies entirely within −0.5 to +0.5 points (two one-sided tests at α = 0.05 each; unadjusted, labelled as such) |
| **Not demonstrated (inconclusive)** | anything else. The report will say "a difference was not demonstrated; the data are compatible with differences from [lower CI] to [upper CI] points" and never "no difference" |

**Answer to RQ1:**

- "Yes" if at least one forecast meets *waste reduction demonstrated*.
- "No, and no forecast exceeds the MMD" only if all four are *practically equivalent* or show an increase.
- "Not demonstrated" otherwise.

## 4.8 Transformations

None. Waste is analysed on the percentage-point scale. Lost units and emergency units are on the unit scale.

## 4.9 Data inclusion and exclusion

All days in the scoring windows are included. There are no outlier exclusions. Unusually large days (for example, a recorded maximum of 39 units) are real demand and stay in. Simulation runs are excluded only under the unmatched-target rule (Section 4.1).

## 4.10 Missing data

- Aachen has no missing dates.
- Stanford is missing 1 January 2013 (outside the test window). No imputation.
- Any forecast missing for a needed origin (for example, at a year boundary) falls back to WA4 for that origin only. Every fallback is counted and reported.

## 4.11 Assumption checks

- Residual plots of the mixed model, and a check for autocorrelation between consecutive blocks within a year (lag-1 correlation reported).
- If the lag-1 correlation is above 0.3, the year-level *t*-test result is reported alongside as a check. The primary label still comes from the pre-declared model.

---

# 5. Variables (summary)

- **Manipulated (policy) variables:** the forecast (6 policies plus 2 references); the ordering rule (R1 primary, R2, R3); the matching target (recorded short days primary; 20 and 50 short days as sensitivity analyses).
- **Measured variables (simulated):** daily wasted units, emergency units, short days, stock; and the trade-off curve over *k*.
- **Measured variables (recorded):** daily units transfused (the demand driver), and recorded waste and emergency purchases (calibration and validation only).
- **Indices:** waste %; lost units; emergency units per short day; TVD of the weekday waste distribution; the 20–50 trade-off summary; cost.

## 5.1 Secondary analyses (listed so they are not mistaken for confirmatory)

1. RQ2: each forecast vs WA4, primary outcome, calibrated simulation, R1.
2. RQ3: the trade-off summary (mean waste gap against SO across levels 20–50), vs SO and vs WA4. Waste at the single fixed points of 20 and 50 short days is reported as a sensitivity analysis (Section 5.2).
3. RQ4: R2 and R3 versions of the primary analysis.
4. RQ6: the calibration validation (A1–A4), plus per-year simulated vs recorded waste.
5. Lost units, emergency units and cost, vs SO and vs WA4.
6. The LASSO and RNN reference forecasts vs SO, 2- and 4-day orders only (as in v9).

## 5.2 Sensitivity analyses (all secondary; primary comparator, R1, recorded short days unless stated)

1. **v9 base configuration** (uncalibrated: Tue–Sat, 70/30 life split, 10% shortfalls), with R1.
2. **Delivery calendars:** each of the 4 calendars not chosen by calibration, with other calibrated parameters held fixed.
3. **Life on arrival:** p3 = 0.30 and 0.43 (the plausible range from v9), and an extreme sweep p3 = 0 to 1 in steps of 0.1, with p2 fixed at the calibrated value.
4. **Delivery shortfalls:** none; 10% (50–90% filled); heavy 25% (30–80% filled).
5. **No blood groups** (pooled stock); patient episodes with mean 2 units.
6. **Cushion chosen in advance:** each policy's *k* is set to match the *previous* year's recorded short days, then held for the test year. Short days are then not matched, and both waste and short days are reported.
7. **Fixed shortage targets (Aachen):** waste at 20 short days a year (the pre-declared sensitivity) and at 50 short days a year, vs SO and vs WA4, under R1.
8. **Stanford:** targets of 0 and 25 short days; clinical models with "pip" and "strict" timing.

## 5.3 Optional exploratory national-level check (not confirmatory; not a third site)

NHS Blood and Transplant (NHSBT) publishes open monthly counts of platelet units issued to hospitals in England (April 2016 to October 2025 at the time of writing this plan; https://www.nhsbt.nhs.uk/who-we-are/transparency/parliamentary-questions/). This is a national supplier-issue series, not daily demand at one hospital, and it has no stock, expiry, order or shortage data.

If this series is used at all, it will be labelled **exploratory, not confirmatory**, and will be limited to a descriptive national-level check (for example, whether national monthly issues show trend or seasonal features worth mentioning as context). It will not be used as a primary or secondary site, will not enter the mixed model or the Holm family, and will not be used to confirm or overturn H1a–d. The hospital inventory simulation in this plan will not be run on this series, because the required daily hospital demand and inventory fields are not in the file.

**Access date, if the file is used:** not yet downloaded; the date will be recorded at first download and reported in the paper.

---

# 6. Deviations policy, reporting and timeline

**Deviations.**

- Any change to this plan after registration is recorded in a dated **deviations table** in the paper and supplement, and as an **OSF Update** to the registration, with the reason, the date, and whether it was made before or after the primary results were seen.
- **Bugs found after results:** fix them, then report both the original and the corrected results, and state which is primary. A bug fix does not count as a deviation if it makes the code do what this plan says.
- **Changes that are never allowed after primary results are seen:** the primary comparator, outcome, matching target, ordering rule, model or multiplicity correction.
- If something in this plan proves impossible (for example, compute limits), the closest feasible version is run and labelled as a deviation.

**Reporting of null or unfavourable results.**

- The primary result (all four comparisons, with μ̂, 95% CI, Holm-adjusted *p* and the inference label) goes in the abstract, whatever it shows.
- Calibration failure, if it happens, also goes in the abstract.
- Secondary results that look better than the primary cannot replace it in the title, abstract or conclusion.
- Results that contradict v9 will be stated plainly, with both versions cited.
- All result files and code will be released (MIT licence; data under their own licences).

**Timeline (target; actual dates logged).**

| Step | Target |
|---|---|
| Register this plan (Liam, on osf.io) | Week 0 |
| Write and test new code on synthetic data; timing test with SO only | Weeks 1–2 |
| Calibration on 2009–2011 (SO only); save the report | Week 3 |
| Validation on 2012–2018 (SO only); save the report | Week 3 |
| Primary and secondary comparisons, Aachen | Week 4 |
| Stanford replication | Weeks 5–6 |
| Sensitivity analyses; write-up; cut to the journal word limit | Weeks 6–9 |

---

# 7. Analyses NOT planned (anything like this will be labelled exploratory)

- Refitting, retuning or adding forecast models, or new features. This includes clinical covariates for Aachen, which are not in the public file.
- Choosing any matching target, calendar, cushion rule or statistic *after* seeing the comparisons.
- A further calibration round after validation has been seen.
- Per-year highlighting ("best year") as evidence.
- Cold-stored platelets; the US-rules scenario; changes to ABO/RhD rules beyond v9.
- Other public series in the project folder (Japanese supply data, Hamilton summaries). These are not part of this plan.
- NHSBT monthly platelet issues may be used only as the labelled exploratory national-level check in Section 5.3. They are not a primary or secondary analysis and not a third site.
- Any use of non-public, employer or patient-level data, or contact with any hospital system. **These are never allowed, exploratory or not.**
- Any claim about real-world savings at any hospital. The simulation is a model.

Any analysis not listed in Sections 4 and 5 will be labelled "exploratory, not preregistered" wherever it appears.

---

# 8. Other: context

- **AI assistance.** An AI assistant helped draft this plan and the analysis code. The author reviewed and takes responsibility for every decision.
- **Ethics.** Public, de-identified, aggregate data only. No human participants.
- **Visibility.** Register this plan as **public immediately, with no embargo**.
- **Attachments to upload with the registration:**
  1. this file (PDF or DOCX);
  2. `paper/osf_prereg_input_hashes.txt`;
  3. optionally, preprint draft v9 as background, clearly labelled as the exploratory study.
