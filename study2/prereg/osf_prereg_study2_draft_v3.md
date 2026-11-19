# OSF pre-registration draft — Study 2 (version 3)

**Status:** FINAL DRAFT FOR POSTING (draft 3, reviewed 19 November 2026). This document has not yet been posted to OSF or anywhere else. No forecasting model has been fitted or scored on the NHSBT issues series. Looking at the file structure (date range, gaps, and how values are written) was allowed and is described below. A structure-only check of the analysis script's loader was also run on the snapshot (sheet name, column names, 115 rows, first and last month, no gaps, hash); it printed no values and computed no forecasts or errors. Its console output is saved at `study2/results/nhsbt_structure_check/check_structure_log.txt`.

**Date of this draft:** 18 November 2026 (America/New_York). This is version 3 of the draft. Versions 1 and 2 are kept at `osf_prereg_study2_draft.md` and `osf_prereg_study2_draft_v2.md`. The changes are listed in `changes_v1_to_v2.md` and `changes_v2_to_v3.md`.

**Public affiliation:** Independent researcher. Educational, advisory-only project. Not clinical advice, and nothing here will be deployed as an ordering tool.

**Data rule:** public data only. No employer, hospital-system or vendor data. No patient-level files and no credentialed clinical databases.

---

## Title

Forecasting monthly platelet issues from a national blood service in England, 2016–2025: a pre-registered comparison of simple seasonal methods

## Primary research question

For national monthly platelet units issued to hospitals in England from April 2016 to October 2025, do pre-specified standard statistical models (ETS, SARIMA, and one calendar regression) forecast **one month ahead** more accurately than a calendar-fair seasonal naive baseline? Only the one-month horizon is confirmatory; forecasts two and three months ahead are reported descriptively.

This is a **national blood-service supply-planning** question. It is about the total number of platelet components the national supplier issued to hospitals each month. It is not a hospital daily ordering question, and the results will not tell any hospital how many platelets to order.

---

## Primary series

- **What:** monthly platelet units issued to hospitals by NHS Blood and Transplant (NHSBT), England.
- **Where in the file:** workbook sheet "Blood Products Issued by Month," column "Platelets."
- **Span:** April 2016 to October 2025, **115 months, no gaps.** The sheet title and the data notes say "April 2016 – August 2025," but the rows run through October 2025. We will use all 115 months as published, and we will also run a pre-specified sensitivity that drops September and October 2025 as scoring targets, because those two months fall outside the sheet's stated period and may be provisional. They are the last two one-month-ahead test months, so the check matters.
- **Source (official, no account):** the Parliamentary Questions transparency page, https://www.nhsbt.nhs.uk/who-we-are/transparency/parliamentary-questions/, file https://nhsbtdbe.blob.core.windows.net/umbraco-assets-corp/40021/blood-donation-appointments-available-products-issued-and-meeting-ro-demand-2016-2025.xlsx
- **Dates inside the file:** the data notes give an extract date of 12 November 2025 and a "Period Covered" of "2016 – 14/11/2025," which does not match the sheet title or each other. There is also a `#VALUE!` error in the data-notes sheet. These are signs of a hand-assembled file. We will analyse the dated snapshot as it stands.
- **Unit definition:** the data notes describe this column as the "Number of blood components issued to hospitals, by month." They do not print a clearer definition (for example adult dose versus pack). All 115 platelet figures fall on a quarter-unit grid (for example 21,337.75), which is consistent with fractional adult-dose counting, but we will not convert or re-round the published numbers. We will analyse them as they stand.
- **What this series is not:** it is not daily hospital demand, not a single hospital, not inventory, and not recorded expiry or waste. We will not run a waste or shortage simulation on these data, because neither waste nor shortage is recorded.

### Dated snapshot and hash

The official workbook was first downloaded on 18 November 2026 for scouting (evening, America/New_York). A dated snapshot was saved later the same day, before any model was fitted, at a gitignored path:

`study2/data/public/NHSBT_issues_2016-2025_snapshot_2026-11-18.xlsx`

