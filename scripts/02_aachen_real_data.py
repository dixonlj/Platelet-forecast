#!/usr/bin/env python3
"""
Milestone 2: our forecasting + ordering pipeline on REAL public data.

Educational / advisory only. Never clinical. Not an ordering tool.

Data: University Hospital Aachen (UKA), daily platelet counts 2008-2018,
published as Multimedia Appendix 1 of
  Schilling M, Rickmann L, Hutschenreuter G, Spreckelsen C.
  JMIR Med Inform 2022;10(2):e29978. doi:10.2196/29978  (CC BY 4.0)
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8848235/
It is aggregate (units per day). There is no patient-level information in it.

What this script does, in order:
  1. Load the original xlsx, check it, and write a short data profile.
  2. Build 1- to 4-day-ahead forecasts from five models (four simple
     baselines and one gradient-boosting model), plus the authors' own
     published LASSO and RNN forecasts as a reference.
  3. Score everything with expanding-window yearly folds (2012-2017) and a
     final untouched holdout year (2018). No shuffling, no peeking ahead.
  4. Run one FIFO inventory simulation on 2018 that copies Aachen's documented
     constraints (units arrive with 4 days of shelf life left, nothing arrives
     on Sundays or Mondays, emergency buys cover any gap) and sweep the
     safety-stock multiplier k to trace a waste-vs-shortage curve per model.
  5. Compare with what the hospital actually recorded in 2018 and save charts.

Run:  python3 scripts/02_aachen_real_data.py
Needs: pandas, numpy, matplotlib, scikit-learn, holidays, openpyxl
"""

from __future__ import annotations

from pathlib import Path

import holidays
import matplotlib
import matplotlib.dates

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
XLSX = PROJECT_ROOT / "data/public/UKA_Aachen_daily_platelets_2008-2018_JMIR_app1.xlsx"
CHART_DIR = PROJECT_ROOT / "charts"
RESULTS_DIR = PROJECT_ROOT / "results/aachen"

SEED = 42
MAX_H = 4  # we forecast up to 4 days ahead (Thursday orders must cover 4 days)

# Validation design. Each CV fold trains on 2008..(Y-1) and tests on year Y.
CV_TEST_YEARS = [2012, 2013, 2014, 2015, 2016, 2017]
HOLDOUT_YEAR = 2018  # final test: trained on 2008-2017, touched once

# Gradient boosting: plain settings picked before looking at the holdout.
HGBR_PARAMS = dict(max_depth=4, learning_rate=0.05, max_iter=300,
                   l2_regularization=1.0, random_state=SEED)

# Inventory simulation settings
SHELF_DAYS_ON_ARRIVAL = 4      # usable on arrival day + 3 more days, then discarded
LEAD_DAYS = 2                  # order on day i arrives on the morning of day i+2
K_GRID = np.round(np.arange(0, 6.01, 0.25), 2)  # safety-stock multipliers to sweep
REFERENCE_K = 1.0              # the "sensible" common setting reported in the table
SIM_START = pd.Timestamp("2017-12-25")   # warm-up week (not scored)
EVAL_START = pd.Timestamp("2018-01-08")  # scoring window starts
EVAL_END = pd.Timestamp("2018-12-18")    # last origin day with BOTH authors' forecasts
INITIAL_STOCK = 20             # same starting shelf for every model

# Display names, in a stable order
MODELS = {
    "naive": "Use yesterday",
    "last7": "Last-7-day average",
    "same_dow": "Same weekday last week",
    "dow4": "4-week weekday average",
    "hgbr": "Gradient boosting",
}
AUTHOR_MODELS = {"lasso": "Authors' LASSO (ref.)", "rnn": "Authors' RNN (ref.)"}
COLORS = {"naive": "#999999", "last7": "#66a61e", "same_dow": "#e7298a",
          "dow4": "#1f77b4", "hgbr": "#d95f02", "lasso": "#7570b3", "rnn": "#a6761d"}


