# Changes from pre-registration draft v1 to v2

This file maps every item in `review_prereg_draft.md` (Required R1–R6, Recommended M1–M15, Optional O1–O7, and the reference notes) to what was changed in `osf_prereg_study2_draft_v2.md`, or to a reason for skipping it. Version 1 is unchanged at `osf_prereg_study2_draft.md`. Nothing has been posted to OSF. No model has been fitted or scored on the NHSBT issues series.

Date: 18 November 2026 (America/New_York).

---

## Required items (all six fixed)

### R1 — Block bootstrap, with the block length stated

**Review:** a month-by-month bootstrap ignores that forecast errors come in runs; state the block length.

**Fix in v2 (Uncertainty section):** non-circular overlapping moving-block bootstrap. Block length is 3 months at the one-month horizon and *h* + 2 months at horizon *h*. 10,000 resamples, seed 20261118, paired for differences (same resampled target months). Implemented in `inference.py` (`block_length`, `moving_block_indices`, `block_bootstrap_mae`, `block_bootstrap_mae_diff`).

### R2 — Diebold–Mariano: exact lag/HAC rule and Harvey–Leybourne–Newbold correction

**Review:** the lag used in the HAC variance and a small-sample correction were not stated.

**Fix in v2 (Uncertainty section):** two-sided DM on absolute-error loss; Newey–West variance with *h* − 1 lags (lag 0 at one month); Harvey–Leybourne–Newbold (1997) correction \(DM^* = DM\sqrt{(n+1-2h+h(h-1)/n)/n}\), compared with *t*_{*n*−1}. If the variance is not a positive finite number, report “test not computable” and treat the comparison as “could not tell them apart.” Implemented in `inference.py` (`diebold_mariano_hln`). Harvey et al. 1997 is now in the reference list (doi:10.1016/S0169-2070(96)00719-4; this is the standard citation for that paper; the 1997 article itself was not re-opened in this pass).

### R3 — Holm-correct the 3 primary tests; label everything else descriptive

**Review:** many comparisons were planned (methods × horizons × products, plus sensitivities and secondary metrics) without a correction or a clear “descriptive only” label.

**Fix in v2 (Uncertainty section):** only three confirmatory tests — ETS, SARIMA, and the calendar regression, each versus seasonal naive, at the one-month horizon, on platelet units per day. Those three DM p-values are Holm-corrected at 5%. A “winner” is declared only if the Holm-corrected test is significant *and* the block-bootstrap CI for the MAE difference excludes 0. Two- and three-month horizons, secondary products, secondary metrics, and all sensitivities are labelled descriptive; no “significant” or “better” wording and no winner from them. The plan notes that it produces well over 100 numerical comparisons.

### R4 — Define SARIMA non-convergence precisely, plus a fallback with a constant

**Review:** “if it does not converge, a reserved fallback” was too vague, and a no-constant fallback of (1,0,1)(1,0,1)12 would forecast toward zero.

**Fix in v2 (Methods):** failure = exception, or a `ConvergenceWarning` / warning whose message mentions convergence, or a non-finite forecast, or `mle_retvals['success']` is False. Fallback, that origin only: (1,0,1)(1,0,1)12 **with a constant** (`trend='c'`). The constant is required because the fallback is not differenced. Fallback count will be reported. Warnings are logged, not silenced. Implemented in `inference.py` (`fit_sarima_primary`).

### R5 — Choose one ETS specification and state the trend explicitly

**Review:** “standard ETS / Holt–Winters with additive season, period 12” left the trend unspecified.

**Fix in v2 (Methods):** one specification — **no trend** (level plus additive season only; not textbook Holt–Winters with a trend), `seasonal='add'`, period 12, `initialization_method='estimated'`, fitted by minimising SSE with `statsmodels.tsa.holtwinters.ExponentialSmoothing.fit(optimized=True)`. The draft no longer says this class is fitted by maximum likelihood (it is not). If it fails, that origin is omitted for ETS; no other ETS form is substituted. For the COVID sensitivity only, the equivalent state-space ETS class is used because `holtwinters` cannot accept missing values; that software difference is disclosed. Implemented in `inference.py` (`fit_ets_primary`) and in the COVID-sensitivity path of `nhsbt_analysis.py`.

