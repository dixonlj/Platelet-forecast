# Validation report (preregistered step 4), Aachen 2012-2018, standing order only, R1

Saved: 2026-11-14T04:45:55-05:00 (box time, America/New_York).
No forecast other than the standing order has been run through the new simulation at this point.

Configuration: {"calendar": "mon_sat", "p2": 0.0, "p3": 0.0, "demand": "unit", "shortfall": "heavy_25pct", "lag": "+1"}

- A1 mean waste: simulated 5.22% vs recorded 9.74% (pass if within 1.5 points): FAIL
- A2 emergency units per short day: simulated 5.00 vs recorded 8.82 (pass if 6.6 to 11.0): FAIL
- A3 weekday waste pattern: TVD 0.226 (pass if <= 0.20): FAIL
  - simulated shares: Mon 21.5, Tue 17.9, Wed 35.5, Thu 0.0, Fri 7.3, Sat 5.7, Sun 12.0
  - recorded shares:  Mon 29.4, Tue 19.4, Wed 28.2, Thu 13.2, Fri 6.8, Sat 1.0, Sun 2.0
- A4 (descriptive): yearly correlation simulated vs recorded waste 0.25; yearly MAE 4.41 points

**Calibration FAILS the preregistered validation.**

 year  target_short_days  sim_waste_pct  sim_waste_units  sim_emergency_units  sim_short_days  sim_k  runs_matched  runs_below_target_at_k0  rec_waste_pct  rec_emergency_units  demand  sigma_n2  sigma_n3  sigma_n4
 2012                 40           5.33           223.30               174.93            40.0   1.10            30                        0           7.62                  342    4189      5.69      7.79      9.90
 2013                 31           5.16           233.46               128.44            31.0   1.12            30                        0           6.45                  285    4524      5.91      7.94      9.75
 2014                 21           7.12           273.15                94.11            21.0   0.82            30                        0          11.03                  172    3836      5.24      6.71      8.08
 2015                 38           4.68           227.74               185.92            38.0   1.35            30                        0           8.57                  216    4867      6.13      8.15      9.94
 2016                 35           5.48           234.98               167.39            35.0   0.59            30                        0          12.91                  294    4290      7.34     10.04     12.86
 2017                 42           4.54           230.10               255.24            42.0   1.12            30                        0           9.07                  573    5071      6.81      9.10     11.12
 2018                 31           4.79           267.32               184.27            31.0   1.21            30                        0          12.30                  217    5584      6.95      9.27     11.42
## File fingerprints (SHA-256)
- results/m10/39_validation_report.md: 6d1f3afaf5c9418169f7736de5df145f37b0518e777b80666cea5ebdd7328aca
- results/m10/39_validation_result.json: 5a6d2a207e6d89b591cbeb5e7df7f01c2e2546ce46d13e8e9a309840628bbe21
- results/m10/39_validation_per_year.csv: 6e999d38ce5a89a84af66b82c8bcdecb3a52effb4c7f2589cb7868a9cdeacafe
