# OSF pre-registration draft — Study 2

**Status:** DRAFT ONLY. This document has not been posted to OSF or anywhere else. No forecasting model has been fitted or scored on the NHSBT issues series. Looking at the file structure (date range, gaps, and how values are written) was allowed and is described below.

**Date of this draft:** 18 November 2026 (America/New_York)

**Public affiliation:** Independent researcher. Educational, advisory-only project (Platelet Forecast Lab). Not clinical advice, and nothing here will be deployed as an ordering tool.

**Data rule:** public data only. No employer, hospital-system or vendor data. No patient-level files and no credentialed clinical databases.

---

## Title

Forecasting monthly platelet issues from a national blood service in England, 2016–2025: a pre-registered comparison of simple seasonal methods

## Primary research question

For national monthly platelet units issued to hospitals in England from April 2016 to October 2025, do pre-specified standard statistical models (ETS, SARIMA, and at most one calendar regression) forecast one to three months ahead more accurately than a calendar-fair seasonal naive baseline?

This is a **national blood-service supply-planning** question. It is about the total number of platelet components the national supplier issued to hospitals each month. It is not a hospital daily ordering question, and the results will not tell any hospital how many platelets to order.

---

## Primary series

- **What:** monthly platelet units issued to hospitals by NHS Blood and Transplant (NHSBT), England.
- **Where in the file:** workbook sheet "Blood Products Issued by Month," column "Platelets."
- **Span:** April 2016 to October 2025, **115 months, no gaps.** (The sheet title and the data notes say "April 2016 – August 2025," but the rows run through October 2025. We will use all 115 months as published.)
- **Source (official, no account):** the Parliamentary Questions transparency page, https://www.nhsbt.nhs.uk/who-we-are/transparency/parliamentary-questions/, file https://nhsbtdbe.blob.core.windows.net/umbraco-assets-corp/40021/blood-donation-appointments-available-products-issued-and-meeting-ro-demand-2016-2025.xlsx
- **NHSBT extract date printed in the file:** 12 November 2025.
- **Unit definition:** the data notes describe this column as the "Number of blood components issued to hospitals, by month." They do not print a clearer definition (for example adult dose versus pack). All 115 platelet figures fall on a quarter-unit grid (for example 21,337.75), which is consistent with fractional adult-dose counting, but we will not convert or re-round the published numbers. We will analyse them as they stand.
- **What this series is not:** it is not daily hospital demand, not a single hospital, not inventory, and not recorded expiry or waste. We will not run a waste or shortage simulation on these data, because neither waste nor shortage is recorded.

### Dated snapshot and hash

A dated copy of the official workbook was saved on 18 November 2026 (America/New_York), before any model was fitted, at a gitignored path:

`study2/data/public/NHSBT_issues_2016-2025_snapshot_2026-11-18.xlsx`

SHA-256:

`f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696`

The folder `study2/data/public/` is listed in the project `.gitignore`. NHSBT has printed no open licence on the file or the landing page, and figures may later be revised. The snapshot is kept so that the analysis can be tied to a known extract. **The spreadsheet will not be redistributed.** Results, error tables and figures may be reported; the file itself will not be placed in a public repository, preprint or supplement. If a public data deposit is wanted later, that is a request for NHSBT to make, not something this draft assumes.

### Looking at the file structure (not modelling)

Only the following descriptive checks have been made on this snapshot, plus earlier scouting counts and a reviewer's own descriptive look (counts and yearly averages). No forecast has been produced.

- 115 months, April 2016–October 2025, no calendar gaps.
- Platelets: all 115 values lie on a quarter-unit grid; 88 of them are not whole numbers, from the first month onwards.
- Red cells: 15 of 115 months are not whole numbers, beginning in April 2024. May–August 2024 happen to be whole numbers again; every month from September 2024 through October 2025 is fractional. This is treated as a possible change in how red cells were counted (see below). It does not change the primary platelet series.
- Fresh frozen plasma and cryoprecipitate also include some fractional months, starting in 2020. They are secondary series only.

---

## Secondary series (to be reported whatever they show)

The same workbook, same 115 months, will also be used for:

1. Red blood cells issued to hospitals.
2. Fresh frozen plasma issued to hospitals.
3. Cryoprecipitate issued to hospitals.

These are pre-specified secondary analyses, not a hunt for a product where a model looks better. Every method, horizon and metric listed below will be reported for each product, including results that favour the baseline.

### The April 2024 red-cell counting change

Even though the primary series is platelets, we note a change in how red-cell issues are written from April 2024. NHSBT also warns that "metric definitions, methodologies, and reported values could be revised." For the secondary red-cell analysis we pre-specify:

- The primary red-cell evaluation uses the same origins and horizons as the platelet analysis.
- The calendar regression (see methods) will include a pre-specified level-shift indicator from April 2024 onwards, for red cells only.
- A pre-specified sensitivity will start the red-cell test period at April 2024, so that all scored red-cell months use the later counting style. That shortens the red-cell test window, and we will say so.
- We will also split red-cell errors into months before April 2024 and months from April 2024 on, and report both. We will not choose this split after seeing the results.

