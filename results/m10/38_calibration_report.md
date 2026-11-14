# Calibration report (preregistered step 3), Aachen 2009-2011, standing order only

Saved: 2026-11-14T04:41:54-05:00 (box time, America/New_York). Run time 449 s.
No forecast other than the standing order has been run through the new simulation at this point.

## Recorded targets (scoring windows 2009-2011, pooled, from the public file)
- Waste 8.25%; emergency units per short day 6.53; short days per year [25, 26, 40]
- Weekday shares of waste (Mon..Sun): 21.9, 12.9, 33.9, 14.8, 13.6, 1.8, 0.9

## Standing-order cushion units sigma_SO(n) (MAE of n-day totals, previous year; 2009 from 2009 itself)
- 2009: n=2: 3.98, n=3: 5.16, n=4: 6.18
- 2010: n=2: 3.98, n=3: 5.16, n=4: 6.18
- 2011: n=2: 4.58, n=3: 5.98, n=4: 7.32
- Forecast origins that fell back to the 4-week weekday average (warm-up of 2009 only, no 2007 data): {2: 6, 3: 6, 4: 6}

## Grid
- 2,700 combinations (675 simulations per year, logging lag applied afterwards), 30 runs each.
- Loss minimum 6.953; 1 combination(s) within 5% of it.
- Runs never matched (dropped): 0 of 60750 run-years. Run-years already below the target at k = 0 (flagged, k = 0 used): 0.

## Chosen configuration (tie rule applied)
- Calendar Mon-Sat; life on arrival p2=0.0, p3=0.0, p4=1.00; logging lag +1; demand unit; shortfalls heavy_25pct.
- W_sim 7.70% (target 8.25), E_sim 4.00 (target 6.53), TVD 0.195; loss 6.953; departures from v9 base 4.
- Simulated weekday shares (Mon..Sun): 21.1, 16.4, 34.2, 0.0, 9.7, 5.7, 12.9

## For reference: v9 base configuration in the same grid
- W_sim 13.43%, E_sim 3.83, TVD 0.544, loss 59.666 (rank 1382 of 2,700).

## Ten lowest-loss combinations
calendar  p2   p3 lag demand   shortfall  W_sim  E_sim   TVD  loss  departures_from_v9
 mon_sat 0.0 0.00  +1   unit heavy_25pct  7.696  3.998 0.195 6.953                   4
 tue_sun 0.0 0.45  +1   unit        none  8.303  3.423 0.176 7.382                   4
 tue_sun 0.0 0.45  +1   unit    v9_10pct  8.913  3.576 0.187 7.812                   3
 tue_sun 0.1 0.15  +2   unit    v9_10pct  8.655  3.581 0.197 7.915                   4
 tue_sun 0.0 0.30  +1   unit    v9_10pct  7.833  3.591 0.200 7.995                   2
 tue_sun 0.1 0.15  +2   unit        none  8.135  3.437 0.193 7.998                   5
 mon_sat 0.0 0.45  +2   unit        none  8.016  3.529 0.204 8.223                   4
   daily 0.0 0.00  +2    ep2 heavy_25pct  8.209  3.775 0.224 8.394                   5
 mon_sat 0.0 0.45  +2   unit    v9_10pct  8.631  3.637 0.214 8.422                   3
 tue_sun 0.0 0.60  +1   unit        none  9.304  3.424 0.178 8.563                   4

## File fingerprints (SHA-256)
- results/m10/38_calibration_grid.csv: 62aa1e6c45e375df8953867a7aad5519d4df1f1fb35e32bb9c8ae515f8bbf506
- results/m10/38_calibration_choice.json: f863dd3154fffc2deee8fed9ec166ca83f2c7756f369eff116a12531f961a2af