# ---------------------------------------------------------------------------
# 1. Load and check the data
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """Read the authors' xlsx. Row 1 is a copyright note; the header is row 2."""
    raw = pd.read_excel(XLSX, header=1)
    df = pd.DataFrame({
        "date": pd.to_datetime(raw["date"]),
        "transfused": raw["Transfused"].astype(int),   # our demand proxy
        "waste": raw["Waste"].astype(int),             # units expired/discarded
        "purchase": raw["Purchase"].astype(int),       # emergency buys from outside
        # Authors' forecasts. We verified (MAPE/RMSE match Table 2 of the paper)
        # that the value on row d is the forecast for days d..d+1 (2-day) and
        # d..d+3 (4-day), i.e. made before day d starts.
        "lasso2": raw["Predicted_transfusions_LASSO_next_2_days"],
        "lasso4": raw["Predicted_transfusions_LASSO_next_4_days"],
        "rnn2": raw["Predicted_transfusions_RNN_next_2_days"],
        "rnn4": raw["Predicted_transfusions_RNN_next_4_days"],
        "lasso_sim_waste": raw["Waste_simulated_LASSO"],
        "lasso_sim_purchase": raw["Purchase_simulated_LASSO"],
        "rnn_sim_waste": raw["Waste_simulated_RNN"],
        "rnn_sim_purchase": raw["Purchase_simulated_RNN"],
    })
    # Sanity checks: one row per day, weekday labels and running totals agree.
    assert df["date"].diff().dropna().eq(pd.Timedelta(days=1)).all(), "gap in dates"
    assert (raw["Weekday"] == df["date"].dt.day_name().str[:3]).all()
    assert (raw["Transfused"].cumsum() == raw["Cumulative_transfusions"]).all()
    assert (raw["Waste"].cumsum() == raw["Cumulative_waste"]).all()
    assert (raw["Purchase"].cumsum() == raw["Cumulative_purchase"]).all()
    # Cost column is exactly 350*waste + 700*purchase (the paper's cost weights).
    assert (raw["Cost"] == 350 * raw["Waste"] + 700 * raw["Purchase"]).all()
    return df.set_index("date")


def data_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly totals and rates, using the paper's definitions (rates per unit transfused)."""
    g = df.groupby(df.index.year).agg(
        transfused=("transfused", "sum"), waste=("waste", "sum"),
        purchase=("purchase", "sum"),
        purchase_days=("purchase", lambda s: int((s > 0).sum())),
        zero_days=("transfused", lambda s: int((s == 0).sum())),
        mean_per_day=("transfused", "mean"))
    g["waste_pct"] = 100 * g["waste"] / g["transfused"]
    g["shortage_pct"] = 100 * g["purchase"] / g["transfused"]
    g.index.name = "year"
    return g.round(2)


# ---------------------------------------------------------------------------
# 2. Forecasts. Everything is indexed by the ORIGIN day i: the forecast is made
#    in the evening of day i, after day i's usage is known, for days i+1..i+4.
# ---------------------------------------------------------------------------
def nrw_holiday_flags(dates: pd.DatetimeIndex) -> np.ndarray:
    """1 if the date is a public holiday in North Rhine-Westphalia (Aachen's state)."""
    hol = holidays.Germany(subdiv="NW", years=range(dates.year.min(), dates.year.max() + 2))
    return np.array([d in hol for d in dates.date], dtype=int)


def baseline_forecasts(y: pd.Series) -> dict[str, pd.DataFrame]:
    """Return {model: DataFrame[origin x h]} for the four simple baselines.

    Only uses values on or before the origin day, so there is no leakage.
    """
    out = {}
    roll7 = y.rolling(7).mean()
    out["naive"] = pd.DataFrame({h: y for h in range(1, MAX_H + 1)})
    out["last7"] = pd.DataFrame({h: roll7 for h in range(1, MAX_H + 1)})
    # Target day j = i + h. "Same weekday last week" is y[j-7] = y[i + h - 7].
    out["same_dow"] = pd.DataFrame({h: y.shift(7 - h) for h in range(1, MAX_H + 1)})
    # 4-week weekday average: mean of y[j-7], y[j-14], y[j-21], y[j-28].
    out["dow4"] = pd.DataFrame({
        h: sum(y.shift(7 * w - h) for w in range(1, 5)) / 4 for h in range(1, MAX_H + 1)})
    return out