### R6 — Exact COVID-removal procedure, and the seasonal-naive Nov–Dec 2022 issue

**Review:** “treat those months as missing” was incomplete; seasonal naive for Nov and Dec 2022 would otherwise use Nov and Dec 2021 (inside the COVID window).

**Fix in v2 (COVID rule):** primary analysis does not drop, dummy, or interpolate March 2020–December 2021, and it states that seasonal naive for November and December 2022 is simply November and December 2021. The sensitivity: ETS and SARIMA treat those months as missing (calendar left in place); the regression drops those training rows; seasonal naive uses the most recent same calendar month outside the COVID window (November and December **2019** for the first two test months). The COVID window will not be redefined after looking at residuals.

---

## Recommended items applied

### M1 — Smallest meaningful difference

Applied. Set at **7 platelet units a day** (~1% of typical daily national issues), as a planning judgement, not from test-period errors. The already-disclosed 115-month descriptive mean of about 682 units a day is cited as the scale.

### M2 — Red-cell April 2024 shift: when it may enter the regression

Applied. The shift is added only once at least three months after April 2024 are in the training window (origins whose training data include July 2024 or later). The no-shift red-cell regression is always reported as well. The pre-specified April 2024 start for a red-cell sensitivity, and the pre/post split, are unchanged from v1 and restated.

### M3 — Sensitivity dropping September and October 2025 as scoring targets

Applied. These two months fall outside the sheet title and may be provisional; they are the last two one-step test months. The sensitivity is listed among the descriptive checks.

### M4 — Drop “replication”; use “extension”

Applied. Title, prior-work section, and wording now call the study an **extension** of Nandi et al. (2020), not a replication. The changes in product, time grain, period, and methods are stated.

### M5–M7 — Reference notes (units, tuning, Ejohwomu, missing DOIs)

Applied; see “Reference notes” below.

### M8 — Affiliation

Applied. Public affiliation is “Independent researcher.” “Platelet Forecast Lab” is not used as an affiliation in v2.

### M9 — Brazil forecasts existed before the plan was finalised

Applied, in Methods and in “Datasets already examined.” The Brazil exploratory forecasts ran before this pre-registration was finalised and did not tune the confirmatory methods. The draft also explains why a calendar regression replaced an earlier suggestion of a 12-month seasonal average (a close cousin of seasonal naive; the regression uses the whole training window’s month effects, a linear trend, and, for red cells, the April 2024 shift). That swap was not a response to the Brazil errors.

### M10 — Expanding window, not a fixed-length rolling window

Applied. The Train/test section now says “expanding-window” explicitly and contrasts it with a fixed-length rolling window.

### M11 — Per-day scaling does not fix weekdays, bank holidays, or Easter

Applied. Metrics and Limits now state this remaining calendar limitation, and that it also affects the seasonal naive baseline.

### M12–M14 — Brazil exploratory write-up

Applied in `study2/brazil_exploratory/README.md` and, for M14, as a footnote on the panel chart. See the Brazil section below. These were not pre-registration text changes.

### M15 — Name the software and a seed; hash a synthetic-tested analysis script

Applied. Software: Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1. Seed 20261118. Scripts, tested only on made-up data (`nhsbt_analysis.py --synthetic-test`), with SHA-256:

- `study2/prereg/inference.py`: `6d55e1b1acfd17a5c6511c98080ff1480fb2bf66dd20d53e3e5ba313c6cb9416`
- `study2/prereg/nhsbt_analysis.py`: `0f429756f03ac9362f87e75eecd554ca7a5bee48f83ac518ff7e2b571268a30d`

Running `nhsbt_analysis.py --nhsbt` refuses and does not open the workbook.

---

## Optional items

