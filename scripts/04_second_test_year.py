#!/usr/bin/env python3
"""
Milestone 4, step 1: a second test year (2017).

Train on 2008-2016, test on 2017, with the same four baselines and the same
gradient-boosting model as in scripts/02_aachen_real_data.py. Then rerun the
realistic inventory simulation (blood groups, short deliveries, 30 paired
seeds) on 2017, and ask: does gradient boosting's waste edge over the 4-week
weekday average still hold, at the hospital's 2017 shortage-day count?

Educational / advisory only. Never clinical. Public Aachen data only.

Run:  python scripts/04_second_test_year.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import lib_m4 as L

PROJECT_ROOT = L.PROJECT_ROOT
RESULTS = L.RESULTS_DIR
CHARTS = L.CHART_DIR
YEAR = 2017
# Safety unit comes from 2016, so 2017 is not used to set the cushion.
SIGMA_TRAIN_END = pd.Timestamp("2015-12-31")
FC_TRAIN_END = pd.Timestamp("2016-12-31")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    sim_start, eval_start, eval_end = L.year_window(YEAR)
    hospital = L.hospital_actual(df, eval_start, eval_end)
    target_sd = hospital["shortage_days"]

    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    # Forecasts used in 2017: GB trained only through 2016.
    fc17 = {**base, "hgbr": L.m2.hgbr_forecasts(feat, FC_TRAIN_END)}
    # Safety unit: 2016 out-of-sample 2-day miss, with GB trained only through 2015.
    fc16 = {**base, "hgbr": L.m2.hgbr_forecasts(feat, SIGMA_TRAIN_END)}
    sigma = L.sigma_for_year(y, fc16, YEAR)

    # --- average miss per day (and 2-/4-day totals) on 2017 ---
    scores = L.m2.score_period(y, fc17, authors,
                               pd.Timestamp(f"{YEAR}-01-01"),
                               pd.Timestamp(f"{YEAR + 1}-01-01"))
    score_df = pd.DataFrame(scores)
    score_df.to_csv(RESULTS / "04_mae_2017.csv", index=False)

    # --- realistic simulation on 2017, 30 paired seeds ---
    win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fc17.items()}
    models = list(L.m2.MODELS)  # baselines + gradient boosting (not authors)
    res = L.run_config(L.m3.BASE, y, win, sigma, models, year=YEAR)
    summ, matched, k_at = L.matched_table(res, target_sd, models)
    paired = L.paired_vs(matched, baseline="dow4", models=models)
    summ.to_csv(RESULTS / "04_inventory_2017.csv", index=False)
    paired.to_csv(RESULTS / "04_paired_vs_dow4.csv", index=False)
    pd.DataFrame({k: v for k, v in matched.items()}).to_csv(
        RESULTS / "04_per_seed_waste.csv", index_label="seed")
    pd.DataFrame([{"window": f"{eval_start.date()} to {eval_end.date()}",
                   **hospital, "sigma": sigma}]).to_csv(
        RESULTS / "04_hospital_2017_window.csv", index=False)

    gb_wins = int(paired.loc[paired["model"] == "hgbr", "n_better"].iloc[0])
    gb_n = int(paired.loc[paired["model"] == "hgbr", "n"].iloc[0])
    gb_gap = float(paired.loc[paired["model"] == "hgbr", "diff_vs_dow4_mean"].iloc[0])
    gb_waste = float(summ.loc[summ["model"] == "hgbr", "waste_mean"].iloc[0])
    dow4_waste = float(summ.loc[summ["model"] == "dow4", "waste_mean"].iloc[0])
    gb_mae = float(score_df.loc[score_df["model"] == "hgbr", "mae_1d"].iloc[0])
    dow4_mae = float(score_df.loc[score_df["model"] == "dow4", "mae_1d"].iloc[0])

    # One simple chart: waste at the hospital's 2017 short-day count.
    items = [
        ("Use yesterday's\nnumber", matched["naive"], L.m2.COLORS["naive"]),
        ("Average of the\nlast 4 same weekdays", matched["dow4"], L.m2.COLORS["dow4"]),
        ("Machine learning\n(gradient boosting)", matched["hgbr"], L.m2.COLORS["hgbr"]),
        (f"What the hospital\nactually did ({YEAR})",
         np.array([hospital["waste_pct"]]), "#222222"),
    ]
    if gb_gap < 0:
        title = (f"In {YEAR} too, the machine-learning forecast threw away fewer "
                 f"platelets\nthan the 4-week weekday average, with the same number of short days")
    elif gb_gap > 0:
        title = (f"In {YEAR}, the 4-week weekday average threw away fewer platelets\n"
                 f"than the machine-learning forecast, with the same number of short days")
    else:
        title = (f"In {YEAR}, the machine-learning forecast and the 4-week weekday "
                 f"average\nthrew away about the same share of platelets")
    chart = L.simple_bar_chart(
        CHARTS / "m4_second_test_year_2017.png",
        title=title,
        ylabel="Platelets thrown away\n(% of units transfused)",
        items=items,
        footnote=(
            f"Aachen hospital, {YEAR} ({eval_start.date()} to {eval_end.date()}). "
            f"Each option is set so it has the hospital's {target_sd} short days. "
            "Black lines = 5th to 95th percentile of 30 simulated runs. "
            "A learning exercise on public data, not a real result."
        ),
        ylim=(0, max(30, hospital["waste_pct"] + 8)),
        value_fmt="{:.1f}% wasted",
    )

    log_metrics = {
        "year": YEAR,
        "target_shortage_days": target_sd,
        "hospital_waste_pct": hospital["waste_pct"],
        "hgbr_mae_1d": gb_mae,
        "dow4_mae_1d": dow4_mae,
        "hgbr_waste_mean": gb_waste,
        "dow4_waste_mean": dow4_waste,
        "waste_gap_hgbr_minus_dow4": gb_gap,
        "hgbr_wins_out_of_30": gb_wins,
    }
    trackio_msg = L.log_trackio("04_second_test_year", log_metrics, {"year": YEAR})

    lines = []
    def p(msg=""):
        print(msg)
        lines.append(str(msg))
    p("=== Step 1: second test year 2017 ===")
    p(f"Scoring window: {eval_start.date()} to {eval_end.date()}")
    p(f"Hospital actual: {hospital['waste_pct']:.2f}% wasted, "
      f"{target_sd} short days, {hospital['demand']} units transfused.")
    p("Average miss per day (units), 2017:")
    for _, r in score_df.iterrows():
        name = {**L.m2.MODELS, **L.m2.AUTHOR_MODELS}.get(r["model"], r["model"])
        mae = r["mae_1d"]
        mae_s = "n/a (authors published 2- and 4-day totals only)" if pd.isna(mae) else f"{mae:.2f}"
        p(f"  {name:28s}  {mae_s}")
    p(f"Safety-stock unit (2016 2-day average miss): "
      + ", ".join(f"{k}={v:.2f}" for k, v in sigma.items()))
    p(f"Waste at {target_sd} short days (mean of 30 seeds):")
    p(summ.to_string(index=False))
    p(paired.to_string(index=False))
    p(f"Gradient boosting vs 4-week weekday average: "
      f"{gb_wins} of {gb_n} runs had less waste; "
      f"mean waste gap = {gb_gap:+.2f} percentage points "
      f"(GB {gb_waste:.2f}% vs 4-week {dow4_waste:.2f}%).")
    p(f"Chart: {chart}")
    p(f"Trackio: {trackio_msg}")
    (RESULTS / "04_run_log.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