---

## Train/test split and evaluation

- **Fixed rolling-origin evaluation** over the last 36 months of the series (November 2022 to October 2025).
- At the end of each month *t*, models are fitted only on data up to *t* and then forecast *t*+1, *t*+2 and *t*+3.
- Origins that support all three horizons and still land inside the series run from the end of October 2022 through the end of July 2025 (34 origins). One-month-ahead scores will also be reported for the two later origins that can still be scored (August and September 2025), giving 36 one-step forecasts.
- The first training window therefore has 79 months (April 2016 to October 2022), about 6½ seasonal cycles, one of them covering the COVID period. That is enough for the short method list below. It is **not** enough to train gradient boosting, deep learning, or a large machine-learning model fairly, and those methods will not be used.
- Models are refit at every origin, using only past data.

Sample size will be stated in the abstract and the limits section: **115 monthly points, 36 in the one-month-ahead test window (34 origins for the three-month horizon).**

---

## Horizons

Primary horizon: **1 month ahead.**

Also reported, always: **2 months ahead** and **3 months ahead.** These are the horizons that matter for national collection and supply planning, not for next-day hospital ordering.

---

## Metrics

- **Primary metric:** mean absolute error (MAE) of **units per day.** Each month's issued total is divided by the number of days in that month (including leap days) before errors are computed. This stops February from looking like a "demand dip" that a model can take credit for catching.
- **Secondary metrics:** MAE of the raw monthly totals; root mean squared error (RMSE) of the units-per-day series; mean absolute percentage error (MAPE) of the units-per-day series. MAPE is secondary only, because it can be pulled around by a few unusual months.

We will not add further error measures after seeing the results.

---

## Methods (fixed, short list)

All methods are fitted on the units-per-day series, then compared on that scale. The method list is closed.

1. **Seasonal naive (the calendar-fair baseline).** The forecast for a month is the units-per-day value from the same calendar month one year earlier. For a two- or three-month horizon, the forecast is the units-per-day value from 12 months before the target month, using only data available at the origin. This already respects month length because the series is on a per-day scale.

2. **ETS.** Additive Holt–Winters exponential smoothing with a seasonal period of 12, estimated on the training window only at each origin. If this specification fails to estimate at an origin, that failure is recorded and that origin is omitted for ETS, not replaced with a different specification chosen after seeing the error.

3. **SARIMA.** Pre-specified order (0,1,1)(0,1,1)12, estimated on the training window only. If that specification fails to converge at an origin, the only reserved fallback is (1,0,1)(1,0,1)12. No other orders will be tried, and we will not search a larger grid after seeing test errors.

4. **At most one regression:** a linear calendar regression of units per day on 11 month indicators and a linear time trend, estimated on the training window only. For the secondary red-cell series only, this regression also includes the pre-specified April 2024 level shift. No other regressors, and no machine-learning models.

We will report every method at every horizon, including when the baseline is as good as or better than the others.

---

## COVID rule (pre-specified)

The COVID-affected window is **March 2020 through December 2021** inclusive. This window sits entirely inside the training history of the primary evaluation (the scored months start in November 2022). We will not drop, dummy out, winsorize, or interpolate those months in the primary analysis. Models see them as ordinary history.

A pre-specified sensitivity, reported but not used to pick a winner, will refit every method after excluding March 2020–December 2021 from the training windows, and will say whether the ranking of methods changes.

We will not redefine the COVID window after looking at residuals.

---

## Uncertainty and how a "winner" is (and is not) declared

For the primary comparison — each of ETS, SARIMA and the calendar regression versus seasonal naive, at the one-month horizon, on platelet units per day — we will report:

- MAE for each method, with a 95% bootstrap confidence interval;
- the difference in MAE versus seasonal naive, with a 95% bootstrap confidence interval;
- a two-sided Diebold–Mariano test on absolute-error loss, with a lag consistent with the forecast horizon.

**If the interval for the difference includes zero, or if the Diebold–Mariano test is not significant at 5%, we will say that we could not tell the methods apart.** We will not declare a winner from a small point-estimate gap. Thirty-six one-step errors from a smooth monthly series are correlated, so this outcome is likely, and we will treat it as an honest result rather than a problem to be fixed by trying more models.

The same rule will be used for secondary products and for the two- and three-month horizons.

---

## Prior work, and how this study is an extension

Nandi, Roberts and Nandi, *Transfusion* 2020;60(3):535–543, doi:10.1111/trf.15705, already forecast NHSBT **red-cell** issues. They used daily aggregates from 2005 to 2011, rolled them up to weekly and 4-weekly totals, and found that four simple linear methods gave "very similar results" (public abstract: standard deviation of the percentage error of 3.0% at 4 weeks and 4.0% at 24 weeks).

The present study is an **extension and replication**, not a first look at NHSBT issues. What is different is the product (platelets rather than red cells), the later period (2016–2025, which includes COVID), a monthly calendar that a national service actually plans around, a calendar-fair seasonal naive baseline, and a plan that is written down before any model is fitted. The contribution is modest and will be described that way. Ejohwomu, Too and Edwards (2021) is a related open UK stock-holding-unit study and will be cited; it is not the same series.