def hgbr_feature_table(y: pd.Series) -> pd.DataFrame:
    """One row per (origin i, horizon h) with features known on day i.

    Calendar features describe the TARGET day (known in advance). Lag and
    rolling features use only data up to the origin day.
    """
    hol = pd.Series(nrw_holiday_flags(y.index), index=y.index)
    rows = []
    for h in range(1, MAX_H + 1):
        target_dates = y.index + pd.Timedelta(days=h)
        f = pd.DataFrame(index=y.index)
        f["origin"] = y.index
        f["h"] = h
        f["dow"] = target_dates.dayofweek
        f["month"] = target_dates.month
        f["holiday"] = nrw_holiday_flags(target_dates)
        f["origin_holiday"] = hol.values
        f["lag1"] = y.values                    # last known day (the origin)
        f["lag7"] = y.shift(7 - h).values       # same weekday one week before target
        f["lag14"] = y.shift(14 - h).values     # same weekday two weeks before target
        f["roll7"] = y.rolling(7).mean().values
        f["roll28"] = y.rolling(28).mean().values
        f["target"] = y.shift(-h).values        # what actually happened on day i+h
        f["target_date"] = target_dates
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


FEATURES = ["h", "dow", "month", "holiday", "origin_holiday",
            "lag1", "lag7", "lag14", "roll7", "roll28"]


def hgbr_forecasts(feat: pd.DataFrame, train_end: pd.Timestamp) -> pd.DataFrame:
    """Fit on rows whose TARGET date is <= train_end, predict every origin.

    Returns DataFrame[origin x h]. Predictions for origins before train_end are
    in-sample and are only used for the simulation warm-up, never scored.
    """
    ok = feat[FEATURES].notna().all(axis=1)
    train = feat[ok & feat["target"].notna() & (feat["target_date"] <= train_end)]
    model = HistGradientBoostingRegressor(**HGBR_PARAMS,
                                          categorical_features=[FEATURES.index("dow")])
    model.fit(train[FEATURES], train["target"])
    pred = pd.Series(np.nan, index=feat.index)
    pred[ok] = model.predict(feat.loc[ok, FEATURES])
    return (feat.assign(pred=pred).pivot(index="origin", columns="h", values="pred"))


def window_sum(fc: pd.DataFrame, n: int) -> pd.Series:
    """Forecast of total demand for days i+1..i+n, from a per-horizon table."""
    return fc[list(range(1, n + 1))].sum(axis=1, min_count=n)


def actual_window_sum(y: pd.Series, n: int) -> pd.Series:
    return sum(y.shift(-h) for h in range(1, n + 1))


def author_window(df: pd.DataFrame, col: str) -> pd.Series:
    """Authors' forecast re-indexed to OUR origin convention.

    Row d holds their forecast for days d.. ; our origin i covers i+1.. ,
    so origin i uses row i+1.
    """
    return df[col].shift(-1)


# ---------------------------------------------------------------------------
# 3. Metrics
# ---------------------------------------------------------------------------
def mae(a, f):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(f))))


def wape(a, f):
    """Weighted absolute % error = total |error| / total actual. Safe with zero days."""
    a, f = np.asarray(a), np.asarray(f)
    return float(100 * np.abs(a - f).sum() / a.sum())


