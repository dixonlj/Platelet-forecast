#!/usr/bin/env python3
"""
Platelet demand forecasting — baselines, one ML model, and a simple ordering sim.

Educational / advisory only. Never clinical. Uses SYNTHETIC example data.

What this script does, in order:
  1. Load the synthetic daily series (generate it first if the CSV is missing).
  2. Build one-step-ahead baselines and a gradient-boosting model, with
     features that use only information known at forecast time (no leakage).
  3. Score them with rolling-origin (expanding-window) cross-validation and
     with a final time-based holdout (last 6 months). No shuffling.
  4. Run the same simple 5-day shelf-life ordering policy on each model's
     forecasts over the holdout, and compare waste and shortages.
  5. Save a metrics table and a few clear charts.

Read the comments as you go — they are written for someone comfortable in
the lab who is teaching themselves this material, not for a data scientist.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit

# Make the generate script importable when we run this file directly.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_synthetic_data import OUTPUT_CSV, SEED, generate  # noqa: E402

DATA_PATH = OUTPUT_CSV
CHART_DIR = PROJECT_ROOT / "charts"
RESULTS_DIR = PROJECT_ROOT / "results"

# Last 6 months of the series are the final holdout (test) period.
TEST_START = pd.Timestamp("2025-07-01")

# Rolling window lengths used as features / in the 4-week weekday baseline.
LAGS = (1, 7, 14)
ROLL_WINDOWS = (7, 28)
MIN_HISTORY = 28  # need 28 prior days before the first 4-week / roll-28 feature

# Gradient boosting: small and plain on purpose. We are not tuning hard,
# because on synthetic data a fancy search would mostly overfit our own rules.
HGBR_PARAMS = dict(
    max_depth=3,
    learning_rate=0.08,
    max_iter=200,
    l2_regularization=0.1,
    random_state=SEED,
)

# Inventory policy (identical rule for every model).
# Each day we order up to: forecast(t+1) + forecast(t+2) + safety stock,
# minus what is already on the shelf. Safety stock = SAFETY_K * that model's
# 1-step MAE on the training period. SAFETY_K was chosen ahead of time.
SAFETY_K = 1.5
SHELF_LIFE_DAYS = 5  # usable on arrival day and the next 4 days, then expires
LEAD_TIME_DAYS = 1  # order tonight, units arrive tomorrow morning
INITIAL_INVENTORY_DAYS_OF_MEAN = 2.0  # starting stock, same for every model

# Cross-validation folds on the training period only.
N_CV_SPLITS = 6


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def mae(y_true, y_pred) -> float:
    """Mean Absolute Error: average of |actual - forecast|, in units."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def wape(y_true, y_pred) -> float:
    """
    Weighted Absolute Percentage Error, as a percent.

    WAPE = 100 * sum(|actual - forecast|) / sum(actual)

    This is safer than MAPE (which divides each day by that day's actual).
    A single quiet day with 2 units and a forecast of 4 would be a 100% MAPE
    error even though it is only 2 units off. WAPE treats those 2 units in
    proportion to total demand.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = float(np.sum(y_true))
    if denom == 0:
        return float("nan")
    return float(100.0 * np.sum(np.abs(y_true - y_pred)) / denom)


def mape_safe(y_true, y_pred) -> float:
    """MAPE in percent, skipping any days where actual demand is 0."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return float("nan")
    return float(100.0 * np.mean(np.abs(y_true[mask] - y_pred[mask]) / y_true[mask]))