---

## Datasets already examined, and models already run

This list is here so that Study 2 is not a silent hunt across products and countries. None of the following changes the primary question above.

**Already used for modelling in this project (not the Study 2 confirmatory series):**

- University Hospital Aachen daily platelet transfusions, purchases and recorded waste, 2008–2018 (CC BY 4.0). Used in Study 1. Advanced models did not reliably beat simple baselines on that daily hospital series.
- Stanford `pip` example data: daily platelet use at two hospitals combined, 2013–2015, with clinical-driver columns (GPL 2 or later). Used in Study 1 and again in Study 2 milestones S2-1 to S2-10. On that series, SARIMA beat a weekday average on next-day MAE in 22 of 24 four-week windows; a Guan-style lasso that used laboratory and census features was close on accuracy and looked better in a *simulated* waste comparison; gradient boosting and Chronos were also run. There is no recorded waste in the Stanford file; waste and shortage figures from those milestones are simulated.

**Examined, described, or used only for structure or coverage — no forecasting model has been fitted to the NHSBT monthly issues series:**

- NHSBT official monthly issues of platelets, red cells, FFP and cryoprecipitate, April 2016–October 2025 (this study's source; structure and a dated hash only so far).
- NHSBT official monthly red-cell demand and whole-blood collections, same span; weekly bookable donation slots; annual donor counts; Ro red-cell demand.
- NHSBT unofficial daily days-of-stock by blood group for red cells and platelets (svenlatham scraper, April 2023–October 2026). Scraper code is MIT; NHSBT's figures have no printed licence.
- Japanese Red Cross monthly net supply of whole blood, red cells, plasma and platelets (copyright reserved; a private sense-check only, not for deposit).
- Malaysia official daily blood donations by group, 2006–2026 (CC BY 4.0). A long, clean official series, but it measures donor turnout, not platelet issues. Azlin and Nor (2026) have already modelled part of the same official file. It is not Study 2.
- Brazil ANVISA Hemoprod monthly establishment reports (CC BY-ND 3.0). Incomplete coverage (São Paulo and Rio de Janeiro are not in the system), changing numbers of reporting sites, and no open right to share a cleaned file. A **separate, clearly labelled exploratory** analysis of a fixed reporting panel, using only seasonal naive, ETS and SARIMA, is documented in `study2/brazil_exploratory/`. It is not part of this confirmatory question and will not be used to choose methods here.
- Paul-Ehrlich-Institut annual German production, issue and expiry annexes (yearly only; licence restricted).
- Finnish, Swiss and Dutch blood-service yearbooks (annual).
- Tema General Hospital, Ghana: monthly unspecified "blood" demand and supply, 2013–2020 (licence unconfirmed).
- Live stock snapshots from Lifeblood (Australia), Taiwan, Hong Kong and Singapore, and a short frozen Malaysia stock-percentage file from mid-2022. Not usable as official demand series.
- Turkulainen et al. (2022) weekly red-cell demand in Finland and the Netherlands: described in the paper, but the data were not made public.
- Hamilton TRUST / Motamedi / Li datasets: ethics-restricted, not used and not requested.
- Kaggle files labelled as Kenya hospital blood use (failed a reality check) and a synthetic Jordan donation set.
- CDC/HHS NBCUS and WHO GDBS: biennial or annual estimates, not a monthly series.

An independent review dated 18 November 2026 also looked at simple descriptions (counts and yearly averages) of the NHSBT platelet series and of Hemoprod coverage, and did not fit forecasting models to the NHSBT issues series.

---

## Limits (to be stated in the abstract and the paper)

These are national monthly supplier issues. They are not hospital daily demand, and the results do not tell any hospital how many platelets to order. The series has 115 monthly points, with 36 in the one-month-ahead test window. That is a short, relatively smooth national total: hospital-level day-to-day swings cancel out, and a monthly total also hides the 5- to 7-day shelf-life problem. Beating, or failing to beat, a seasonal naive baseline here does not settle the daily hospital ordering problem studied in Study 1. There is no recorded waste or shortage in the file, so there will be no inventory simulation. No open licence has been assumed for the NHSBT spreadsheet.

---

## Licence and sharing

No licence is assumed for the NHSBT workbook. We will cite the official URL, analyse the dated snapshot, and share code, error tables and figures. We will not redistribute the spreadsheet, a re-typed copy of it, or a cleaned extract. The snapshot remains in a gitignored folder.

---

## AI-assistance note

Grok Bot drafted this pre-registration and, in a separate labelled side analysis, ran the exploratory Hemoprod forecasts. Liam Dixon is responsible for the content, the choices, and any later decision to post a final version to OSF. This draft has not been posted. An AI draft or an AI review does not replace review by a human statistician, a transfusion-medicine specialist, or someone who knows data licensing.

---

## Version

Draft 1, 18 November 2026 (America/New_York). To be posted on OSF only after Liam has read it, after any agreed edits, and **before** any forecasting model is fitted to the NHSBT issues series.
