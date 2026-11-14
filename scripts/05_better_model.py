#!/usr/bin/env python3
"""
Milestone 4, step 2: a better gradient-boosting model, and safety stock that
follows each day's uncertainty.

Changes vs the original gradient boosting in script 02:
  - Extra features: a slow trend, the gap between the last week and the last
    four weeks, a combined weekday-and-holiday label, and the number of days
    since / until the nearest public holiday (plus "day before" / "day after").
  - Two extra models that forecast a low and a high band (the 50th and 90th
    percentiles), so the cushion can be large on uncertain days and small on
    predictable ones, instead of the same cushion every day.

We compare the new forecast with a fixed cushion against the same forecast
with a day-by-day cushion, on both 2017 and 2018, in the realistic simulation
at the hospital's shortage-day count for that year.

Educational / advisory only. Never clinical. Public Aachen data only.
scikit-learn is the main toolkit (HistGradientBoostingRegressor).

Run:  PYTHONPATH=scripts .venv/bin/python scripts/05_better_model.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import lib_m4 as L

RESULTS = L.RESULTS_DIR
CHARTS = L.CHART_DIR
HGBR_PARAMS = dict(L.m2.HGBR_PARAMS)

NEW_FEATURES = [
    "h", "dow", "month", "holiday", "origin_holiday",
    "lag1", "lag7", "lag14", "roll7", "roll28",
    "t_years", "recent_minus_month", "cal_bin",
    "days_since_hol", "days_until_hol",
    "day_before_hol", "day_after_hol",
]
CAT_FEATURES = ["dow", "month", "cal_bin"]


def _holiday_distances(index: pd.DatetimeIndex, hol: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Days since the last holiday and until the next, on this index.

    Holidays just outside the series (previous December, next January) are
    included so the ends of the file are not missing a neighbour.
    """
    years = range(index.year.min() - 1, index.year.max() + 2)
    holset = L.m2.holidays.Germany(subdiv="NW", years=years)
    hol_dates = pd.DatetimeIndex(sorted(pd.Timestamp(d) for d in holset)).unique()
    # "since": distance to the latest holiday on or before the date
    # "until": distance to the earliest holiday on or after the date
    since = np.empty(len(index), dtype=float)
    until = np.empty(len(index), dtype=float)
    j_prev, j_next = 0, 0
    hol_dates = hol_dates.sort_values()
    for i, d in enumerate(index):
        while j_prev + 1 < len(hol_dates) and hol_dates[j_prev + 1] <= d:
            j_prev += 1
        while j_next < len(hol_dates) and hol_dates[j_next] < d:
            j_next += 1
        since[i] = (d - hol_dates[j_prev]).days if hol_dates[j_prev] <= d else 365
        until[i] = (hol_dates[j_next] - d).days if j_next < len(hol_dates) else 365
    return since, until


def better_feature_table(y: pd.Series) -> pd.DataFrame:
    """Like script 02's table, plus trend, calendar interaction, and holiday distance."""
    hol = pd.Series(L.m2.nrw_holiday_flags(y.index), index=y.index)
    since, until = _holiday_distances(y.index, hol)
    t0 = y.index[0]
    rows = []
    for h in range(1, L.m2.MAX_H + 1):
        target_dates = y.index + pd.Timedelta(days=h)
        # Holiday flags / distances on the TARGET day, looked up by shifting
        # the origin-day arrays (known in advance for calendar fields).
        f = pd.DataFrame(index=y.index)
        f["origin"] = y.index
        f["h"] = h
        f["dow"] = target_dates.dayofweek
        f["month"] = target_dates.month
        f["holiday"] = L.m2.nrw_holiday_flags(target_dates)
        f["origin_holiday"] = hol.values
        f["lag1"] = y.values
        f["lag7"] = y.shift(7 - h).values
        f["lag14"] = y.shift(14 - h).values
        f["roll7"] = y.rolling(7).mean().values
        f["roll28"] = y.rolling(28).mean().values
        f["t_years"] = (y.index - t0).days / 365.25
        f["recent_minus_month"] = f["roll7"] - f["roll28"]
        f["cal_bin"] = f["dow"] + 8 * f["holiday"]
        # Holiday distances are computed on the target dates (known in advance).
        t_since, t_until = _holiday_distances(target_dates, hol)
        f["days_since_hol"] = t_since
        f["days_until_hol"] = t_until
        f["day_before_hol"] = (f["days_until_hol"] == 1).astype(int)
        f["day_after_hol"] = (f["days_since_hol"] == 1).astype(int)
        f["target"] = y.shift(-h).values
        f["target_date"] = target_dates
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