SHA-256:

`f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696`

A later live download of the same official URL matched this hash. The folder `study2/data/public/` is listed in the project `.gitignore`. This box working copy may not itself be a git repository; the ignore rule should be checked in the real repository clone before any push.

NHSBT has printed no open licence on the file or the landing page, and figures may later be revised. The snapshot is kept so that the analysis can be tied to a known extract. **The spreadsheet will not be redistributed.** Results, error tables and figures may be reported; the file itself will not be placed in a public repository, preprint or supplement. If a public data deposit is wanted later, that is a request for NHSBT to make, not something this draft assumes.

### Looking at the file structure (not modelling)

Only the following descriptive checks have been made on this snapshot, plus earlier scouting counts and a reviewer's own descriptive look (counts, yearly averages, and the 115-month mean of about 682 platelet units a day, range about 509 to 740). No forecast has been produced from the NHSBT series.

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

These are pre-specified secondary analyses, not a hunt for a product where a model looks better. Every method, horizon and metric listed below will be reported for each product, including results that favour the baseline. **All secondary-product results are descriptive** (see Uncertainty). No winner will be declared from them.

### The April 2024 red-cell counting change

Even though the primary series is platelets, we note a change in how red-cell issues are written from April 2024. This date was noticed from the number format of months that fall inside the test window, so it is a mild information leak about format, not about forecast errors; it is disclosed here. NHSBT also warns that metric definitions, methodologies and reported values could be revised.

For the secondary red-cell analysis we pre-specify:

- The primary red-cell evaluation uses the same origins and horizons as the platelet analysis.
- The calendar regression may include a level-shift indicator from April 2024, **but only once at least three months after April 2024 are already in the training window** — that is, only at origins whose training data include July 2024 or later. We will also report the red-cell regression **without** that shift, at every origin.
- A pre-specified sensitivity will start the red-cell test period at April 2024, so that all scored red-cell months use the later counting style. That shortens the red-cell test window, and we will say so.
- We will also split red-cell errors into months before April 2024 and months from April 2024 on, and report both. We will not choose this split after seeing the results.

---

## Train/test split and evaluation

- **Expanding-window** evaluation (the training sample grows by one month at each origin; it is not a fixed-length rolling window).
- Origins cover the last 36 months of the series (targets from November 2022 to October 2025).
- At the end of each month *t*, models are fitted only on data up to *t* and then forecast *t*+1, *t*+2 and *t*+3.
- Origins that support all three horizons and still land inside the series run from the end of October 2022 through the end of July 2025 (34 origins). One-month-ahead scores will also be reported for the two later origins that can still be scored (August and September 2025), giving 36 one-step forecasts.
- The first training window therefore has 79 months (April 2016 to October 2022), about 6½ seasonal cycles, one of them covering the COVID period. That is enough for the short method list below. It is **not** enough to train gradient boosting, deep learning, or a large machine-learning model fairly, and those methods will not be used.
- Models are refit at every origin, using only past data.

Sample size will be stated in the abstract and the limits section: **115 monthly points, 36 in the one-month-ahead test window (34 origins for the three-month horizon).**

---

## Horizons

Primary horizon: **1 month ahead.**

Also reported, always, as **descriptive** only: **2 months ahead** and **3 months ahead.** These are the horizons that matter for national collection and supply planning, not for next-day hospital ordering.

---

## Metrics

- **Primary metric:** mean absolute error (MAE) of **units per day.** Each month's issued total is divided by the number of days in that month (including leap days) before errors are computed. This stops February from looking like a "demand dip" that a model can take credit for catching. It does not adjust for the number of weekdays or bank holidays, or for the moving date of Easter, which can also change the monthly total. That remaining calendar effect is a limitation and will be stated as such. It also affects the seasonal naive baseline.
- **Secondary metrics (descriptive):** MAE of the raw monthly totals; root mean squared error (RMSE) of the units-per-day series; mean absolute percentage error (MAPE) of the units-per-day series. MAPE is secondary because the primary decision is in units, not percentages. On this series, MAPE of the per-day rates is the same as MAPE of the monthly totals, and the per-day values stay well above zero.

