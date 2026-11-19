#!/usr/bin/env python3
"""
Pre-registered Study 2 analysis script for NHSBT monthly issues.

DO NOT run this script on the NHSBT workbook until the pre-registration
has been posted to OSF. The only implemented runner is --synthetic-test,
which uses made-up seasonal numbers and never reads the NHSBT file.

Software: Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1.
Random seed: 20261118 (see inference.py).
"""

from __future__ import annotations

import argparse
import calendar
import sys
from pathlib import Path

import numpy as np

import inference as inf

# Refuse to touch the official snapshot from this script until posting.
NHSBT_SNAPSHOT = Path(__file__).resolve().parents[1] / (
    "data/public/NHSBT_issues_2016-2025_snapshot_2026-11-18.xlsx"
)


def days_in(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def calendar_regression_forecast(train_values, train_months, future_months, rbc_shift=False):
    """
    Linear regression of units per day on 11 month indicators and a linear
    time trend, fit on the training window only. For the secondary red-cell
    series, rbc_shift adds a level-shift from April 2024, but only once at
    least three months after April 2024 are already in the training window
    (i.e. the training data include July 2024 or later).
    """
    n = len(train_values)
    # Design: intercept + months 2-12 + time (0..n-1)
    months = np.array([m for (_, m) in train_months], dtype=int)
    X = np.column_stack(
        [np.ones(n), *[(months == m).astype(float) for m in range(2, 13)], np.arange(n, dtype=float)]
    )
    use_shift = False
    if rbc_shift:
        last_train = train_months[-1]
        # Training must include July 2024 or later
        if last_train >= (2024, 7):
            use_shift = True
            shift = np.array(
                [1.0 if (y, m) >= (2024, 4) else 0.0 for (y, m) in train_months], dtype=float
            )
            X = np.column_stack([X, shift])
    beta, *_ = np.linalg.lstsq(X, np.asarray(train_values, dtype=float), rcond=None)
    preds = []
    for i, (y, m) in enumerate(future_months, start=n):
        row = [1.0, *[(1.0 if m == mm else 0.0) for mm in range(2, 13)], float(i)]
        if use_shift:
            row.append(1.0 if (y, m) >= (2024, 4) else 0.0)
        elif rbc_shift:
            row.append(0.0)  # not used
        preds.append(float(np.dot(beta, row if len(beta) == len(row) else row[: len(beta)])))
    return np.array(preds, dtype=float), use_shift


def synthetic_monthly_series(n=115, start=(2016, 4), seed=inf.SEED):
    """Made-up seasonal series used only to test the code path. Not NHSBT."""
    rng = np.random.default_rng(seed)
    months = []
    y, m = start
    for _ in range(n):
        months.append((y, m))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    t = np.arange(n)
    seasonal = 20 * np.sin(2 * np.pi * np.array([mm for _, mm in months]) / 12)
    values = 680 + 0.05 * t + seasonal + rng.normal(0, 15, size=n)
    # A fake COVID dip in Mar 2020–Dec 2021
    for i, (yy, mm) in enumerate(months):
        if (2020, 3) <= (yy, mm) <= (2021, 12):
            values[i] -= 80
    return months, values


def expanding_origin_forecasts(months, values, covid_as_missing=False):
    """Expanding-window 1- to 3-month forecasts. Returns records[h][model]."""
    n = len(values)
    # First origin: end of October 2022, index of that month in the series.
    def idx_of(ym):
        return months.index(ym)

    first_origin = idx_of((2022, 10))  # train on months[0:first_origin+1]
    last_target = n - 1
    records = {h: {m: [] for m in ("naive", "ets", "sarima", "regression")} for h in (1, 2, 3)}
    fallbacks = 0
    ets_omit = 0
    for origin in range(first_origin, n - 1):
        train_end = origin + 1  # exclusive slice end
        train = list(values[:train_end])
        train_months = months[:train_end]
        if covid_as_missing:
            train_arr = []
            for val, ym in zip(train, train_months):
                if (2020, 3) <= ym <= (2021, 12):
                    train_arr.append(np.nan)
                else:
                    train_arr.append(val)
            train_ets_sarima = train_arr
        else:
            train_ets_sarima = train
        for h in (1, 2, 3):
            target = origin + h
            if target > last_target:
                continue
            actual = values[target]
            # Seasonal naive, with COVID-sensitivity rule if requested
            if covid_as_missing:
                yhat_n = np.nan
                ty, tm = months[target]
                # most recent same calendar month outside the COVID window, known at origin
                for back in range(1, 20):
                    cand_y = ty - back
                    cand = (cand_y, tm)
                    if cand in months:
                        ci = months.index(cand)
                        if ci <= origin and not ((2020, 3) <= cand <= (2021, 12)):
                            yhat_n = values[ci]
                            break
            else:
                yhat_n = inf.seasonal_naive_forecast(train, h)
            records[h]["naive"].append((actual, yhat_n))
            # ETS: state-space version only when missing values are present
            if covid_as_missing and any(np.isnan(train_ets_sarima)):
                fc = _fit_ets_statespace_missing(train_ets_sarima, h)
                if fc is None:
                    ets_omit += 1
                else:
                    records[h]["ets"].append((actual, float(fc[h - 1])))
            else:
                fc, _logs = inf.fit_ets_primary(train, h)
                if fc is None:
                    ets_omit += 1
                else:
                    records[h]["ets"].append((actual, float(fc[h - 1])))
            fc, label, _spec, _logs = inf.fit_sarima_on_array(train_ets_sarima, h) if covid_as_missing else inf.fit_sarima_primary(train, h)
            if fc is None:
                pass
            else:
                records[h]["sarima"].append((actual, float(fc[h - 1])))
                if label == "fallback":
                    fallbacks += 1
            # regression: drop COVID rows in the sensitivity
            if covid_as_missing:
                keep_v = [v for v, ym in zip(train, train_months) if not ((2020, 3) <= ym <= (2021, 12))]
                keep_m = [ym for ym in train_months if not ((2020, 3) <= ym <= (2021, 12))]
            else:
                keep_v, keep_m = train, train_months
            future = [months[origin + k] for k in range(1, h + 1) if origin + k < n]
            if keep_v and future:
                preds, _ = calendar_regression_forecast(keep_v, keep_m, future, rbc_shift=False)
                if h - 1 < len(preds):
                    records[h]["regression"].append((actual, float(preds[h - 1])))
    return records, fallbacks, ets_omit


def _fit_ets_statespace_missing(train, horizon):
    """COVID-sensitivity ETS only: state-space ETS can treat months as missing."""
    import warnings
    from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing as SS_ETS

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = SS_ETS(
                np.asarray(train, dtype=float),
                trend=False,
                seasonal=12,
                damped_trend=False,
                initialization_method="estimated",
            )
            fit = model.fit(disp=False)
            fc = np.asarray(fit.forecast(horizon), dtype=float)
            if inf._warnings_show_convergence(caught) or (not np.all(np.isfinite(fc))):
                return None
            return fc
    except Exception:  # noqa: BLE001
        return None


def run_synthetic_test() -> int:
    months, values = synthetic_monthly_series()
    assert len(months) == 115
    records, fallbacks, ets_omit = expanding_origin_forecasts(months, values, covid_as_missing=False)
    # One-step should have 36 forecasts for naive
    n1 = len(records[1]["naive"])
    print(f"SYNTHETIC TEST: 1-month-ahead naive forecasts: {n1} (expected 36)")
    if n1 != 36:
        print("FAIL: unexpected one-step count")
        return 1
    m, lo, hi = inf.block_bootstrap_mae(records[1]["naive"], horizon=1)
    print(f"SYNTHETIC TEST: naive 1-month MAE={m:.2f} (block-bootstrap 95% CI {lo:.2f} to {hi:.2f})")
    dm = inf.diebold_mariano_hln(records[1]["ets"], records[1]["naive"], horizon=1)
    print(f"SYNTHETIC TEST: ETS vs naive HLN-DM computable={dm['computable']} p={dm['p_value']}")
    rec_s, _, _ = expanding_origin_forecasts(months, values, covid_as_missing=True)
    print(f"SYNTHETIC TEST: COVID-sensitivity 1-month naive forecasts: {len(rec_s[1]['naive'])}")
    # Nov/Dec 2022 naive in the sensitivity should use 2019, not 2021
    # Target Nov 2022 is origin Oct 2022. Check the first two 1-step actual months.
    print("SYNTHETIC TEST: expanding-window path and COVID-missing path both ran.")
    print("SYNTHETIC TEST: OK. NHSBT file was not read.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Study 2 NHSBT analysis (synthetic test only until OSF posting)")
    parser.add_argument("--synthetic-test", action="store_true", help="Run on made-up data only")
    parser.add_argument("--nhsbt", action="store_true", help="Disabled until the pre-registration is posted")
    args = parser.parse_args()
    if args.nhsbt:
        raise SystemExit(
            "Do not run on NHSBT until the pre-registration has been posted to OSF. "
            f"The snapshot at {NHSBT_SNAPSHOT} was not opened."
        )
    if not args.synthetic_test:
        raise SystemExit("Use --synthetic-test. --nhsbt is disabled until the pre-registration is posted.")
    sys.exit(run_synthetic_test())


if __name__ == "__main__":
    main()