def fit_predict(feat: pd.DataFrame, train_end: pd.Timestamp, *,
                loss: str = "squared_error", quantile: float | None = None) -> pd.DataFrame:
    ok = feat[NEW_FEATURES].notna().all(axis=1)
    train = feat[ok & feat["target"].notna() & (feat["target_date"] <= train_end)]
    params = dict(HGBR_PARAMS)
    params["loss"] = loss
    if quantile is not None:
        params["quantile"] = quantile
    cat_idx = [NEW_FEATURES.index(c) for c in CAT_FEATURES]
    model = HistGradientBoostingRegressor(**params, categorical_features=cat_idx)
    model.fit(train[NEW_FEATURES], train["target"])
    pred = pd.Series(np.nan, index=feat.index)
    pred[ok] = model.predict(feat.loc[ok, NEW_FEATURES])
    return feat.assign(pred=pred).pivot(index="origin", columns="h", values="pred")


def window_spread(q50: pd.DataFrame, q90: pd.DataFrame, n: int) -> pd.Series:
    """Day-specific uncertainty: high band minus typical band, for a 2- or 4-day window."""
    cols = list(range(1, n + 1))
    spread = q90[cols].sum(axis=1, min_count=n) - q50[cols].sum(axis=1, min_count=n)
    return spread.clip(lower=0.0)


def forecasts_for(y, feat_old, feat_new, train_end: pd.Timestamp) -> dict:
    base = L.m2.baseline_forecasts(y)
    old = L.m2.hgbr_forecasts(feat_old, train_end)
    new = fit_predict(feat_new, train_end, loss="squared_error")
    q50 = fit_predict(feat_new, train_end, loss="quantile", quantile=0.5)
    q90 = fit_predict(feat_new, train_end, loss="quantile", quantile=0.9)
    return {
        "dow4": base["dow4"],
        "hgbr": old,
        "hgbr_new": new,
        "q50": q50,
        "q90": q90,
        "naive": base["naive"],
        "last7": base["last7"],
        "same_dow": base["same_dow"],
    }