def score_period(y, fcs, authors, start, end) -> list[dict]:
    """Score daily (1-day-ahead) and 2-/4-day totals for one test period.

    2- and 4-day totals are scored on the origins where the authors also have
    a forecast, so every model is judged on exactly the same days.
    """
    rows = []
    origins = y.index[(y.index >= start - pd.Timedelta(days=1)) & (y.index < end)]
    act1 = y.shift(-1)
    act = {n: actual_window_sum(y, n) for n in (2, 4)}
    common = {n: origins[authors[f"lasso{n}"].reindex(origins).notna().values
                          & authors[f"rnn{n}"].reindex(origins).notna().values
                          & act[n].reindex(origins).notna().values] for n in (2, 4)}
    for key, fc in fcs.items():
        r = {"model": key}
        o1 = origins[act1.reindex(origins).notna().values]
        r["mae_1d"] = mae(act1[o1], fc.loc[o1, 1])
        r["wape_1d"] = wape(act1[o1], fc.loc[o1, 1])
        for n in (2, 4):
            o = common[n]
            r[f"mae_{n}d"] = mae(act[n][o], window_sum(fc, n)[o])
            r[f"wape_{n}d"] = wape(act[n][o], window_sum(fc, n)[o])
        rows.append(r)
    for key in ("lasso", "rnn"):
        r = {"model": key, "mae_1d": np.nan, "wape_1d": np.nan}
        for n in (2, 4):
            o = common[n]
            r[f"mae_{n}d"] = mae(act[n][o], authors[f"{key}{n}"][o])
            r[f"wape_{n}d"] = wape(act[n][o], authors[f"{key}{n}"][o])
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# 4. Inventory simulation (FIFO, Aachen-style constraints)
# ---------------------------------------------------------------------------
def order_window(day: pd.Timestamp) -> int:
    """How many days an order placed this evening must cover (0 = no order).

    Sun-Wed orders arrive two days later (Tue-Fri) and cover days i+1 and i+2.
    Thursday's order arrives Saturday and must cover Fri-Mon (4 days),
    because nothing is ordered Fri/Sat and nothing arrives Sun/Mon.
    """
    dow = day.dayofweek  # Mon=0 ... Sun=6
    if dow in (6, 0, 1, 2):
        return 2
    if dow == 3:
        return 4
    return 0


