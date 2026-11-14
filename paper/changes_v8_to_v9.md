# Changes from draft v8 to draft v9

Source: `paper/independent_review_v8.md` (optional wording items m1–m6). **Only text and reporting fixes were made. No new analyses were run and no result values changed.** All numbers were verified from existing result files. The title and the author field ("Liam Dixon") are unchanged, the analysis left out of the paper in v5 remains out (only the one Stolla 2025 background sentence remains), and no employer names appear.

## 1. Robustness caveat moved into the main text (review m1)

§4.2 "Other assumptions" still reports that the newer forecasts' mean waste gaps against the weekday average stayed in their favour (0.35 to 0.82 points) under the four other assumptions of Section 3.6 (Supplement Table S4.2). It now also states:

- Under heavy delivery shortfalls, gradient boosting, Chronos-Bolt and SARIMA all wasted less than the 4-week weekday average in all 7 years, with every 95% CI excluding zero.
- The null waste result is therefore specific to the base assumptions.
- The standing order was not run in these scenarios.

Verified from `results/m8/21_multiyear_robustness.csv` (t-based 95% CI over the 7 yearly gaps):

| Forecast | Mean gap (points) | 95% CI | Years lower |
|---|---:|---|---:|
| Gradient boosting | −0.54 | −0.97 to −0.10 | 7/7 |
| Chronos-Bolt | −0.71 | −0.98 to −0.45 | 7/7 |
| SARIMA | −0.65 | −0.94 to −0.36 | 7/7 |

## 2. "Added after internal review" (review m2)

"Added after review" now reads "added after internal review" in the abstract, the Figure 2 caption, the detrended-gradient-boosting Methods sentence, the Supplement S8 Results heading, and the Figure S8 caption, so readers do not take this to mean journal peer review. No bare "added after review" remains in the paper or the supplement.

## 3. SARIMA's 0.3–0.4-point edge qualified (review m3)

The abstract and the Conclusion (and, for consistency, the matching Discussion sentence) now say that SARIMA's calendar edge over the standing order, about 0.3–0.4 points, was statistically clear only under Monday to Saturday. That fact was already in §4.2 and Supplement S8; no numbers changed (Mon–Fri −0.28, Mon–Sat −0.39, Tue–Sun −0.41, daily −0.36; the CI excluded zero only for Mon–Sat; `results/m9/26_weekend_delivery.csv`).

## 4. Realistic shelf-life range quoted (review m4)

The 0–100% life-on-arrival sweep (about 6% to about 17% mean waste) is still reported, but the comparison now leads with the plausible range:

- Raising the share of units arriving with 3 days from the assumed 30% to the calibrated 43% increased weekday-average waste by about 1.3 points (8.9% to 10.2%; Supplement Tables S4.2 and S6.4).
- Discussion: "Across the plausible range (30% to the calibrated 43% short-life units), waste moved by about 1.3 points ... the extreme 0–100% sweep moved it by about 10 points."

Verified: weekday-average 7-year mean waste 8.928% at 30% (`results/m8/21_multiyear_robustness.csv`, base case) and 10.215% at 43% (same file, calibrated-share scenario); gap 1.287 points, reported as 8.9% to 10.2% and about 1.3 points. The 0–100% means across the four original forecasts remain about 6% to about 17% (`results/m6/15_models_life_sweep.csv`).

## 5. S8 Wednesday wording (review m5)

The supplement no longer says recorded Wednesday waste (28%) was "far more than any simulated calendar produced (at most 11%)". Table S8.3 shows only the weekday average, whose maximum Wednesday share is 9% (Tuesday–Sunday). The 11% figure is now attributed: it is the highest share among all forecasts, for detrended gradient boosting under Tuesday–Sunday (`results/m9/26_waste_share_by_weekday.csv`).

## 6. S6.1 Monday-share averaging (review m6)

The 2012–2018 comparison now uses the same convention, the mean of yearly shares, on both sides: 36% simulated against 30% recorded (48% against 32% in 2018). The previous 37% against 29% mixed a mean of yearly simulated shares with a pooled-over-days recorded share (29%; the mean of yearly recorded shares is 30%). Sources: `results/m5/09_reality_check.csv` and `08_hospital_by_year.csv`.

## Size

| | v8 | v9 |
|---|---:|---:|
| Abstract (excluding section labels) | 250 | 250 |
| Body, running text plus headings (same counter: Introduction to Conclusion, excluding table and figure captions and citation keys) | 3,802 | 3,895 |
| Main layout PDF | 14 pages | 14 pages |
| Supplement layout PDF | 33 pages | 33 pages |

The v8 changes file reported 3,805 body words; 3,802 is the count from the same counter used here, applied to both drafts.

Layout PDFs were built with `python3 paper/build_paper.py v9 --layout` and `paper/layout_docx.py`. Hyphen-minus signs were converted to U+2212: 71 in the main paper and 423 in the supplement, the same counts as v8. No hyphen-minus remains as a minus sign before a number in either PDF.

## Number check

`scripts/36_check_v9_numbers.py` covers the v8 checks plus the new v9 wording and the numbers behind it (heavy-shortfall 7/7 and CIs, 30%→43% waste 8.9% to 10.2%, Wednesday 9%/11%, Monday-share means, "after internal review", and the Mon–Sat qualifier). Result: **82 of 82 checks passed** (`paper/refcheck/v9_number_check.md`). The employer-name scan was run separately and found nothing, so the names are not written into any file.

## Files

- `paper/draft_v9.src.md`, `draft_v9.md`, `draft_v9.docx`, `draft_v9_layout.docx`, `draft_v9_layout.pdf`
- `paper/supplement_v9.src.md`, `supplement_v9.md`, `supplement_v9.docx`, `supplement_v9_layout.docx`, `supplement_v9_layout.pdf`
- `scripts/36_check_v9_numbers.py`, `paper/refcheck/v9_number_check.md`

Nothing was pushed, published or shared.
