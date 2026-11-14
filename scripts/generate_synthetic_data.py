#!/usr/bin/env python3
"""
Generate a SYNTHETIC daily platelet-demand series for education only.

This is EXAMPLE DATA, not real hospital or patient data.
It is built to *look* like mid-size-hospital platelet use (weekday dips,
holiday slowdowns, occasional trauma spikes) so we can practice forecasting.
Every generating assumption is documented in the project README and in
the comments below, so later we can tell whether a model is just rediscovering
the rules we wrote down.

Never use this output as if it were a real blood bank's history.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42

# Project paths. This file lives in scripts/, data goes in data/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_CSV = DATA_DIR / "SYNTHETIC_daily_platelet_demand.csv"

# Three full calendar years. Last ~6 months of 2025 will be the holdout later.
START_DATE = "2023-01-01"
END_DATE = "2025-12-31"

# Hidden data-generating parameters (see README for the plain-language list).
BASE_BACKGROUND = 16.0  # typical weekday "background" (non-OR) demand, units
ANNUAL_TREND = 0.04  # +4% per year, applied linearly in time
SEASONAL_AMPLITUDE = 0.08  # +/- 8% sinusoid, peak around mid-January
NB_DISPERSION = 12.5  # negative-binomial alpha; larger => closer to Poisson

# Day-of-week multipliers on background demand (Mon=0 ... Sun=6).
# Weekends are clearly lower: fewer elective procedures and outpatient transfusions.
DOW_BACKGROUND_MULT = {
    0: 1.00,  # Monday
    1: 1.02,  # Tuesday
    2: 1.02,  # Wednesday
    3: 1.00,  # Thursday
    4: 0.98,  # Friday
    5: 0.70,  # Saturday
    6: 0.62,  # Sunday
}

# Expected elective-surgery *cases* by weekday. Zero on weekends/holidays.
# These are cases, not platelet units. Each case adds expected platelets below.
DOW_ELECTIVE_CASES_MEAN = {
    0: 6.0,  # Monday
    1: 12.0,  # Tuesday (busier OR slate)
    2: 12.0,  # Wednesday
    3: 11.0,  # Thursday
    4: 7.0,  # Friday
    5: 0.0,  # Saturday
    6: 0.0,  # Sunday
}
HEAVY_SURGERY_PROB = 0.12  # extra-busy elective lists, Tue-Thu only
HEAVY_SURGERY_MULT = 1.5
UNITS_PER_ELECTIVE_CASE = 0.45  # expected platelet units per elective case

# Unpredictable massive-transfusion / trauma days (~4-5 per year).
TRAUMA_DAY_PROB = 0.012
TRAUMA_BASE_EXTRA = 8  # minimum extra units on a trauma day
TRAUMA_POISSON_EXTRA = 10  # additional Poisson noise on top of that

# Observed U.S. federal holidays, 2023-2025, plus a short "near-holiday" list
# where elective slates are often thinned out (day after Thanksgiving, Christmas
# Eve/week, New Year's Eve). These are calendar facts, not hospital data.
FEDERAL_HOLIDAYS = {
    # 2023
    "2023-01-02": "New Year's Day (observed)",
    "2023-01-16": "Martin Luther King Jr. Day",
    "2023-02-20": "Washington's Birthday",
    "2023-05-29": "Memorial Day",
    "2023-06-19": "Juneteenth",
    "2023-07-04": "Independence Day",
    "2023-09-04": "Labor Day",
    "2023-10-09": "Columbus Day / Indigenous Peoples' Day",
    "2023-11-10": "Veterans Day (observed)",
    "2023-11-23": "Thanksgiving",
    "2023-12-25": "Christmas",
    # 2024
    "2024-01-01": "New Year's Day",
    "2024-01-15": "Martin Luther King Jr. Day",
    "2024-02-19": "Washington's Birthday",
    "2024-05-27": "Memorial Day",
    "2024-06-19": "Juneteenth",
    "2024-07-04": "Independence Day",
    "2024-09-02": "Labor Day",
    "2024-10-14": "Columbus Day / Indigenous Peoples' Day",
    "2024-11-11": "Veterans Day",
    "2024-11-28": "Thanksgiving",
    "2024-12-25": "Christmas",
    # 2025
    "2025-01-01": "New Year's Day",
    "2025-01-20": "Martin Luther King Jr. Day",
    "2025-02-17": "Washington's Birthday",
    "2025-05-26": "Memorial Day",
    "2025-06-19": "Juneteenth",
    "2025-07-04": "Independence Day",
    "2025-09-01": "Labor Day",
    "2025-10-13": "Columbus Day / Indigenous Peoples' Day",
    "2025-11-11": "Veterans Day",
    "2025-11-27": "Thanksgiving",
    "2025-12-25": "Christmas",
}

NEAR_HOLIDAYS = {
    "2023-11-24": "Day after Thanksgiving",
    "2023-12-24": "Christmas Eve",
    "2023-12-26": "Day after Christmas",
    "2023-12-31": "New Year's Eve",
    "2024-07-03": "Day before Independence Day",
    "2024-11-29": "Day after Thanksgiving",
    "2024-12-24": "Christmas Eve",
    "2024-12-26": "Day after Christmas",
    "2024-12-31": "New Year's Eve",
    "2025-07-03": "Day before Independence Day",
    "2025-11-28": "Day after Thanksgiving",
    "2025-12-24": "Christmas Eve",
    "2025-12-26": "Day after Christmas",
    "2025-12-31": "New Year's Eve",
}

# Stronger dip on the biggest holidays, milder on other federal holidays.
MAJOR_HOLIDAY_NAMES = {
    "New Year's Day",
    "New Year's Day (observed)",
    "Independence Day",
    "Thanksgiving",
    "Christmas",
}
MAJOR_HOLIDAY_MULT = 0.60
OTHER_HOLIDAY_MULT = 0.70
NEAR_HOLIDAY_MULT = 0.82

# Placeholder supply columns (NOT used in this step's forecasts).
# A crude standing order: a little above typical weekday/weekend use.
STANDING_ORDER_WEEKDAY = 24
STANDING_ORDER_WEEKEND_OR_HOLIDAY = 14
SHELF_LIFE_DAYS = 5


def holiday_multiplier(date_str: str, holiday_name: str | None, is_near: bool) -> float:
    """Return the calendar multiplier for holidays / near-holidays."""
    if holiday_name:
        if holiday_name in MAJOR_HOLIDAY_NAMES:
            return MAJOR_HOLIDAY_MULT
        return OTHER_HOLIDAY_MULT
    if is_near:
        return NEAR_HOLIDAY_MULT
    return 1.0


def negative_binomial_draw(rng: np.random.Generator, mu: float, alpha: float) -> int:
    """
    Draw one count from a negative-binomial distribution with mean `mu`.

    We use the common 'NB2' parameterization: variance = mu + mu^2 / alpha.
    Larger alpha means less extra variation (closer to Poisson).
    """
    mu = max(float(mu), 1e-8)
    # numpy's negative_binomial(n, p) has mean n * (1-p) / p.
    # Set n = alpha, p = alpha / (alpha + mu) to get the mean we want.
    n = alpha
    p = alpha / (alpha + mu)
    return int(rng.negative_binomial(n, p))


def generate(seed: int = SEED) -> pd.DataFrame:
    """Build the full SYNTHETIC daily table and return it."""
    rng = np.random.default_rng(seed)

    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    n_days = len(dates)
    # Time index in years from the start, for the mild trend.
    years_elapsed = np.arange(n_days) / 365.25

    rows = []
    for i, ts in enumerate(dates):
        date_str = ts.strftime("%Y-%m-%d")
        dow = int(ts.dayofweek)  # Mon=0 ... Sun=6
        holiday_name = FEDERAL_HOLIDAYS.get(date_str)
        near_name = NEAR_HOLIDAYS.get(date_str)
        is_holiday = holiday_name is not None
        is_near_holiday = near_name is not None
        cal_mult = holiday_multiplier(date_str, holiday_name, is_near_holiday)

        # Mild annual trend and a gentle winter-peak seasonal wave.
        trend_factor = 1.0 + ANNUAL_TREND * years_elapsed[i]
        day_of_year = int(ts.dayofyear)
        # Peak near day 15 (mid-January), trough in mid-July.
        season_factor = 1.0 + SEASONAL_AMPLITUDE * np.cos(
            2.0 * np.pi * (day_of_year - 15) / 365.25
        )

        mu_background = (
            BASE_BACKGROUND
            * trend_factor
            * season_factor
            * DOW_BACKGROUND_MULT[dow]
            * cal_mult
        )

        # Elective surgery: none on weekends or holidays.
        is_heavy_surgery_day = False
        if (dow <= 4) and (not is_holiday):
            case_mean = DOW_ELECTIVE_CASES_MEAN[dow]
            # Near-holidays keep a thinner slate rather than a full cancel.
            if is_near_holiday:
                case_mean *= 0.4
            if (dow in (1, 2, 3)) and (rng.random() < HEAVY_SURGERY_PROB):
                case_mean *= HEAVY_SURGERY_MULT
                is_heavy_surgery_day = True
            n_surgeries = int(rng.poisson(case_mean))
        else:
            n_surgeries = 0

        mu_surgery = n_surgeries * UNITS_PER_ELECTIVE_CASE

        # Occasional trauma / massive-transfusion spike (unpredictable).
        is_trauma_spike = rng.random() < TRAUMA_DAY_PROB
        if is_trauma_spike:
            trauma_extra = TRAUMA_BASE_EXTRA + int(rng.poisson(TRAUMA_POISSON_EXTRA))
        else:
            trauma_extra = 0

        mu = mu_background + mu_surgery + trauma_extra
        units = negative_binomial_draw(rng, mu, NB_DISPERSION)

        # Placeholder standing-order supply (recorded only; unused this step).
        if is_holiday or dow >= 5:
            standing_order = STANDING_ORDER_WEEKEND_OR_HOLIDAY
        else:
            standing_order = STANDING_ORDER_WEEKDAY

        rows.append(
            {
                "date": date_str,
                "units_transfused": units,
                "weekday": dow,
                "weekday_name": ts.strftime("%A"),
                "month": int(ts.month),
                "year": int(ts.year),
                "is_holiday": int(is_holiday),
                "holiday_name": holiday_name if holiday_name else "",
                "is_near_holiday": int(is_near_holiday),
                "elective_surgery_cases": n_surgeries,
                "is_heavy_surgery_day": int(is_heavy_surgery_day),
                "is_trauma_spike": int(is_trauma_spike),
                # Hidden expected mean from the data-generating process.
                # Do NOT use this as a model feature; it would be cheating.
                "dgp_expected_mean": round(float(mu), 3),
                "assumed_standing_order": standing_order,
                "assumed_shelf_life_days": SHELF_LIFE_DAYS,
            }
        )

    df = pd.DataFrame(rows)
    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = generate(SEED)
    df.to_csv(OUTPUT_CSV, index=False)

    # Quick sanity checks printed to the terminal (not used as model features).
    print("=" * 70)
    print("SYNTHETIC / EXAMPLE DATA — not real hospital or patient data")
    print("=" * 70)
    print(f"Wrote {len(df)} days to {OUTPUT_CSV}")
    print(f"Date range: {df['date'].iloc[0]} through {df['date'].iloc[-1]}")
    print(f"Random seed: {SEED}")
    print()
    print("units_transfused summary:")
    print(df["units_transfused"].describe().to_string())
    print()
    print("Mean units by weekday:")
    by_dow = (
        df.groupby("weekday_name", sort=False)["units_transfused"]
        .mean()
        .reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
    )
    print(by_dow.round(2).to_string())
    print()
    print(f"Holiday days: {int(df['is_holiday'].sum())}")
    print(f"Heavy surgery days: {int(df['is_heavy_surgery_day'].sum())}")
    print(f"Trauma-spike days: {int(df['is_trauma_spike'].sum())}")
    print(f"Overall mean: {df['units_transfused'].mean():.2f} units/day")
    print(f"Overall std:  {df['units_transfused'].std():.2f}")


if __name__ == "__main__":
    main()