We will not add further error measures after seeing the results.

---

## Methods (fixed, short list)

All methods are fitted on the units-per-day series, then compared on that scale. The method list is closed.

The exploratory Brazil forecasts (seasonal naive, ETS and SARIMA, with the same orders later written down here) had already been run before this plan was finalised. The method list was not changed after seeing those results. An earlier review had suggested a 12-month seasonal average and at most one machine-learning model. Those were replaced, before this draft was locked, by a single calendar regression: a 12-month average is close to seasonal naive, whereas the regression uses the whole training window's month effects, adds a linear trend, and (for red cells) can include the April 2024 level shift. That swap was not a response to the Brazil errors.

Software, frozen before posting: Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1, openpyxl 3.1.5. Random seed 20261118. The **complete** analysis is in two files: `study2/prereg/nhsbt_analysis.py` (SHA-256 `dcb2f18cf590505db266574b317368cf2d719126644e6d2f064aaf07404354ac`) and the helper module it imports, `study2/prereg/inference.py` (SHA-256 `0e5248d473a0bb216f1d1e20d7536f0c3401b4e04e11bb3033f66a0528e0bf64`). `nhsbt_analysis.py` runs everything in this plan end to end: it loads the sheet, converts each monthly total to units per day, makes every forecast, computes every metric, interval and test, applies Holm and the verdict rule, runs every secondary and sensitivity analysis, and writes the output tables (listed under **Outputs**). It has been run only on a made-up workbook in the same layout (`--synthetic-test`, which runs the whole pipeline and then 78 checks) and, on the real snapshot, only in a structure-only mode (`--check-structure`). The confirmatory run (`--nhsbt`) refuses to start unless it is given a URL beginning with `https://osf.io/` and the snapshot hash matches; this is only a guard against accidental runs, because the script cannot check that the URL is a real registration. Before reading the snapshot, it also computes the SHA-256 of `nhsbt_analysis.py` and `inference.py` and stops unless both match the hashes written in this paragraph **and** the same hashes in the small manifest `study2/prereg/FROZEN_CODE.sha256`. The expected hashes are kept outside the scripts, so neither script has to contain its own hash. This makes a quiet edited rerun visible; it cannot make the run impossible. The actual protection is the timeline: the OSF registration's public timestamp must come before the run time recorded in the run manifest. The v2 code, whose hashes appear in draft 2, is kept unchanged in `study2/prereg/archive_v2_code/`.

1. **Seasonal naive (the calendar-fair baseline).** The forecast for a month is the units-per-day value from the same calendar month one year earlier. For a two- or three-month horizon, the forecast is the units-per-day value from 12 months before the target month, using only data available at the origin. This already respects month length because the series is on a per-day scale. In the **primary** analysis, the one-month-ahead seasonal naive forecasts for November and December 2022 are simply the November and December 2021 values, which sit inside the COVID window (see COVID rule).

2. **ETS.** One specification only: **no trend** (level plus additive season only; this is not the textbook Holt–Winters model with a trend), additive season with period 12, initial values estimated, fitted by minimising the sum of squared errors using `statsmodels.tsa.holtwinters.ExponentialSmoothing` with `fit(optimized=True)`. ETS (like SARIMA) is fitted **once per origin** and that one fit gives the 1-, 2- and 3-month forecasts. If this specification fails at an origin (see the failure rule below), that origin is omitted for ETS at all horizons, and the number and share of omitted origins is reported. If more than half of the origins for a product in a run are omitted, that product's ETS result in that run will be labelled **unreliable** (the same rule as for SARIMA below). No other ETS form will be substituted.

