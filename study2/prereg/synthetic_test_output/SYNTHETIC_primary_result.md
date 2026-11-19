# Primary result (SYNTHETIC)

**MADE-UP DATA. These numbers are a code test, not a result about NHSBT or any blood service.**

Platelet units per day, 1 month ahead, method minus seasonal naive (negative = method had lower MAE).
Holm over these three tests at 5%; 'better' needs Holm rejection AND a 95% circular block-bootstrap
interval that excludes zero. Smallest meaningful difference: 7 units/day.

| Comparison | n | MAE diff | 95% CI | HLN-DM p | Holm p | Verdict | Practical | Fit reliability |
|---|---|---|---|---|---|---|---|---|
| ets - naive | 36 | -8.56 | -18.27 to -0.47 | 0.0281 | 0.0844 | couldn't tell them apart | no claim | ok |
| sarima - naive | 36 | -8.14 | -17.38 to -0.51 | 0.0366 | 0.0844 | couldn't tell them apart | no claim | ok |
| regression - naive | 36 | 8.10 | -1.11 to 17.59 | 0.0581 | 0.0844 | couldn't tell them apart | no claim | ok |

SARIMA fallback / omitted share per run and product: primary/platelets fallback 0.00, omitted 0.00 (ok); primary/red_cells fallback 0.00, omitted 0.00 (ok); primary/ffp fallback 0.00, omitted 0.00 (ok); primary/cryo fallback 0.00, omitted 0.00 (ok); covid_sensitivity/platelets fallback 0.25, omitted 0.00 (ok); covid_sensitivity/red_cells fallback 0.28, omitted 0.06 (ok); covid_sensitivity/ffp fallback 0.31, omitted 0.00 (ok); covid_sensitivity/cryo fallback 0.31, omitted 0.00 (ok)

ETS omitted share per run and product: primary/platelets 0.00 (ok); primary/red_cells 0.00 (ok); primary/ffp 0.00 (ok); primary/cryo 0.00 (ok); covid_sensitivity/platelets 0.00 (ok); covid_sensitivity/red_cells 0.69 (treat as unreliable (more than half of origins omitted (fit failed))); covid_sensitivity/ffp 0.00 (ok); covid_sensitivity/cryo 0.11 (ok)

Everything else in the output tables is descriptive.