# ---------------------------------------------------------------------------
# Data loading and feature construction (no leakage)
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """Load the synthetic CSV, generating it first if needed."""
    if not DATA_PATH.exists():
        print("Synthetic CSV not found — generating it now...")
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_raw = generate(SEED)
        df_raw.to_csv(DATA_PATH, index=False)
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def add_calendar_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Make sure weekday / month / holiday flag are present and numeric."""
    out = df.copy()
    out["weekday"] = out["date"].dt.dayofweek
    out["month"] = out["date"].dt.month
    out["is_holiday"] = out["is_holiday"].astype(int)
    return out


def build_origin_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a table keyed by *forecast origin* date t.

    At the end of day t we already know today's transfusions. We may then
    forecast day t+1 (1-step) and day t+2 (2-step). Every feature below is
    knowable at that moment:

      - lag_1, lag_7, lag_14 are y_t, y_{t-6}, y_{t-13}
      - roll_7  is the mean of y_{t-6} .. y_t  (the last 7 observed days)
      - roll_28 is the mean of y_{t-27} .. y_t
      - target-day calendar fields (weekday, month, holiday) are known in
        advance because they come from the calendar, not from demand.

    We deliberately do NOT include elective_surgery_cases, trauma flags, or
    dgp_expected_mean. Those were used to *create* the fake data; using them
    as features would be leaking the answer key.
    """
    d = add_calendar_columns(df)
    y = d["units_transfused"].astype(float)

    feat = pd.DataFrame({"origin_date": d["date"]})
    feat["y_t"] = y.values

    # Lags and rolling means of *observed* demand through day t (the origin).
    feat["lag_1"] = y.values  # most recent day, which is t itself
    feat["lag_7"] = y.shift(6).values  # 7 days before the target t+1 is t-6
    feat["lag_14"] = y.shift(13).values
    feat["roll_7"] = y.rolling(7, min_periods=7).mean().values
    feat["roll_28"] = y.rolling(28, min_periods=28).mean().values

    # 1-step target and its calendar (day t+1).
    feat["y_t1"] = y.shift(-1).values
    feat["date_t1"] = d["date"].shift(-1).values
    feat["weekday_t1"] = d["weekday"].shift(-1).values
    feat["month_t1"] = d["month"].shift(-1).values
    feat["is_holiday_t1"] = d["is_holiday"].shift(-1).values

    # 2-step target and its calendar (day t+2).
    feat["y_t2"] = y.shift(-2).values
    feat["date_t2"] = d["date"].shift(-2).values
    feat["weekday_t2"] = d["weekday"].shift(-2).values
    feat["month_t2"] = d["month"].shift(-2).values
    feat["is_holiday_t2"] = d["is_holiday"].shift(-2).values

    # Same-weekday history as of origin t, used by the weekday baselines.
    # For a 1-step forecast of t+1, "last week, same weekday" is y_{t-6}.
    # The 4-week weekday average uses t-6, t-13, t-20, t-27.
    feat["same_dow_lag1w_t1"] = y.shift(6).values
    feat["same_dow_lag2w_t1"] = y.shift(13).values
    feat["same_dow_lag3w_t1"] = y.shift(20).values
    feat["same_dow_lag4w_t1"] = y.shift(27).values
    # For a 2-step forecast of t+2, "last week, same weekday" is y_{t-5}.
    feat["same_dow_lag1w_t2"] = y.shift(5).values
    feat["same_dow_lag2w_t2"] = y.shift(12).values
    feat["same_dow_lag3w_t2"] = y.shift(19).values
    feat["same_dow_lag4w_t2"] = y.shift(26).values

    # Drop rows that do not have a full 28-day history or a 2-step target.
    feat = feat.dropna().reset_index(drop=True)
    return feat


FEATURE_COLS_H1 = [
    "weekday_t1",
    "month_t1",
    "is_holiday_t1",
    "lag_1",
    "lag_7",
    "lag_14",
    "roll_7",
    "roll_28",
]
FEATURE_COLS_H2 = [
    "weekday_t2",
    "month_t2",
    "is_holiday_t2",
    "lag_1",
    "lag_7",
    "lag_14",
    "roll_7",
    "roll_28",
]
# weekday and month are categorical (a Tuesday is not "2 more" than a Sunday).
CATEGORICAL_H1 = [0, 1]  # column positions in FEATURE_COLS_H1
CATEGORICAL_H2 = [0, 1]