def simulate(y: pd.Series, fc2: pd.Series, fc4: pd.Series, safety: float) -> dict:
    """Run the same ordering rule for one model and one safety-stock level.

    Each day t:
      morning   - the order placed on day t-2 arrives with 4 days of life left
      daytime   - demand (units actually transfused) is issued oldest-first;
                  any gap is an emergency purchase = a shortage in our scoring
      evening   - units on their last day are discarded (waste)
                - if t is Sun-Thu: order up to forecast(window) + safety,
                  minus stock on hand and the order already on its way.
    """
    days = pd.date_range(SIM_START, EVAL_END)
    lots: list[list] = [[SIM_START + pd.Timedelta(days=1), INITIAL_STOCK // 2],
                        [SIM_START + pd.Timedelta(days=2), INITIAL_STOCK - INITIAL_STOCK // 2]]
    pipeline: dict[pd.Timestamp, int] = {}
    log = []
    for t in days:
        arriving = pipeline.pop(t, 0)
        if arriving:
            lots.append([t + pd.Timedelta(days=SHELF_DAYS_ON_ARRIVAL - 1), arriving])
        lots.sort(key=lambda lot: lot[0])  # FIFO: oldest expiry first
        demand = int(y[t])
        need = demand
        for lot in lots:
            take = min(lot[1], need)
            lot[1] -= take
            need -= take
        short = need  # covered by an emergency purchase in real life
        wasted = sum(q for exp, q in lots if exp <= t)
        lots = [lot for lot in lots if lot[0] > t and lot[1] > 0]
        on_hand = sum(q for _, q in lots)
        order = 0
        n = order_window(t)
        if n:
            forecast = fc2[t] if n == 2 else fc4[t]
            in_transit = pipeline.get(t + pd.Timedelta(days=1), 0)
            order = max(0, int(round(forecast + safety - on_hand - in_transit)))
            if order:
                pipeline[t + pd.Timedelta(days=LEAD_DAYS)] = order
        log.append((t, demand, short, wasted, on_hand, order))
    d = pd.DataFrame(log, columns=["date", "demand", "short", "wasted", "end_stock", "order"])
    d = d.set_index("date").loc[EVAL_START:EVAL_END]
    return {"daily": d, "demand": int(d["demand"].sum()),
            "waste_units": int(d["wasted"].sum()), "short_units": int(d["short"].sum()),
            "shortage_days": int((d["short"] > 0).sum()),
            "waste_pct": 100 * d["wasted"].sum() / d["demand"].sum(),
            "shortage_pct": 100 * d["short"].sum() / d["demand"].sum(),
            "mean_end_stock": float(d["end_stock"].mean())}


# ---------------------------------------------------------------------------
# 5. Charts
# ---------------------------------------------------------------------------
def _style(ax):
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def chart_tradeoff(sweep: pd.DataFrame, actual: dict, path: Path) -> None:
    """Left: every model over the full k range. Right: zoom on the useful corner."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5),
                             gridspec_kw={"width_ratios": [1, 1.15]})
    zoom = dict(xlim=(0, 14), ylim=(0, 60))
    for ax, is_zoom in zip(axes, (False, True)):
        for key, name in {**MODELS, **AUTHOR_MODELS}.items():
            s = sweep[sweep["model"] == key].sort_values("k")
            ls = "--" if key in AUTHOR_MODELS else "-"
            ax.plot(s["waste_pct"], s["shortage_days"], ls, marker="o", ms=3.5,
                    color=COLORS[key], label=name, lw=1.6)
            ref = s[s["k"] == REFERENCE_K]
            ax.plot(ref["waste_pct"], ref["shortage_days"], "s", ms=8, mfc="white",
                    mec=COLORS[key], mew=2)
        ax.plot(actual["waste_pct"], actual["shortage_days"], "*", ms=20, color="black",
                label="Hospital actual (recorded), same 2018 days")
        if is_zoom:
            ax.set_xlim(*zoom["xlim"])
            ax.set_ylim(*zoom["ylim"])
            ax.annotate(f"Hospital actual: {actual['waste_pct']:.1f}% waste,\n"
                        f"{actual['shortage_days']} days with emergency buys",
                        (actual["waste_pct"], actual["shortage_days"]), xytext=(-170, 25),
                        textcoords="offset points", fontsize=9,
                        arrowprops=dict(arrowstyle="->", color="black"))
            ax.set_title("Zoom: the useful corner (bottom-left is better)", fontsize=10)
            ax.legend(frameon=False, fontsize=9, loc="upper right")
        else:
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)
            ax.set_title("All models, k = 0 to 6", fontsize=10)
        ax.set_xlabel("Waste (% of units transfused)")
        ax.set_ylabel("Shortage days (days needing an emergency buy)")
        _style(ax)
    fig.suptitle("Aachen 2018 holdout (Jan 8 - Dec 18): waste vs shortage trade-off as safety "
                 "stock k rises. Each dot = one k; white square = k = 1.\n"
                 "Simplified FIFO simulation, all blood groups pooled. Not the hospital's real "
                 "ordering process.", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_actual_vs_forecasts(y, fcs, best_key, path: Path) -> None:
    periods = [("2018-02-01", "2018-02-28", "February 2018"),
               ("2018-06-01", "2018-06-30", "June 2018"),
               ("2018-10-01", "2018-10-31", "October 2018")]
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharey=True)
    for ax, (a, b, title) in zip(axes, periods):
        idx = pd.date_range(a, b)
        ax.plot(idx, y[idx], color="#222222", lw=1.8, marker="o", ms=3,
                label="Actual units transfused")
        keys = ["dow4", "hgbr"] if best_key in ("dow4", "hgbr") else [best_key, "dow4", "hgbr"]
        for k in keys:
            # 1-day-ahead forecast for day j was made on origin j-1
            f = fcs[k][1].shift(1).reindex(idx)
            ax.plot(idx, f, color=COLORS[k], lw=1.4, label=f"{MODELS[k]} (1 day ahead)")
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_xlim(idx[0] - pd.Timedelta(hours=12), idx[-1] + pd.Timedelta(hours=12))
        ax.set_ylabel("Units / day")
        ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(bymonthday=[1, 8, 15, 22, 29]))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%a %d %b"))
        _style(ax)
    axes[0].legend(frameon=False, fontsize=9, ncol=3, loc="upper right")
    fig.suptitle("Aachen (real public data): actual daily platelet use vs forecasts, "
                 "2018 holdout", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(exist_ok=True)
    df = load_data()
    y = df["transfused"].astype(float)

    profile = data_profile(df)
    profile.to_csv(RESULTS_DIR / "yearly_profile.csv")
    print("Yearly profile (rates per unit transfused, paper definition):\n", profile, "\n")

    base = baseline_forecasts(y)
    feat = hgbr_feature_table(y)
    authors = {c: author_window(df, c) for c in ("lasso2", "lasso4", "rnn2", "rnn4")}

    # --- expanding-window CV, one fold per year ---
    cv_rows = []
    for year in CV_TEST_YEARS:
        start, end = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31")
        fcs = {**base, "hgbr": hgbr_forecasts(feat, start - pd.Timedelta(days=1))}
        for r in score_period(y, fcs, authors, start, end):
            cv_rows.append({"fold_test_year": year, **r})
        if year == 2017:
            fcs_2017 = fcs  # keep: its out-of-sample error sizes the safety stock
    cv = pd.DataFrame(cv_rows)
    cv.to_csv(RESULTS_DIR / "cv_folds.csv", index=False)
    cv_mean = cv.groupby("model").mean(numeric_only=True).drop(columns="fold_test_year")

    # --- final holdout: train on 2008-2017, test 2018 once ---
    h_start, h_end = pd.Timestamp(f"{HOLDOUT_YEAR}-01-01"), pd.Timestamp(f"{HOLDOUT_YEAR}-12-31")
    fcs_hold = {**base, "hgbr": hgbr_forecasts(feat, h_start - pd.Timedelta(days=1))}
    hold = pd.DataFrame(score_period(y, fcs_hold, authors, h_start, h_end)).set_index("model")

    # --- safety-stock unit per model: out-of-sample MAE of its 2-day total in
    #     2017 (the last year before the holdout). In-sample "training MAE" would
    #     flatter gradient boosting, so we use this instead for every model. ---
    s17, e17 = pd.Timestamp("2016-12-31"), pd.Timestamp("2017-12-30")
    o17 = y.loc[s17:e17].index
    act2 = actual_window_sum(y, 2)
    sigma = {k: mae(act2[o17], window_sum(fc, 2)[o17]) for k, fc in fcs_2017.items()}
    for k in AUTHOR_MODELS:
        sigma[k] = mae(act2[o17], authors[f"{k}2"][o17])

    print("safety unit (2017 out-of-sample MAE of 2-day total):", {k: round(v, 2) for k, v in sigma.items()})
    # --- inventory sweep on the holdout ---
    win = {k: (window_sum(fc, 2), window_sum(fc, 4)) for k, fc in fcs_hold.items()}
    win.update({k: (authors[f"{k}2"], authors[f"{k}4"]) for k in AUTHOR_MODELS})
    sweep_rows, ref_daily = [], {}
    for key, (f2, f4) in win.items():
        for k in K_GRID:
            res = simulate(y, f2, f4, k * sigma[key])
            sweep_rows.append({"model": key, "k": k, "safety_units": k * sigma[key],
                               **{c: res[c] for c in ("demand", "waste_units", "waste_pct",
                                                       "short_units", "shortage_pct",
                                                       "shortage_days", "mean_end_stock")}})
            if k == REFERENCE_K:
                ref_daily[key] = res["daily"]
    sweep = pd.DataFrame(sweep_rows)
    sweep.to_csv(RESULTS_DIR / "inventory_k_sweep.csv", index=False)
    for key, d in ref_daily.items():
        d.to_csv(RESULTS_DIR / f"inventory_daily_k1_{key}.csv")

    # --- what the hospital actually recorded on the same scored days ---
    w = df.loc[EVAL_START:EVAL_END]
    actual = {"demand": int(w["transfused"].sum()), "waste_units": int(w["waste"].sum()),
              "short_units": int(w["purchase"].sum()),
              "shortage_days": int((w["purchase"] > 0).sum()),
              "waste_pct": 100 * w["waste"].sum() / w["transfused"].sum(),
              "shortage_pct": 100 * w["purchase"].sum() / w["transfused"].sum()}
    # The authors' own simulated outcomes on the same days (from their file)
    authors_sim = {k: {"waste_pct": 100 * w[f"{k}_sim_waste"].sum() / w["transfused"].sum(),
                       "short_units": float(w[f"{k}_sim_purchase"].sum()),
                       "shortage_days": int((w[f"{k}_sim_purchase"] > 0).sum())}
                   for k in AUTHOR_MODELS}

    # --- summary table ---
    ref = sweep[sweep["k"] == REFERENCE_K].set_index("model")
    # Best shortage result each model can reach while wasting no more than the hospital did
    matched = (sweep[sweep["waste_pct"] <= actual["waste_pct"]]
               .sort_values(["shortage_days", "short_units", "waste_pct"])
               .groupby("model").first())
    # And the mirror view: least waste each model needs to have no more
    # shortage days than the hospital recorded
    matched_s = (sweep[sweep["shortage_days"] <= actual["shortage_days"]]
                 .sort_values(["waste_pct", "shortage_days"])
                 .groupby("model").first())
    table = []
    for key, name in {**MODELS, **AUTHOR_MODELS}.items():
        table.append({
            "model": name,
            "cv_mae_1d": cv_mean.loc[key, "mae_1d"], "cv_wape_1d": cv_mean.loc[key, "wape_1d"],
            "cv_wape_2d": cv_mean.loc[key, "wape_2d"],
            "hold_mae_1d": hold.loc[key, "mae_1d"], "hold_wape_1d": hold.loc[key, "wape_1d"],
            "hold_mae_2d": hold.loc[key, "mae_2d"], "hold_wape_2d": hold.loc[key, "wape_2d"],
            "hold_wape_4d": hold.loc[key, "wape_4d"],
            "safety_unit_sigma": sigma[key],
            "k1_waste_pct": ref.loc[key, "waste_pct"], "k1_shortage_days": ref.loc[key, "shortage_days"],
            "k1_units_short": ref.loc[key, "short_units"],
            "k1_shortage_pct": ref.loc[key, "shortage_pct"],
            "k1_mean_end_stock": ref.loc[key, "mean_end_stock"],
            "matched_k": matched.loc[key, "k"] if key in matched.index else np.nan,
            "matched_waste_pct": matched.loc[key, "waste_pct"] if key in matched.index else np.nan,
            "matched_shortage_days": matched.loc[key, "shortage_days"] if key in matched.index else np.nan,
            "matched_units_short": matched.loc[key, "short_units"] if key in matched.index else np.nan,
            "sdmatch_k": matched_s.loc[key, "k"] if key in matched_s.index else np.nan,
            "sdmatch_waste_pct": matched_s.loc[key, "waste_pct"] if key in matched_s.index else np.nan,
            "sdmatch_shortage_days": matched_s.loc[key, "shortage_days"] if key in matched_s.index else np.nan,
            "sdmatch_units_short": matched_s.loc[key, "short_units"] if key in matched_s.index else np.nan,
        })
    table = pd.DataFrame(table).round(2)
    table.to_csv(RESULTS_DIR / "summary_table.csv", index=False)
    pd.DataFrame([{"what": "Hospital actual (recorded)", **actual}]
                 + [{"what": f"Authors' own sim, {k} (from their file)", **v}
                    for k, v in authors_sim.items()]).round(2).to_csv(
        RESULTS_DIR / "hospital_actual_2018_window.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("Holdout scoring days for inventory:", EVAL_START.date(), "to", EVAL_END.date())
    print("Hospital actual:", {k: round(v, 2) for k, v in actual.items()})
    print("Authors' own simulation (their file):", authors_sim)
    print(table.to_string(index=False))

    # --- charts ---
    chart_tradeoff(sweep, actual, CHART_DIR / "aachen_waste_vs_shortage_tradeoff.png")
    best_key = hold.loc[list(MODELS), "mae_1d"].idxmin()
    chart_actual_vs_forecasts(y, fcs_hold, best_key, CHART_DIR / "aachen_holdout_actual_vs_forecasts.png")
    print("best 1-day holdout model:", best_key)


if __name__ == "__main__":
    main()