3. **SARIMA.** Pre-specified order (0,1,1)(0,1,1)12, **without a constant**, estimated on the training window only. If that specification fails at an origin, the only reserved fallback is (1,0,1)(1,0,1)12 **with a constant** (`trend='c'` in statsmodels). The constant is required because that fallback has no differencing and would otherwise forecast toward zero. SARIMA is fitted **once per origin**, so the fallback, if used, applies to that origin's 1-, 2- and 3-month forecasts. The number and share of fallback origins will be reported for every run and product. If both specifications fail, that origin is omitted for SARIMA. A product's SARIMA result in a run is labelled **unreliable** if more than half of its origins used the fallback, or if more than half were omitted. The **unreliable** label (for ETS or SARIMA) is reported next to the verdict and never changes the verdict itself. No other orders will be tried, and we will not search a larger grid after seeing test errors.

4. **One regression:** a linear calendar regression of units per day on an intercept, 11 month indicators (February to December) and a linear time trend, estimated by ordinary least squares on the training window only and refitted at each origin. The time variable is each month's real position in the series (0 for April 2016, 1 for May 2016, and so on), in training and forecasting alike. For the secondary red-cell series, the April 2024 level shift is added only under the rule above, and the no-shift version is always reported as well. No other regressors, and no machine-learning models.

**Failure rule (ETS and SARIMA).** A fit has failed if any of the following is true: (a) the software raises an exception; (b) a warning is issued whose category is statsmodels `ConvergenceWarning`; (c) a warning is issued whose message contains "converge" (any case); (d) a warning is issued whose message contains both "failed to" and "optim" (any case); (e) the forecast is not a finite number; or (f), for SARIMA and for the state-space ETS used only in the COVID sensitivity, `mle_retvals['converged']` is False. (Draft 2 named a `success` key; statsmodels records this as `converged`.) Other warnings do not count as failures. Every warning at every origin, and every failure, is written to `fit_warning_log.csv` with the run, product, method, origin and specification.

We will report every method at every horizon, including when the baseline is as good as or better than the others. If seasonal naive is reliably *better* on the primary tests, we will say so plainly.

---

## COVID rule (pre-specified)

The COVID-affected window is **March 2020 through December 2021** inclusive. This window sits entirely inside the training history of the scored test months, which start in November 2022. In the primary analysis we will not drop, dummy out, winsorize, or interpolate those months. Models see them as ordinary history.

That said, the **seasonal naive forecasts for the first two test months (November and December 2022) are the November and December 2021 values**, which are inside the COVID window. So COVID months directly feed two baseline forecasts in the primary analysis. This is noted here in advance.

A pre-specified sensitivity, reported but not used to pick a winner, will handle those months as follows:

- **ETS and SARIMA:** treat March 2020–December 2021 as **missing values**, leaving the calendar in place (the series is not cut and joined). `holtwinters.ExponentialSmoothing` does not accept missing values, so ETS in this sensitivity only will be fitted with the equivalent state-space model `statsmodels.tsa.statespace.exponential_smoothing.ExponentialSmoothing` (no trend, additive season of period 12), which can treat months as missing. This implementation difference is confined to the sensitivity and will be reported. SARIMAX already allows missing observations. The same SARIMA orders and fallback rule apply.
- **Calendar regression:** drop the COVID rows from the training data. The remaining months keep their calendar labels and their **real time position** (for example, January 2022 stays at position 69); time is not renumbered after the rows are dropped.
- **Seasonal naive:** use the most recent same calendar month that is outside the COVID window and already known at the origin. For November and December 2022, that means November and December **2019**. This substitute is three years older than the target, while ETS and SARIMA in the same sensitivity see 2022 data, so it makes the baseline's job slightly harder; that is acceptable for a descriptive sensitivity and is stated here in advance.
- **ETS and SARIMA reliability in this sensitivity:** with 22 months missing, fits may fail more often, so ETS may be omitted and SARIMA may use its fallback at many origins. The omitted and fallback shares will be reported, and the unreliable rules above apply (more than half of origins omitted, for ETS or SARIMA; more than half on the fallback, for SARIMA). Every sensitivity result is shown with the number of months actually paired.
- **Scope:** the COVID sensitivity is run for all four products at all three horizons, scored on all test months.