# ---------------------------------------------------------------------------
# Forecasts
# ---------------------------------------------------------------------------
def baseline_forecasts(feat: pd.DataFrame) -> pd.DataFrame:
    """
    Four simple 1-step and 2-step baselines, all computable at origin t.

    (a) Naive: tomorrow (and the day after) will look like today.
    (b) Last-7-day average: the mean of the last 7 observed days.
    (c) Same-weekday-last-week: last Tuesday for next Tuesday, etc.
    (d) 4-week weekday average: mean of the last four same weekdays.
    """
    out = feat.copy()
    out["pred_naive_t1"] = out["lag_1"]
    out["pred_naive_t2"] = out["lag_1"]

    out["pred_last7_t1"] = out["roll_7"]
    out["pred_last7_t2"] = out["roll_7"]

    out["pred_same_dow_t1"] = out["same_dow_lag1w_t1"]
    out["pred_same_dow_t2"] = out["same_dow_lag1w_t2"]

    out["pred_dow4_t1"] = out[
        ["same_dow_lag1w_t1", "same_dow_lag2w_t1", "same_dow_lag3w_t1", "same_dow_lag4w_t1"]
    ].mean(axis=1)
    out["pred_dow4_t2"] = out[
        ["same_dow_lag1w_t2", "same_dow_lag2w_t2", "same_dow_lag3w_t2", "same_dow_lag4w_t2"]
    ].mean(axis=1)
    return out


def fit_hgbr(train_feat: pd.DataFrame):
    """
    Fit two gradient-boosting models: one for 1-step, one for 2-step.

    Direct 2-step (a second model that predicts t+2 from origin t) avoids
    feeding a t+1 *prediction* back in as if it were a real lag.
    """
    model_h1 = HistGradientBoostingRegressor(**HGBR_PARAMS, categorical_features=CATEGORICAL_H1)
    model_h2 = HistGradientBoostingRegressor(**HGBR_PARAMS, categorical_features=CATEGORICAL_H2)
    model_h1.fit(train_feat[FEATURE_COLS_H1], train_feat["y_t1"])
    model_h2.fit(train_feat[FEATURE_COLS_H2], train_feat["y_t2"])
    return model_h1, model_h2


def predict_hgbr(model_h1, model_h2, feat: pd.DataFrame) -> pd.DataFrame:
    """Add clipped (non-negative) HGBR forecasts to a feature frame."""
    out = feat.copy()
    out["pred_hgbr_t1"] = np.clip(model_h1.predict(out[FEATURE_COLS_H1]), 0, None)
    out["pred_hgbr_t2"] = np.clip(model_h2.predict(out[FEATURE_COLS_H2]), 0, None)
    return out


# Short display names, in a stable order, used in tables and charts.
MODELS = {
    "naive": "Naive (yesterday)",
    "last7": "Last-7-day average",
    "same_dow": "Same weekday last week",
    "dow4": "4-week weekday average",
    "hgbr": "Gradient boosting",
}


def score_rows(frame: pd.DataFrame, pred_col: str, actual_col: str = "y_t1") -> dict:
    """Return MAE, WAPE, and MAPE for one prediction column."""
    y = frame[actual_col].to_numpy()
    yhat = frame[pred_col].to_numpy()
    return {
        "mae": mae(y, yhat),
        "wape": wape(y, yhat),
        "mape": mape_safe(y, yhat),
        "n_days": int(len(frame)),
    }