def pack_windows(fcs):
    return {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4))
            for k, fc in fcs.items() if k not in ("q50", "q90")}


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    feat_old = L.m2.hgbr_feature_table(y)
    feat_new = better_feature_table(y)

    score_rows = []
    inv_rows = []
    paired_rows = []
    per_seed = {}
    year_matched = {}
    hospitals = {}

    for year in (2017, 2018):
        _, eval_start, eval_end = L.year_window(year)
        hospital = L.hospital_actual(df, eval_start, eval_end)
        hospitals[year] = hospital
        target_sd = hospital["shortage_days"]

        fcs_test = forecasts_for(y, feat_old, feat_new, pd.Timestamp(f"{year - 1}-12-31"))
        fcs_sigma = forecasts_for(y, feat_old, feat_new, pd.Timestamp(f"{year - 2}-12-31"))

        # Score average miss per day on the test year (point forecasts only).
        point = {k: fcs_test[k] for k in ("naive", "last7", "same_dow", "dow4", "hgbr", "hgbr_new")}
        # q50 is a median forecast: score it too, as "new model, typical-day band".
        point["hgbr_q50"] = fcs_test["q50"]
        scores = L.m2.score_period(y, point, authors,
                                   pd.Timestamp(f"{year}-01-01"),
                                   pd.Timestamp(f"{year + 1}-01-01"))
        for r in scores:
            r["year"] = year
            score_rows.append(r)

        sigma_src = {k: fcs_sigma[k] for k in ("dow4", "hgbr", "hgbr_new", "naive", "last7", "same_dow")}
        sigma = L.sigma_for_year(y, sigma_src, year)
        # The quantile-safety run uses the same point forecast as hgbr_new,
        # so it shares that model's 2-day miss as a fallback if a day is missing.
        sigma["hgbr_new_q"] = sigma["hgbr_new"]

        win = pack_windows(fcs_test)
        # Quantile-safety model places the same hgbr_new point forecast, but a
        # day-varying cushion equal to (high band - typical band) for the window.
        win["hgbr_new_q"] = win["hgbr_new"]
        safety_daily = {
            "hgbr_new_q": {
                2: window_spread(fcs_test["q50"], fcs_test["q90"], 2),
                4: window_spread(fcs_test["q50"], fcs_test["q90"], 4),
            }
        }
        models = ["dow4", "hgbr", "hgbr_new", "hgbr_new_q"]
        res = L.run_config(L.m3.BASE, y, win, sigma, models,
                           year=year, safety_daily=safety_daily)
        summ, matched, _ = L.matched_table(res, target_sd, models)
        summ["year"] = year
        inv_rows.append(summ)
        paired = L.paired_vs(matched, baseline="hgbr_new", models=models)
        paired["year"] = year
        paired_rows.append(paired)
        year_matched[year] = matched
        for k, v in matched.items():
            per_seed[f"{year}_{k}"] = v

        print(f"=== {year}  hospital {hospital['waste_pct']:.2f}% waste, "
              f"{target_sd} short days ===")
        print(summ.to_string(index=False))
        print(paired.to_string(index=False))

    score_df = pd.DataFrame(score_rows)
    inv_df = pd.concat(inv_rows, ignore_index=True)
    paired_df = pd.concat(paired_rows, ignore_index=True)
    score_df.to_csv(RESULTS / "05_mae.csv", index=False)
    inv_df.to_csv(RESULTS / "05_inventory.csv", index=False)
    paired_df.to_csv(RESULTS / "05_paired.csv", index=False)
    pd.DataFrame(per_seed).to_csv(RESULTS / "05_per_seed_waste.csv", index_label="seed")

    # Chart: one idea — does a day-by-day cushion beat a fixed cushion?
    # Four bars: 2017 fixed, 2017 day-by-day, 2018 fixed, 2018 day-by-day.
    m17f = year_matched[2017]["hgbr_new"]
    m17q = year_matched[2017]["hgbr_new_q"]
    m18f = year_matched[2018]["hgbr_new"]
    m18q = year_matched[2018]["hgbr_new_q"]
    gap17 = float(np.nanmean(m17q) - np.nanmean(m17f))
    gap18 = float(np.nanmean(m18q) - np.nanmean(m18f))
    # Honest title from the numbers.
    if gap17 < -0.15 and gap18 < -0.15:
        title = ("Letting the cushion follow each day's uncertainty threw away\n"
                 "fewer platelets than a fixed cushion, in both 2017 and 2018")
    elif gap17 > 0.15 and gap18 > 0.15:
        title = ("A fixed cushion threw away fewer platelets than a cushion\n"
                 "that followed each day's uncertainty, in both 2017 and 2018")
    elif (gap17 + gap18) / 2 < 0:
        title = ("Letting the cushion follow each day's uncertainty helped a little\n"
                 "overall, but the gain was small and not the same every year")
    else:
        title = ("Letting the cushion follow each day's uncertainty did not clearly\n"
                 "beat a fixed cushion on these two years")

    items = [
        ("2017,\nfixed cushion", m17f, "#1f77b4"),
        ("2017,\ncushion follows\nthe day's uncertainty", m17q, "#5fa2ce"),
        ("2018,\nfixed cushion", m18f, "#d95f02"),
        ("2018,\ncushion follows\nthe day's uncertainty", m18q, "#f1a766"),
    ]
    chart = L.simple_bar_chart(
        CHARTS / "m4_better_model_quantile_safety.png",
        title=title,
        ylabel="Platelets thrown away\n(% of units transfused)",
        items=items,
        footnote=(
            "Same improved machine-learning forecast in every bar. "
            "Each bar is set to the hospital's short-day count for that year "
            f"(42 days in 2017, 31 days in 2018). "
            "Black lines = 5th to 95th percentile of 30 simulated runs. "
            "A learning exercise on public Aachen data, not a real result."
        ),
        ylim=(0, 16),
        value_fmt="{:.1f}% wasted",
    )

    # Trackio: key numbers for both years.
    metrics = {}
    for year in (2017, 2018):
        sub = inv_df[inv_df["year"] == year].set_index("model")
        mae = score_df[(score_df["year"] == year) & (score_df["model"] == "hgbr_new")]["mae_1d"]
        mae_old = score_df[(score_df["year"] == year) & (score_df["model"] == "hgbr")]["mae_1d"]
        metrics[f"{year}_hgbr_new_mae"] = float(mae.iloc[0])
        metrics[f"{year}_hgbr_old_mae"] = float(mae_old.iloc[0])
        for m in ("dow4", "hgbr", "hgbr_new", "hgbr_new_q"):
            metrics[f"{year}_{m}_waste"] = float(sub.loc[m, "waste_mean"])
        metrics[f"{year}_q_minus_fixed"] = float(sub.loc["hgbr_new_q", "waste_mean"]
                                                 - sub.loc["hgbr_new", "waste_mean"])
    trackio_msg = L.log_trackio("05_better_model", metrics, {"models": "dow4,hgbr,hgbr_new,hgbr_new_q"})

    log = []
    log.append("=== Step 2: better model + day-by-day safety ===")
    log.append(score_df.to_string(index=False))
    log.append(inv_df.to_string(index=False))
    log.append(paired_df.to_string(index=False))
    log.append(f"2017 quantile-minus-fixed waste: {gap17:+.2f} pp")
    log.append(f"2018 quantile-minus-fixed waste: {gap18:+.2f} pp")
    log.append(f"Chart: {chart}")
    log.append(f"Trackio: {trackio_msg}")
    text = "\n".join(log) + "\n"
    print(text)
    (RESULTS / "05_run_log.txt").write_text(text)


if __name__ == "__main__":
    main()
