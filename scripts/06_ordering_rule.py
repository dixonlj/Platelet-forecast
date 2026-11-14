#!/usr/bin/env python3
"""
Milestone 4, step 3: an ordering rule that looks at each blood group and at
how soon units on the shelf (and arriving tomorrow) will expire.

Current rule (script 03): one hospital-wide forecast is split across groups
by population share, then we order
    forecast + safety - units on the shelf - units arriving tomorrow
and treat every unit on the shelf as equally usable.

New rule:
  - Still uses group-specific order-up-to levels (forecast x that group's
    share, plus that group's share of the safety cushion).
  - Walks the next few days forward with the group's expected use, and does
    not count units that will expire before they can be used.
  - The new order arrives two days later, so it is not asked to cover
    tomorrow; leftover stock after that look-ahead is credited against the
    target.

Compared in the realistic simulation, at matched shortage days, against the
current rule. Same forecasts (4-week weekday average and original gradient
boosting), 2017 and 2018, 30 paired seeds.

Educational / advisory only. Never clinical. Public Aachen data only.

Run:  PYTHONPATH=scripts .venv/bin/python scripts/06_ordering_rule.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import lib_m4 as L

RESULTS = L.RESULTS_DIR
CHARTS = L.CHART_DIR


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    feat = L.m2.hgbr_feature_table(y)
    base = L.m2.baseline_forecasts(y)

    inv_rows = []
    paired_rows = []
    year_matched = {}

    for year in (2017, 2018):
        _, eval_start, eval_end = L.year_window(year)
        hospital = L.hospital_actual(df, eval_start, eval_end)
        target_sd = hospital["shortage_days"]

        fcs = {"dow4": base["dow4"],
               "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{year - 1}-12-31"))}
        fcs_sigma = {"dow4": base["dow4"],
                     "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{year - 2}-12-31"))}
        sigma = L.sigma_for_year(y, fcs_sigma, year)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcs.items()}

        # Current rule and new rule, same random draws (same seed0), same forecasts.
        res_cur = L.run_config(L.m3.BASE, y, win, sigma, list(fcs),
                               year=year, order_rule="standard")
        res_new = L.run_config(L.m3.BASE, y, win, sigma, list(fcs),
                               year=year, order_rule="expiry_aware", daily_fc=fcs)

        # Present them as four named options for the table.
        res = {
            "dow4_current": res_cur["dow4"],
            "hgbr_current": res_cur["hgbr"],
            "dow4_expiry": res_new["dow4"],
            "hgbr_expiry": res_new["hgbr"],
        }
        summ, matched, _ = L.matched_table(res, target_sd, list(res))
        summ["year"] = year
        inv_rows.append(summ)
        # Pair the new rule against the current rule, within each forecast.
        for forecast, new, cur in (("dow4", "dow4_expiry", "dow4_current"),
                                   ("hgbr", "hgbr_expiry", "hgbr_current")):
            pr = L.paired_vs({cur: matched[cur], new: matched[new]},
                             baseline=cur, models=[cur, new])
            pr["year"] = year
            pr["forecast"] = forecast
            paired_rows.append(pr)
        year_matched[year] = matched
        print(f"=== {year}  target {target_sd} short days, "
              f"hospital waste {hospital['waste_pct']:.2f}% ===")
        print(summ.to_string(index=False))

    inv_df = pd.concat(inv_rows, ignore_index=True)
    paired_df = pd.concat(paired_rows, ignore_index=True)
    inv_df.to_csv(RESULTS / "06_inventory.csv", index=False)
    paired_df.to_csv(RESULTS / "06_paired.csv", index=False)
    seed_cols = {f"{yr}_{k}": year_matched[yr][k] for yr in year_matched for k in year_matched[yr]}
    pd.DataFrame(seed_cols).to_csv(RESULTS / "06_per_seed_waste.csv", index_label="seed")

    # Chart: 2018, current vs new, for both forecasts (4 bars).
    m = year_matched[2018]
    gap_gb = float(np.nanmean(m["hgbr_expiry"]) - np.nanmean(m["hgbr_current"]))
    gap_d4 = float(np.nanmean(m["dow4_expiry"]) - np.nanmean(m["dow4_current"]))
    if gap_gb < -0.15 and gap_d4 < -0.15:
        title = ("Counting units that will expire before they can be used\n"
                 "cut waste in 2018, for both forecasts, at the same number of short days")
    elif gap_gb > 0.15 and gap_d4 > 0.15:
        title = ("The current ordering rule threw away fewer platelets in 2018\n"
                 "than a rule that skipped units about to expire")
    elif gap_gb < -0.15:
        title = ("Counting units that will expire before they can be used cut waste\n"
                 "in 2018 when the forecast was gradient boosting")
    else:
        title = ("Counting units that will expire before they can be used did not\n"
                 "clearly cut waste in 2018, at the same number of short days")

    items = [
        ("4-week average,\ncurrent rule", m["dow4_current"], L.m2.COLORS["dow4"]),
        ("4-week average,\nnew rule", m["dow4_expiry"], "#5fa2ce"),
        ("Gradient boosting,\ncurrent rule", m["hgbr_current"], L.m2.COLORS["hgbr"]),
        ("Gradient boosting,\nnew rule", m["hgbr_expiry"], "#f1a766"),
    ]
    chart = L.simple_bar_chart(
        CHARTS / "m4_ordering_rule.png",
        title=title,
        ylabel="Platelets thrown away\n(% of units transfused)",
        items=items,
        footnote=(
            "Aachen hospital, 2018, set to the hospital's 31 short days. "
            "The new rule still splits the order by blood-group share, but ignores "
            "units that will expire before they can be used. "
            "Black lines = 5th to 95th percentile of 30 simulated runs. "
            "A learning exercise on public data, not a real result."
        ),
        ylim=(0, 16),
        value_fmt="{:.1f}% wasted",
    )

    metrics = {}
    for year in (2017, 2018):
        sub = inv_df[inv_df["year"] == year].set_index("model")
        for mname in sub.index:
            metrics[f"{year}_{mname}_waste"] = float(sub.loc[mname, "waste_mean"])
        metrics[f"{year}_hgbr_expiry_minus_current"] = (
            float(sub.loc["hgbr_expiry", "waste_mean"] - sub.loc["hgbr_current", "waste_mean"]))
    trackio_msg = L.log_trackio("06_ordering_rule", metrics, {"rule": "expiry_aware"})

    lines = [
        "=== Step 3: group- and expiry-aware ordering ===",
        inv_df.to_string(index=False),
        paired_df.to_string(index=False),
        f"2018 GB new-minus-current waste: {gap_gb:+.2f} pp",
        f"2018 4-week new-minus-current waste: {gap_d4:+.2f} pp",
        f"Chart: {chart}",
        f"Trackio: {trackio_msg}",
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    (RESULTS / "06_run_log.txt").write_text(text)


if __name__ == "__main__":
    main()