# ---------------------------------------------------------------------------
# Rolling-origin / expanding-window cross-validation
# ---------------------------------------------------------------------------
def run_timeseries_cv(train_feat: pd.DataFrame) -> pd.DataFrame:
    """
    Expanding-window CV with sklearn's TimeSeriesSplit, training period only.

    Each fold trains on all earlier data and scores the next block of days.
    We never shuffle, and later days are never used to predict earlier days.
    Baselines have no fitted parameters; we still score them on the same
    fold test blocks so the comparison is fair.
    """
    splitter = TimeSeriesSplit(n_splits=N_CV_SPLITS)
    records = []

    for fold, (tr_idx, te_idx) in enumerate(splitter.split(train_feat), start=1):
        tr = train_feat.iloc[tr_idx]
        te = train_feat.iloc[te_idx]
        te_base = baseline_forecasts(te)
        model_h1, model_h2 = fit_hgbr(tr)
        te_ml = predict_hgbr(model_h1, model_h2, te_base)

        for key, label in MODELS.items():
            s = score_rows(te_ml, f"pred_{key}_t1", "y_t1")
            records.append(
                {
                    "fold": fold,
                    "model_key": key,
                    "model": label,
                    "fold_start": te["date_t1"].min(),
                    "fold_end": te["date_t1"].max(),
                    **s,
                }
            )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Simple FIFO ordering simulation (5-day shelf life)
# ---------------------------------------------------------------------------
def starting_inventory(mean_demand: float, first_day: pd.Timestamp) -> list[dict]:
    """
    Identical opening stock for every model: about two days of mean demand,
    split across three lots with 2, 3, and 4 days of remaining life so they
    do not all expire at once and are not all brand new.
    """
    total = max(1, int(round(INITIAL_INVENTORY_DAYS_OF_MEAN * mean_demand)))
    # Split as evenly as we can across the three lots.
    q1, q2, q3 = total // 3, total // 3, total - 2 * (total // 3)
    # Remaining life of 2, 3, 4 days means expiry at end of first_day+1, +2, +3.
    return [
        {"qty": q1, "expiry": first_day + pd.Timedelta(days=1)},
        {"qty": q2, "expiry": first_day + pd.Timedelta(days=2)},
        {"qty": q3, "expiry": first_day + pd.Timedelta(days=3)},
    ]


def on_hand_qty(lots: list[dict]) -> int:
    return int(sum(lot["qty"] for lot in lots))


def issue_fifo(lots: list[dict], demand: int) -> tuple[list[dict], int, int]:
    """Issue oldest units first. Returns (updated lots, issued, short)."""
    remaining = int(demand)
    issued = 0
    # Oldest expiry first; stable so equal expiries keep arrival order.
    lots = sorted(lots, key=lambda lot: lot["expiry"])
    for lot in lots:
        if remaining <= 0:
            break
        take = min(lot["qty"], remaining)
        lot["qty"] -= take
        remaining -= take
        issued += take
    lots = [lot for lot in lots if lot["qty"] > 0]
    short = remaining
    return lots, issued, short


def expire_lots(lots: list[dict], today: pd.Timestamp) -> tuple[list[dict], int]:
    """Units whose expiry date is today expire at the end of the day."""
    expired = sum(lot["qty"] for lot in lots if lot["expiry"] <= today)
    lots = [lot for lot in lots if lot["expiry"] > today]
    return lots, int(expired)