### O1 — Reword why MAPE is secondary

Applied. MAPE is secondary because the primary decision is in units, not percentages. On this series, MAPE of the per-day rates equals MAPE of the monthly totals, and the per-day values stay well above zero.

### O2 — If seasonal naive is reliably better, say so

Applied. Methods and Uncertainty now say that if the primary tests and the interval both show seasonal naive was better, that will be stated plainly.

### O3 — When the official file was first downloaded

Applied. First downloaded on 18 November 2026 for scouting; the dated snapshot was saved later the same day, before any model was fitted. A later live download of the official URL matched the snapshot hash.

### O4 — Extract-date versus “Period Covered” mismatch, and the `#VALUE!` cell

Applied. Noted in the Primary series section as signs of a hand-assembled file. The dated snapshot will be analysed as it stands.

### O5 — Confirm the gitignore in the real repository clone

Partly applied, and listed as a remaining check. The project `.gitignore` already lists `study2/data/public/` and `private_data/`. This box working copy at `/workspace/platelet-forecast` is **not itself a git repository**, so the ignore rule could not be verified with `git check-ignore` here. v2 states that the rule should be checked in the real clone before any push. **Skipped as a completed verification, with that reason.**

### O6 — Brazil city-name check (São Paulo das Missões)

Applied in the Brazil README and in the exploratory script output: 0 rows named “São Paulo” or “Rio de Janeiro”; 6 rows named “São Paulo das Missões” (a small town in Rio Grande do Sul). The check is by city name because there is no state column.

### O7 — `/tmp` copies of Brazil / survey files

**Skipped.** The reviewer noted leftover copies and did not ask that they be deleted. This task also did not ask for deletion. They were left alone.

---

## Reference notes

### Nandi 2020 — units, tuning, and a non-comparable error measure

v1 had implied a 4-weekly-totals framing and had not flagged the tuning or the error measure. v2 now states that Nandi, Roberts and Nandi used daily aggregates from 2005 to 2011, derived **average weekly issues over 4-week periods**, and **tuned window size and model order**. Their reported figure is a standard deviation of the percentage error (3.0% at 4 weeks, 4.0% at 24 weeks). **That measure cannot be compared directly with this study’s MAE.**

### Ejohwomu 2021 — a stock simulation whose data are not public

v2 now describes it as a simulation of platelet stock at UK Stock Holding Units (agent-based and discrete-event), not a forecasting-method comparison. The data, “collected from typical UK SHUs,” are not public. A free author copy of the paper does not make the data open.

### Four (in fact five cited works plus the correction paper) missing or incomplete DOIs, each checked, none invented

DOIs were checked on 18 November 2026 against Crossref (and, for Azlin, the journal page). Added or completed:

| Work | DOI | Note |
| --- | --- | --- |
| Ejohwomu, Too and Edwards 2021 | 10.1080/17509653.2021.1892548 | Verified. |
| Turkulainen, Wemelsfelder, Janssen and Arvas 2022 | 10.1111/trf.16870 | Verified. |
| Azlin and Nor 2026 | 10.30880/ekst.2026.06.01.049 | Verified. Crossref lists only Azlin; the journal page lists Azlin & Nor. Cited as the journal page does, with this DOI. |
| Schilling, Rickmann, Hutschenreuter and Spreckelsen 2022 | 10.2196/29978 | Verified; was missing as a formal reference in v1. |
| Guan et al. 2017 | 10.1073/pnas.1714097114 | Verified; was missing as a formal reference in v1. |

Nandi 2020 (10.1111/trf.15705) was already known and is restated. Flint 2020 (Flint, McQuilten, Irwin, Rushford, Haysom and Wood, *Transfus Med Rev* 2020;34(1):42–50, 10.1016/j.tmrv.2019.08.006) is used in the Brazil README for the outdate-rate sentence (M13) and is not a main pre-reg reference. Harvey, Leybourne and Newbold 1997 (10.1016/S0169-2070(96)00719-4) was added because v2 now uses that correction; the 1997 article was not re-opened in this pass, and that is disclosed in the v2 reference list.