We will not redefine the COVID window after looking at residuals.

---

## Uncertainty, multiple testing, and how a "winner" is (and is not) declared

**Smallest difference that would matter.** We set this at **7 platelet units a day**. It is a **judgement call**, not taken from any planning standard and not from test-period forecast errors. For scale only, it is about 1% of typical daily national issues (the 115-month descriptive mean of about 682 units a day, which includes the test months, is used for scale only). It is used in the decision rule below. No power calculation has been done, so this study **may not be able to** detect a difference of that size.

**Block bootstrap.** MAE and MAE differences will use a **circular overlapping moving-block bootstrap**: blocks may start at any test month and wrap around from the last test month to the first, so every month has the same chance of being drawn (a non-circular version would give the first and last months, including September and October 2025, less weight):

- block length is **3 months** at the one-month horizon, and **h + 2 months** at horizon *h* (so 4 months at the two-month horizon and 5 at the three-month horizon);
- 10,000 resamples, with **percentile** 95% intervals (2.5th and 97.5th percentiles of the resampled statistic);
- random seed 20261118;
- for differences, the two methods' forecasts are first **joined by target month**, keeping only months where both have a forecast (the number of months dropped, and which ones, is reported); the **same resampled target months** are then used for both methods (paired). Forecasts are never paired by their position in a list.

A plain bootstrap of single months is not used, because forecast errors on this series come in runs.

**Diebold–Mariano test.** Two-sided, absolute-error loss. The variance is Newey–West (Bartlett weights) with **h − 1 lags** (lag 0 at the one-month horizon). The loss differential uses the same month-joined pairs as the bootstrap. The test statistic is then given the **Harvey–Leybourne–Newbold (1997) small-sample correction**, and the p-value is taken from a *t* distribution with *n* − 1 degrees of freedom. If the variance estimate is zero or negative, we will report "test not computable" and treat that comparison as "could not tell them apart." Lag 0 at one month is the textbook choice, but this plan also expects errors to come in runs, which could make the test too willing to call a difference. The safeguard is the joint rule below: the block-bootstrap interval, which does allow for runs, must agree. As a descriptive check only, the three primary tests will also be reported with 2 Newey–West lags.

**Primary tests and Holm correction.** The only confirmatory comparisons are the **three** one-month-ahead tests on platelet units per day: ETS versus seasonal naive, SARIMA versus seasonal naive, and the calendar regression versus seasonal naive. Those three Diebold–Mariano p-values (HLN-corrected) will be Holm-corrected at 5%, and the Holm-adjusted p-values will be reported as well as whether each test was rejected. A test that is not computable counts as p = 1. A method will be described as better than seasonal naive **only if** the Holm-corrected test is significant **and** the block-bootstrap confidence interval for the MAE difference excludes zero. If the interval and the Holm-corrected test both say that seasonal naive was better, we will say so plainly. Otherwise we will say that we **could not tell the methods apart**. Thirty-six one-step errors from a smooth monthly series are correlated, so this last outcome is likely, and we will treat it as an honest result rather than a problem to be fixed by trying more models.

**Practical importance (uses the 7 units/day difference).** A difference is called **practically meaningful** only if the method is declared better (or worse) under the rule above **and** its MAE differs from seasonal naive by at least 7 units/day **and** the whole 95% interval is at least 7 units/day away from zero. If the method is declared better and the point estimate is at least 7 units/day, but the interval includes smaller differences, we will say that the difference may be smaller than what matters. If it is declared better but by less than 7 units/day, we will say the difference is below the smallest difference that would matter. A method that is not declared better or worse gets no practical claim.

**Everything else is descriptive.** That includes the two- and three-month horizons, the secondary products, the secondary metrics, the COVID sensitivity, the September–October 2025 sensitivity, and all red-cell shift and split checks. For those results we will not use "significant" or "better" wording, and we will not declare a winner from them. The September–October 2025 sensitivity (dropping those two months as scoring targets) and the red-cell checks (test period starting April 2024, and errors split before and from April 2024) are scored on the primary run's forecasts for each product they apply to; the models are not refitted for them.

