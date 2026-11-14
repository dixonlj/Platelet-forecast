# Changes from draft v9 to draft v10

*14 November 2026. v10 reports the analyses run per the written analysis plan (`osf_preregistration_final.md`, finalised 04:04 ET with inputs hashed at 03:41 ET, before the 04:30–05:10 ET analyses). The plan was registered on OSF later on 14 November 2026, **after** the analyses; v10 says this openly (Methods 2.1, Limitations, Table 3 D8). v9 was the exploratory study.*

## What the paper now says

| | v9 (exploratory) | v10 (per the analysis plan) |
|---|---|---|
| Headline | No forecast was shown to beat a 4-week weekday average; a standing order matched the newer forecasts | **No forecast was shown to beat the prior-year standing order** at Aachen or at Stanford (null under the analysis plan). The calibrated simulation **failed validation**, and the abstract says so. |
| Main comparator | 4-week weekday average | Prior-year standing order (set in the analysis plan). The weekday average is secondary. |
| Ordering rule | Constant cushion for every order | Cushion sized to each order's days (R1). The constant cushion (R2) and an age-aware rule (R3) are secondary. |
| Simulation | Uncalibrated, documented Tue–Sat calendar | Calibrated on 2009–2011 (Mon–Sat, all units with 4 days, waste logged one day late, heavy shortfalls), then validated on 2012–2018: **failed** A1, A2 and A3 |
| Statistics | Year-level tests, mostly unadjusted | Mixed model over 84 four-week blocks, t with 6 df, Holm across 4 tests, preset labels and a 0.5-point minimum meaningful difference |
| Sites | Aachen only | Aachen plus Stanford (public `pip` data, 509 days) |
| Design wording | Simulation study | **Retrospective simulation study using public data** with a planned analysis; the plan was registered on OSF after the analyses (stated as a limitation and as deviation D8) |
| Target journal | *Transfusion* (3,500 words) | ***Transfusion Medicine*** Original Article (5,000 words, 6 display items, 60 references); see `paper/journal_plan_v10.md` |

## Key numbers (all checked against the results files)

- Validation: waste 5.22% simulated vs 9.74% recorded; 5.00 vs 8.82 emergency units per short day; weekday TVD 0.226 (limit 0.20); year correlation 0.25.
- Aachen primary (standing order 5.30%): SARIMA −0.33 (95% CI −0.88 to +0.22, Holm p 0.75); Chronos-Bolt −0.12; detrended GB +0.07; GB +0.17. All "not demonstrated", none equivalent.
- Stanford (standing order 2.86%): −1.40 to −2.29 points, Holm p 0.10 to 0.22. Consistent null.
- Exploratory, labelled as such: delivery calendar (SARIMA Tue–Sat −2.47, Mon–Fri −1.77); against the weekday average, SARIMA −0.54 (−1.03 to −0.05).
- Number check: 53 of 53 checks pass; all 279 numeric tokens in the abstract, body, captions and Table 3 are tied to a check or to a listed design constant (`paper/refcheck/v10_number_check.md`).

## Structure

- Rewritten from scratch in the *Transfusion Medicine* format. Structured abstract with the journal's headings (Objectives; Background; Methods/Materials; Results; Conclusion), 250 words, no abbreviations.
- Body text 3,247 words (v9: about 4,100, counting captions and table text).
- 6 display items (the journal's cap):
  - Table 1: validation;
  - Figure 1: calibration by year;
  - Figure 2: Aachen primary result;
  - Figure 3: Stanford;
  - Table 2: secondary, sensitivity and exploratory results;
  - Table 3: deviations D1–D8 (D8: registration after the analyses).
- All v9 tables and figures were dropped from the main text.
- 30 references. New: the OSF registration of the analysis plan (with an [OSF DOI] placeholder) and the `pip` package for the Stanford data.
- New Supplement v10:
  - S1: full deviation log, clarifications and exploratory observations;
  - S2: all sensitivity analyses;
  - S3: LASSO/RNN substitute (D2);
  - S4: Stanford at 0 and 25 short days, and the clinical reference models;
  - S5: forecast accuracy;
  - S6: trade-off curves and the cushion chosen in advance;
  - S7: calibration details;
  - S8: STRESS checklist.
- No "preregistered" wording remains: the study is described as following an analysis plan finalised before the analyses and registered afterwards. Two old input files (`prereg_deviations.md`, `revision_results_summary.md`) now carry a correction note and D8.
- Title-page statements now cover the *Transfusion Medicine* list: data availability, funding, competing interests, ethics, patient consent, permissions, trial registration, AI use and author contributions.

## Removed from the main text

- v9's exploratory claims about the 20-short-day target, lost units and calendar results against the weekday average are not repeated as findings. Where the planned versions exist, they appear in Table 2 or the supplement, labelled.
- The 2018 US-rules scenario, the add-ons (2017–2018), and the shelf-life discussion based on uncalibrated runs.
- The cold-stored analysis stays out, as decided.

## Build

- `python3 paper/build_paper.py v10` and `python3 paper/build_paper.py v10 --layout`. Plain PDFs come from `soffice --headless --convert-to pdf`.
- Tables come straight from the results files: `scripts/43_tables_v10.py`.
- Number check: `scripts/44_check_v10_numbers.py`.
- Page counts:
  - `draft_v10.pdf`: 19 pages;
  - `draft_v10_layout.pdf`: 14 pages;
  - `supplement_v10.pdf`: 14 pages;
  - `supplement_v10_layout.pdf`: 8 pages.

## Still to do (Liam)

- Replace [OSF DOI] once OSF shows it, and add the timing and deviations note (`paper/osf_update_text.md`) to the registration when submitting it, or file it right after.
- The Zenodo DOI, the repository going public, medRxiv and journal submission all wait for your explicit yes.