The Stanford `pip` commit is given as `6834939381870116f544e6b6fde6b92566c986f7` (https://github.com/bnaras/pip).

---

## Brazil exploratory work (not part of the confirmatory pre-registration)

Code in `study2/brazil_exploratory/aggregate_and_forecast.py` now uses `study2/prereg/inference.py` for the block bootstrap, the HLN-corrected Diebold–Mariano test, the SARIMA fallback with a constant, and the explicit ETS trend (none). The analysis was rerun. Point MAEs for seasonal naive and ETS were unchanged. SARIMA point MAEs changed because 3 of 33 origins used the fallback (30 primary, 3 fallback; 3 `ConvergenceWarning`s). After the new uncertainty methods, the honest conclusion is still that the methods could not be told apart on this short series (12, 11 and 10 points). See the updated `study2/brazil_exploratory/README.md`.

- **M12 (conflicting tests):** the v1 conflict (plain bootstrap CI included 0, uncorrected DM *p* = 0.01 for SARIMA vs naive at horizon 2 on transfusions) is gone under the new rules (HLN *p* = 0.592, block-bootstrap CI includes 0). New conflicts appear for ETS vs naive at horizons 2 and 3 on transfusions: the block-bootstrap CI excludes 0 but the HLN *p*-values are 0.180 and 0.225. With 10–12 points, neither test is very reliable; disagreement is treated as “couldn’t tell them apart.” One descriptive expiry comparison (SARIMA vs naive, horizon 3) has both the interval and the HLN test pointing the same way (SARIMA looked worse); it is still not a confirmatory claim.
- **M13:** the “10–20% outdate rates” sentence is now sourced to Flint, McQuilten, Irwin, Rushford, Haysom and Wood, *Transfusion Medicine Reviews* 2020;34(1):42–50, doi:10.1016/j.tmrv.2019.08.006 (abstract: “frequently reported at 10% to 20%”), not left unsourced. *[Corrected after review 2: this line first gave invented co-authors, pages 42–58 and a paraphrase as a quote; see `changes_v2_to_v3.md`, N4.]*
- **M14:** the README and the panel-chart footnote now say that the monthly-totals chart needs a licensing check before any public use, because the source is CC BY-ND 3.0.

The Brazil analysis itself was not pre-registered. No row-level Brazil data were written into a public file.

---

## Items not fully fixed, or skipped

- **O5 (complete gitignore verification):** cannot be finished on this box, because `/workspace/platelet-forecast` is not a git repository. Flagged in v2 and here.
- **O7 (`/tmp` leftover files):** skipped; deletion was not requested.
- **Human review:** still needed. An AI revision of the draft does not replace a statistician (especially for the bootstrap and Diebold–Mariano details), a transfusion-medicine specialist, or a licensing review. That caveat remains in v2.
- **Not done, by design:** the pre-registration has not been posted; no model has been run on the NHSBT issues series.

---

## File paths

- Kept unchanged: `/workspace/platelet-forecast/study2/prereg/osf_prereg_study2_draft.md` (v1)
- New: `/workspace/platelet-forecast/study2/prereg/osf_prereg_study2_draft_v2.md`
- New: `/workspace/platelet-forecast/study2/prereg/changes_v1_to_v2.md` (this file)
- New: `/workspace/platelet-forecast/study2/prereg/inference.py`
- New: `/workspace/platelet-forecast/study2/prereg/nhsbt_analysis.py`
- Updated: `/workspace/platelet-forecast/study2/brazil_exploratory/aggregate_and_forecast.py`
- Updated: `/workspace/platelet-forecast/study2/brazil_exploratory/README.md`
- Charts rewritten (same paths; panel chart now carries the licensing footnote): `/workspace/platelet-forecast/study2/brazil_exploratory/chart_reporting_coverage.png`, `/workspace/platelet-forecast/study2/brazil_exploratory/chart_panel_transfusions_expiry.png`