**How many comparisons the plan produces.** Across 3 methods × 3 horizons × 4 products there are 36 forecast comparisons against the baseline, before counting the COVID sensitivity (another 36), the September–October 2025 sensitivity, the red-cell shift and split checks, and the three secondary metrics. That is well over 100 numerical comparisons. Only the three primary tests are confirmatory and Holm-corrected. Red cells add one more method (the regression with the April 2024 shift) in every red-cell table.

---

## Outputs (written by `nhsbt_analysis.py --nhsbt`)

All in `study2/results/nhsbt_confirmatory/`:

- `primary_result.md`: the three confirmatory tests, raw and Holm-adjusted p-values, intervals, verdicts and practical labels, plus the SARIMA fallback shares.
- `comparisons_vs_naive.csv`: every method minus seasonal naive, for every run, product, scoring set and horizon, with months paired, months dropped, each method's MAE on the paired months, interval, HLN-DM p-value, the method's reliability label, role (confirmatory or descriptive) and verdict.
- `accuracy.csv`: MAE (units per day) with 95% interval, and the secondary metrics (MAE of monthly totals, RMSE and MAPE of units per day), for every method. Each method is scored on its own forecast months, so if a method drops months its MAE here covers fewer months than seasonal naive's; like-for-like MAEs are in `comparisons_vs_naive.csv`.
- `forecasts_long.csv`: every forecast with its origin, target month, actual value, and monthly-total equivalents.
- `dm_lag2_check.csv`: the descriptive lag-2 check on the three primary tests.
- `naive_2021_vs_2019.csv`: the seasonal-naive inputs for November and December 2022 under the primary rule and the COVID sensitivity.
- `fit_summary.csv` and `fit_warning_log.csv`: specifications used, fallback and omitted origins with their shares and reliability labels, every warning.
- `run_manifest.json`: input hash, software versions, seed, script hashes, OSF registration URL and run time.

Results tables and figures may be shared. The spreadsheet itself will not be redistributed. `forecasts_long.csv` and `naive_2021_vs_2019.csv` contain the actual monthly values, so they will be kept with the snapshot (not in a public repository) unless a licensing check says otherwise.

---

## Prior work, and how this study is an extension

Nandi, Roberts and Nandi, *Transfusion* 2020;60(3):535–543, doi:10.1111/trf.15705, already forecast NHSBT **red-cell** issues. They used daily aggregates from 2005 to 2011, derived the **average weekly issues over 4-week periods**, and, **with tuned window size and model order**, found that four simple linear methods gave "very similar results." Their reported figure is a standard deviation of the percentage error of 3.0% at 4 weeks and 4.0% at 24 weeks (public abstract). **That measure cannot be compared directly with this study's MAE.**

The present study is an **extension**, not a replication. It changes the product (platelets rather than red cells), the time grain (months rather than weeks and 4-week averages), the period (2016–2025, which includes COVID), and the methods, and it writes the plan down before any model is fitted. The contribution is modest and will be described that way.

Ejohwomu, Too and Edwards (2021, doi:10.1080/17509653.2021.1892548) simulated **platelet** stock levels at UK Stock Holding Units, using agent-based and discrete-event modelling. It is the closest UK platelet work, but it is a simulation, not a forecasting-method comparison, and its data ("collected from typical UK SHUs") are not public. A free author copy of the paper is available; that does not make the data open.

---

## Datasets already examined, and models already run

This list is here so that Study 2 is not a silent hunt across products and countries. None of the following changes the primary question above.

**Already used for modelling in this project (not the Study 2 confirmatory series):**

