# Data

## `public/UKA_Aachen_daily_platelets_2008-2018_JMIR_app1.xlsx` (real, public, aggregate)

Daily platelet counts from University Hospital Aachen (UKA), Germany, 1 January 2008 to 31 December 2018 (4,018 days). Each row is a hospital-day total: units transfused, units wasted (outdated) and units bought in an emergency, plus the source authors' own forecasts. There are **no patient-level data**.

- **Source:** Multimedia Appendix 1 of Schilling M, Rickmann L, Hutschenreuter G, Spreckelsen C. Reduction of Platelet Outdating and Shortage by Forecasting Demand With Statistical Learning and Deep Neural Networks: Modeling Study. *JMIR Med Inform* 2022;10(2):e29978. doi:[10.2196/29978](https://doi.org/10.2196/29978). PMCID: [PMC8848235](https://pmc.ncbi.nlm.nih.gov/articles/PMC8848235/).
- **Licence:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)), as stated in the article. Redistribution is allowed with attribution.
- **Changes:** none. The file is the original appendix, renamed. Row 1 holds the publisher's copyright note; the header is on row 2.
- Downloaded on 13 November 2026 through the Europe PMC supplementary-files service: `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8848235/supplementaryFiles`.

## `public/UKA_Aachen_daily_platelets_2008-2018.csv`

A trimmed copy of the same appendix (columns `date`, `Weekday`, `Transfused`, `Waste`, `Purchase` only). It is an adaptation of the CC BY 4.0 appendix above (columns removed) and carries the same licence and attribution. The scripts read the `.xlsx`; the `.csv` is for quick viewing.

## `SYNTHETIC_daily_platelet_demand.csv`

**Synthetic example data** made by `scripts/generate_synthetic_data.py` (seed 42). It is not real and was used only to build and test the first script (`01_baselines.py`).