def simulate_inventory(
    sim_days: pd.DataFrame,
    safety_stock: float,
    initial_lots: list[dict],
    opening_delivery: int = 0,
) -> tuple[dict, pd.DataFrame]:
    """
    Inventory walk over sim_days.

    sim_days must have one row per calendar day we issue against, with:
      date, actual, pred_t1, pred_t2
    where pred_t1/pred_t2 were produced at the *end of that same date*
    (i.e. after that day's demand is known). The order placed that evening
    arrives the next morning.

    Timing, written out:
      1. Morning: yesterday evening's order arrives (5-day life starts today).
      2. Daytime: issue FIFO against today's actual demand. Unmet = shortage.
      3. End of day: units whose expiry is today are wasted.
      4. End of day: order = max(0, round(pred_t1 + pred_t2 + safety - on_hand)).
    """
    lots = [lot.copy() for lot in initial_lots]
    # Units ordered the evening before the first simulated day, arriving this morning.
    pending_arrival = int(opening_delivery)

    units_issued = 0
    units_expired = 0
    units_short = 0
    shortage_days = 0
    units_received = 0
    daily = []

    for _, row in sim_days.iterrows():
        today = pd.Timestamp(row["date"])

        if pending_arrival > 0:
            expiry = today + pd.Timedelta(days=SHELF_LIFE_DAYS - 1)
            lots.append({"qty": int(pending_arrival), "expiry": expiry})
            units_received += int(pending_arrival)
            pending_arrival = 0

        demand = int(row["actual"])
        lots, issued, short = issue_fifo(lots, demand)
        units_issued += issued
        units_short += short
        if short > 0:
            shortage_days += 1

        lots, expired = expire_lots(lots, today)
        units_expired += expired

        yhat1 = float(row["pred_t1"])
        yhat2 = float(row["pred_t2"])
        on_hand = on_hand_qty(lots)
        order_up_to = yhat1 + yhat2 + float(safety_stock)
        order = max(0, int(round(order_up_to - on_hand)))
        pending_arrival = order

        daily.append(
            {
                "date": today,
                "actual": demand,
                "pred_t1": yhat1,
                "pred_t2": yhat2,
                "issued": issued,
                "short": short,
                "expired": expired,
                "on_hand_eod": on_hand,
                "order_placed": order,
                "safety_stock": float(safety_stock),
            }
        )

    # Any leftover pending order would arrive after the last day; we do not
    # count it as received or wasted. Ending on-hand is also left unused.
    issued_plus_expired = units_issued + units_expired
    wastage_rate = (
        100.0 * units_expired / issued_plus_expired if issued_plus_expired else float("nan")
    )
    summary = {
        "units_issued": units_issued,
        "units_expired": units_expired,
        "units_received": units_received,
        "units_short": units_short,
        "shortage_days": shortage_days,
        "wastage_rate_pct": wastage_rate,
        "n_days": int(len(sim_days)),
        "ending_on_hand": on_hand_qty(lots),
        "safety_stock": float(safety_stock),
    }
    return summary, pd.DataFrame(daily)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def _style_axes(ax):
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def chart_actual_vs_forecasts(
    holdout_days: pd.DataFrame,
    best_baseline_key: str,
    path: Path,
) -> None:
    """Line chart of actual demand vs best baseline vs gradient boosting."""
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(
        holdout_days["date"],
        holdout_days["actual"],
        color="#222222",
        linewidth=1.4,
        label="Actual (synthetic)",
    )
    ax.plot(
        holdout_days["date"],
        holdout_days[f"pred_{best_baseline_key}_t1"],
        color="#1f77b4",
        linewidth=1.2,
        alpha=0.9,
        label=f"Best baseline: {MODELS[best_baseline_key]}",
    )
    ax.plot(
        holdout_days["date"],
        holdout_days["pred_hgbr_t1"],
        color="#d95f02",
        linewidth=1.2,
        alpha=0.9,
        label="Gradient boosting",
    )
    ax.set_title("Holdout period: actual daily units vs forecasts (synthetic data)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Platelet units")
    ax.legend(loc="upper right", frameon=False)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_day_of_week(df: pd.DataFrame, path: Path) -> None:
    """Bar chart of mean daily use by weekday, for the whole synthetic series."""
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = (
        df.groupby(df["date"].dt.day_name())["units_transfused"]
        .agg(["mean", "std"])
        .reindex(order)
    )
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    colors = ["#4c78a8"] * 5 + ["#9ecae1"] * 2
    ax.bar(order, grouped["mean"], yerr=grouped["std"], color=colors, capsize=3, ecolor="#555555")
    ax.set_title("Mean daily platelet units by weekday (synthetic, full series)")
    ax.set_ylabel("Units (mean ± 1 SD)")
    ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_inventory_comparison(inv_table: pd.DataFrame, path: Path) -> None:
    """
    Main chart: wastage rate and shortage days for each model, same policy.
    Two side-by-side panels so the units stay readable.
    """
    labels = inv_table["model"].tolist()
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.0))

    bars1 = ax1.bar(x, inv_table["wastage_rate_pct"], color="#6baed6")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha="right")
    ax1.set_ylabel("Wastage rate (%)")
    ax1.set_title("Expired units / (issued + expired)")
    _style_axes(ax1)
    for bar, val, expired in zip(bars1, inv_table["wastage_rate_pct"], inv_table["units_expired"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.1f}%\n({int(expired)} u)",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax1.set_ylim(0, max(inv_table["wastage_rate_pct"].max() * 1.25, 1))

    bars2 = ax2.bar(x, inv_table["shortage_days"], color="#fd8d3c")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=25, ha="right")
    ax2.set_ylabel("Shortage days")
    ax2.set_title("Days with any unmet demand")
    _style_axes(ax2)
    for bar, days, short in zip(bars2, inv_table["shortage_days"], inv_table["units_short"]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(days)} d\n({int(short)} u short)",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ymax = max(inv_table["shortage_days"].max(), 1)
    ax2.set_ylim(0, ymax * 1.30)

    fig.suptitle(
        "Same 5-day shelf-life ordering policy, holdout period (synthetic data)",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Educational platelet-demand project — SYNTHETIC example data")
    print("Advisory only. Not a real hospital. Not for clinical use.")
    print("=" * 70)

    df = load_data()
    print(f"\nLoaded {len(df)} days from {DATA_PATH}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    feat = build_origin_feature_table(df)
    feat = baseline_forecasts(feat)

    # Split by the *target* date of the 1-step forecast.
    # Origins used for training have date_t1 < TEST_START.
    # For the inventory sim we also need the evening-before-test origin
    # (date_t1 == TEST_START, origin_date == TEST_START - 1 day) so we can
    # place an order that arrives on the first test morning. Accuracy metrics
    # on the holdout use every row whose date_t1 is in the test window.
    train_feat = feat[feat["date_t1"] < TEST_START].copy()
    test_feat = feat[feat["date_t1"] >= TEST_START].copy()
    print(f"Training targets: {len(train_feat)} days ({train_feat['date_t1'].min().date()} to {train_feat['date_t1'].max().date()})")
    print(f"Holdout targets:  {len(test_feat)} days ({test_feat['date_t1'].min().date()} to {test_feat['date_t1'].max().date()})")

    # ----- Cross-validation on the training period -----
    print(f"\nRunning expanding-window CV ({N_CV_SPLITS} folds) on the training period...")
    cv_rows = run_timeseries_cv(train_feat)
    cv_summary = (
        cv_rows.groupby(["model_key", "model"], sort=False)
        .agg(cv_mae=("mae", "mean"), cv_wape=("wape", "mean"), cv_mape=("mape", "mean"))
        .reset_index()
    )
    print("\nCross-validation (mean across folds):")
    print(cv_summary[["model", "cv_mae", "cv_wape", "cv_mape"]].to_string(index=False, float_format=lambda v: f"{v:0.3f}"))

    # ----- Final holdout: fit once on all training data -----
    print("\nFitting gradient boosting on the full training period...")
    model_h1, model_h2 = fit_hgbr(train_feat)
    test_feat = predict_hgbr(model_h1, model_h2, test_feat)
    # Also attach training predictions so we can compute training MAE for safety stock.
    train_feat = predict_hgbr(model_h1, model_h2, train_feat)

    holdout_scores = []
    for key, label in MODELS.items():
        s = score_rows(test_feat, f"pred_{key}_t1", "y_t1")
        holdout_scores.append({"model_key": key, "model": label, **s})
    holdout_df = pd.DataFrame(holdout_scores)
    print("\nHoldout 1-step accuracy (last 6 months):")
    print(holdout_df[["model", "mae", "wape", "mape", "n_days"]].to_string(index=False, float_format=lambda v: f"{v:0.3f}"))

    best_baseline_key = (
        holdout_df[holdout_df["model_key"] != "hgbr"].sort_values("mae")["model_key"].iloc[0]
    )
    print(f"\nBest baseline on holdout MAE: {MODELS[best_baseline_key]}")

    # Training 1-step MAE per model, used only for the safety-stock rule.
    train_mae = {}
    for key in MODELS:
        train_mae[key] = mae(train_feat["y_t1"], train_feat[f"pred_{key}_t1"])

    # ----- Inventory simulation on the holdout -----
    # Issue days are the holdout target dates (date_t1). The forecasts used
    # at the *end* of day d must come from the row whose origin_date == d.
    # For day d in the holdout, that is the row with date_t1 == d + 1 day,
    # except we can also look up by origin_date.
    #
    # We need, for each holdout day d:
    #   actual = units on day d
    #   pred_t1, pred_t2 = forecasts made at end of day d
    # Those forecasts live on the feature row with origin_date == d.
    # The last holdout day still has an origin row if the series continues
    # 2 days past it. Our series ends on 2025-12-31, so the last origin with
    # both t+1 and t+2 is 2025-12-29. For 2025-12-30 and 2025-12-31 we would
    # lack a 2-step target in feat (dropped by dropna).
    #
    # Practical approach: simulate through the last date that has an origin
    # row with both forecasts, i.e. origin_date in the holdout and present
    # in `feat`. That drops Dec 30-31 if they have no 2-step future, OR we
    # rebuild forecasts for late origins without needing y_t2 to exist.
    #
    # Rebuild a slimmer origin table that does not drop the last two days
    # for lack of y_t2? For inventory we need pred_t2 even on the last days
    # (the order is unused after the horizon ends, but that's fine).
    # Simplest honest choice: run the sim on holdout days that have an
    # origin row in `feat` (through 2025-12-29). That's 2 days short of
    # 6 months; we will document it. OR: generate preds for remaining
    # origins by not requiring y_t2 when scoring inventory only.
    #
    # Better: build sim_days from feat rows whose origin_date is in the
    # holdout and is not the last date in the file... actually:
    #   - We issue on origin_date (today), using y_t as actual.
    #   - pred_t1/t2 already on that row (need y_t2 only for training).
    # I'll take all rows with origin_date >= TEST_START and origin_date
    # <= last origin in feat (which already required y_t2, so last origin
    # is 2025-12-29). Document the 2-day trim.
    sim_feat = feat[feat["origin_date"] >= TEST_START].copy()
    # sim_feat currently has baseline columns (from earlier) but not hgbr.
    # Re-predict hgbr on these origin rows (features use data through origin,
    # which for early holdout days includes earlier holdout *actuals* as lags
    # — that is the correct one-step-ahead protocol, not leakage).
    sim_feat = baseline_forecasts(sim_feat)
    sim_feat = predict_hgbr(model_h1, model_h2, sim_feat)

    train_mean = float(df.loc[df["date"] < TEST_START, "units_transfused"].mean())
    first_sim_day = pd.Timestamp(sim_feat["origin_date"].min())
    initial_lots = starting_inventory(train_mean, first_sim_day)
    print(
        f"\nInventory sim: {len(sim_feat)} days "
        f"({sim_feat['origin_date'].min().date()} to {sim_feat['origin_date'].max().date()})"
    )
    print(
        f"Opening stock (same for every model): {on_hand_qty(initial_lots)} units "
        f"(~{INITIAL_INVENTORY_DAYS_OF_MEAN} days of training-period mean "
        f"{train_mean:.1f}). Safety-stock rule: {SAFETY_K} × training MAE."
    )

    # Order placed the evening of June 30 (last training day) so the first
    # holdout morning is not artificially short of a delivery.
    eve_before = feat[feat["origin_date"] == (TEST_START - pd.Timedelta(days=1))].copy()
    if eve_before.empty:
        raise RuntimeError("Missing the origin row for the evening before TEST_START.")
    eve_before = baseline_forecasts(eve_before)
    eve_before = predict_hgbr(model_h1, model_h2, eve_before)
    eve_row = eve_before.iloc[0]
    opening_on_hand = on_hand_qty(initial_lots)

    inv_records = []
    for key, label in MODELS.items():
        safety = SAFETY_K * train_mae[key]
        opening_delivery = max(
            0,
            int(round(float(eve_row[f"pred_{key}_t1"] + eve_row[f"pred_{key}_t2"] + safety - opening_on_hand))),
        )
        sim_days = pd.DataFrame(
            {
                "date": sim_feat["origin_date"].values,
                "actual": sim_feat["y_t"].values,
                "pred_t1": sim_feat[f"pred_{key}_t1"].values,
                "pred_t2": sim_feat[f"pred_{key}_t2"].values,
            }
        )
        summary, daily = simulate_inventory(sim_days, safety, initial_lots, opening_delivery)
        daily.to_csv(RESULTS_DIR / f"inventory_daily_{key}.csv", index=False)
        inv_records.append({"model_key": key, "model": label, **summary})
        print(
            f"  {label}: waste {summary['units_expired']} u "
            f"({summary['wastage_rate_pct']:.1f}%), "
            f"shortage days {summary['shortage_days']}, "
            f"units short {summary['units_short']}, "
            f"safety stock {safety:.1f}"
        )

    inv_df = pd.DataFrame(inv_records)

    # Combined table: holdout accuracy + inventory outcomes + CV averages.
    combined = holdout_df.merge(cv_summary[["model_key", "cv_mae", "cv_wape"]], on="model_key")
    combined = combined.merge(
        inv_df[
            [
                "model_key",
                "units_expired",
                "wastage_rate_pct",
                "shortage_days",
                "units_short",
                "units_issued",
                "safety_stock",
            ]
        ],
        on="model_key",
    )
    combined = combined.rename(
        columns={
            "mae": "holdout_mae",
            "wape": "holdout_wape",
            "mape": "holdout_mape",
        }
    )
    col_order = [
        "model",
        "holdout_mae",
        "holdout_wape",
        "holdout_mape",
        "cv_mae",
        "cv_wape",
        "units_expired",
        "wastage_rate_pct",
        "shortage_days",
        "units_short",
        "safety_stock",
        "n_days",
    ]
    combined = combined[col_order]
    combined_path = RESULTS_DIR / "metrics_combined.csv"
    combined.to_csv(combined_path, index=False, float_format="%.3f")
    cv_rows.to_csv(RESULTS_DIR / "cv_fold_scores.csv", index=False, float_format="%.3f")

    # Save holdout forecasts for inspection.
    forecast_out = pd.DataFrame(
        {
            "date": test_feat["date_t1"].values,
            "actual": test_feat["y_t1"].values,
        }
    )
    for key in MODELS:
        forecast_out[f"pred_{key}_t1"] = test_feat[f"pred_{key}_t1"].values
    forecast_path = RESULTS_DIR / "holdout_forecasts.csv"
    forecast_out.to_csv(forecast_path, index=False, float_format="%.3f")

    # ----- Charts -----
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 11,
            "axes.titlesize": 12,
        }
    )

    # Align holdout_days to test_feat (1-step target dates) for the error chart.
    holdout_chart = forecast_out.copy()
    holdout_chart["date"] = pd.to_datetime(holdout_chart["date"])

    path_error = CHART_DIR / "holdout_actual_vs_forecasts.png"
    path_dow = CHART_DIR / "day_of_week_pattern.png"
    path_inv = CHART_DIR / "inventory_wastage_shortage.png"

    chart_actual_vs_forecasts(holdout_chart, best_baseline_key, path_error)
    chart_day_of_week(df, path_dow)
    chart_inventory_comparison(inv_df, path_inv)

    print("\n" + "=" * 70)
    print("Combined results (also saved to results/metrics_combined.csv)")
    print("=" * 70)
    print(combined.to_string(index=False, float_format=lambda v: f"{v:0.3f}"))
    print()
    print("Charts:")
    print(f"  Main (wastage & shortage): {path_inv}")
    print(f"  Actual vs forecasts:       {path_error}")
    print(f"  Day-of-week pattern:       {path_dow}")
    print(f"Metrics table: {combined_path}")


if __name__ == "__main__":
    main()