- University Hospital Aachen daily platelet transfusions, purchases and recorded waste, 2008–2018 (CC BY 4.0), from Schilling, Rickmann, Hutschenreuter and Spreckelsen, *JMIR Medical Informatics* 2022;10(2):e29978, doi:10.2196/29978. Used in Study 1. Advanced models did not reliably beat simple baselines on that daily hospital series.
- Stanford `pip` example data: daily platelet use at two hospitals combined, 2013–2015, with clinical-driver columns (GPL 2 or later), https://github.com/bnaras/pip, commit `6834939381870116f544e6b6fde6b92566c986f7`. Used in Study 1 and again in Study 2 milestones S2-1 to S2-10. On that series, SARIMA beat a weekday average on next-day MAE in 22 of 24 four-week windows; a lasso in the style of Guan et al., *Proceedings of the National Academy of Sciences* 2017;114(43):11368–11373, doi:10.1073/pnas.1714097114, that used laboratory and census features was close on accuracy and looked better in a *simulated* waste comparison; gradient boosting and Chronos were also run. There is no recorded waste in the Stanford file; waste and shortage figures from those milestones are simulated.

**Examined, described, or used only for structure or coverage — no forecasting model has been fitted to the NHSBT monthly issues series:**

- NHSBT official monthly issues of platelets, red cells, FFP and cryoprecipitate, April 2016–October 2025 (this study's source; structure and a dated hash only so far).
- NHSBT official monthly red-cell demand and whole-blood collections, same span; weekly bookable donation slots; annual donor counts; Ro red-cell demand.
- NHSBT unofficial daily days-of-stock by blood group for red cells and platelets (svenlatham scraper, April 2023–October 2026, https://github.com/svenlatham/nhsbt-blood-levels). Scraper code is MIT; NHSBT's figures have no printed licence.
- Japanese Red Cross monthly net supply of whole blood, red cells, plasma and platelets (copyright reserved; a private sense-check only, not for deposit).
- Malaysia official daily blood donations by group, 2006–2026 (CC BY 4.0). A long, clean official series, but it measures donor turnout, not platelet issues. Azlin and Nor (2026, doi:10.30880/ekst.2026.06.01.049) have already modelled part of the same official file (January 2019–February 2025). It is not Study 2. (Crossref lists only Azlin; the journal page lists both authors.)
- Brazil ANVISA Hemoprod monthly establishment reports (CC BY-ND 3.0). Incomplete coverage (São Paulo and Rio de Janeiro are not in the system), changing numbers of reporting sites, and no open right to share a cleaned file. A **separate, clearly labelled exploratory** analysis of a fixed reporting panel, using only seasonal naive, ETS and SARIMA, is documented in `study2/brazil_exploratory/`. Those forecasts were run before this pre-registration was finalised. They did not tune the confirmatory methods and must not be used to choose methods here. The Brazil analysis itself was not pre-registered.
- Paul-Ehrlich-Institut annual German production, issue and expiry annexes (yearly only; licence restricted).
- Finnish, Swiss and Dutch blood-service yearbooks (annual).
- Tema General Hospital, Ghana: monthly unspecified "blood" demand and supply, 2013–2020 (licence unconfirmed).
- Live stock snapshots from Lifeblood (Australia), Taiwan, Hong Kong and Singapore, and a short frozen Malaysia stock-percentage file from mid-2022. Not usable as official demand series.
- Turkulainen, Wemelsfelder, Janssen and Arvas (2022, doi:10.1111/trf.16870) weekly red-cell demand in Finland and the Netherlands: described in the paper, but the data were not made public.
- Hamilton TRUST / Motamedi / Li datasets: ethics-restricted, not used and not requested.
- Kaggle files labelled as Kenya hospital blood use (failed a reality check) and a synthetic Jordan donation set.
- CDC/HHS NBCUS and WHO GDBS: biennial or annual estimates, not a monthly series.

An independent review dated 18 November 2026 also looked at simple descriptions (counts, yearly averages, and the 115-month daily mean) of the NHSBT platelet series and of Hemoprod coverage, and did not fit forecasting models to the NHSBT issues series.

---

## Limits (to be stated in the abstract and the paper)

These are national monthly supplier issues. They are not hospital daily demand, and the results do not tell any hospital how many platelets to order. The series has 115 monthly points, with 36 in the one-month-ahead test window. That is a short, relatively smooth national total: hospital-level day-to-day swings cancel out, and a monthly total also hides the 5- to 7-day shelf-life problem. Dividing by days in the month adjusts for month length, not for weekdays, bank holidays or Easter. Beating, or failing to beat, a seasonal naive baseline here does not settle the daily hospital ordering problem studied in Study 1. There is no recorded waste or shortage in the file, so there will be no inventory simulation. No open licence has been assumed for the NHSBT spreadsheet.

---

## Licence and sharing

No licence is assumed for the NHSBT workbook. We will cite the official URL, analyse the dated snapshot, and share code, error tables and figures. We will not redistribute the spreadsheet, a re-typed copy of it, or a cleaned extract. The snapshot remains in a gitignored folder.

---

## References (DOIs checked 18 November 2026 against Crossref)

- Azlin NS, Nor ME. Time series modelling of daily blood donations in Malaysia. *Enhanced Knowledge in Sciences and Technology.* 2026;6(1):426–436. doi:10.30880/ekst.2026.06.01.049
- Ejohwomu OA, Too J, Edwards DJ. A resilient approach to modelling the supply and demand of platelets in the United Kingdom blood supply chain. *International Journal of Management Science and Engineering Management.* 2021;16(2):143–150. doi:10.1080/17509653.2021.1892548
- Guan L, Tian X, Gombar S, et al. Big data modeling to predict platelet usage and minimize wastage in a tertiary care system. *Proceedings of the National Academy of Sciences.* 2017;114(43):11368–11373. doi:10.1073/pnas.1714097114
- Harvey D, Leybourne S, Newbold P. Testing the equality of prediction mean squared errors. *International Journal of Forecasting.* 1997;13(2):281–291. doi:10.1016/S0169-2070(96)00719-4
- Nandi AK, Roberts DJ, Nandi AK. Prediction paradigm involving time series applied to total blood issues data from England. *Transfusion.* 2020;60(3):535–543. doi:10.1111/trf.15705
- Schilling M, Rickmann L, Hutschenreuter G, Spreckelsen C. Reduction of platelet outdating and shortage by forecasting demand with statistical learning and deep neural networks: modeling study. *JMIR Medical Informatics.* 2022;10(2):e29978. doi:10.2196/29978
- Turkulainen EV, Wemelsfelder ML, Janssen MP, Arvas M. A robust autonomous method for blood demand forecasting. *Transfusion.* 2022;62(6):1261–1268. doi:10.1111/trf.16870

The Harvey, Leybourne and Newbold reference was checked against Crossref on 18 November 2026 (*International Journal of Forecasting* 1997;13(2):281–291). The formula used in the code is the standard published adjustment, \(DM^* = DM\sqrt{(n+1-2h+h(h-1)/n)/n}\), compared with \(t_{n-1}\).

---

## AI-assistance note

Grok Bot drafted this pre-registration (versions 1, 2 and 3) and wrote the analysis code and, in a separate labelled side analysis, ran the exploratory Hemoprod forecasts. Liam Dixon is responsible for the content, the choices, and any later decision to post a final version to OSF. This draft has not been posted. An AI draft or an AI review does not replace review by a human statistician (especially for the bootstrap and Diebold–Mariano details), a transfusion-medicine specialist, or someone who knows data licensing.

---

## Version

Draft 3, 18 November 2026, last edited 19 November 2026 (America/New_York). Research Reviewer's final plan-matches-code check (review_prereg_v3b.md) found nothing required. To be posted on OSF only with Liam's own approval and **before** any forecasting model is fitted to the NHSBT issues series.

File name note: the local copy of this plan must keep the name `study2/prereg/osf_prereg_study2_draft_v3.md`, because `nhsbt_analysis.py` reads the expected code hashes from that fixed path. The copy uploaded to OSF may use any name.
