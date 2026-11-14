#!/usr/bin/env python3
"""Milestone 10 (preregistered revision), Stanford second site: the NEW forecasts
declared in prereg Section 2.5, made with fixed settings before any simulation:

  * SO  standing order: previous calendar year's mean use on the target weekday
        (by usage date), as at Aachen (scripts/09_reality_check.py::standing_order_fc).
  * dGB detrended gradient boosting: script 27 feature construction (lags and 7-day mean
        relative to the past-28-day mean; target relative to the past-28-day mean;
        calendar features of the target day), S2-1 GB settings (lib_s2.HGBR_PARAMS),
        weekly retraining on rows whose target is known at the cut-off (as in S2-1).
  * CB  Chronos-Bolt: separate script 10b (needs torch; run in .venv-chronos).

Forecasts for origins 199..878 (as in S2-1), h = 1..3. Public data. Educational only.
Run: PYTHONPATH=study2/scripts .venv/bin/python study2/scripts/10_m10_forecasts.py
"""
from __future__ import annotations

import holidays
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import lib_s2 as S

OUT = S.STUDY / "results" / "s2m10"
FEATS27 = ["h", "dow", "month", "holiday", "origin_holiday", "lag1_rel", "lag7_rel", "lag14_rel", "roll7_rel"]


def standing_order(df):
    y = df["y"].values
    use = pd.DatetimeIndex(df["use_date"])
    tab = pd.Series(y, index=use).groupby([use.year, use.dayofweek]).mean()
    rows = []
    for i in range(S.FIRST_ORIGIN, S.N_ROWS - 1):
        for h in range(1, S.H_MAX + 1):
            j = i + h
            if j >= S.N_ROWS:
                continue
            d = use[j]
            rows.append(dict(origin=i, h=h, target=j, model="so", fc=tab.get((d.year - 1, d.dayofweek), np.nan)))
    return rows


def detrended_features(df):
    y = df["y"].values
    use = pd.DatetimeIndex(df["use_date"])
    hd = holidays.country_holidays("US", subdiv="CA", years=range(2012, 2016))
    hol = np.array([d.date() in hd for d in use], dtype=int)
    s = pd.Series(y)
    roll7, roll28 = s.rolling(7).mean().values, s.rolling(28).mean().values
    rows = []
    for i in range(28, S.N_ROWS - 1):
        for h in range(1, S.H_MAX + 1):
            j = i + h
            if j >= S.N_ROWS:
                continue
            lev = roll28[i]
            rows.append(dict(origin=i, h=h, target=j, y_target=y[j], level=lev,
                             dow=use[j].day_of_week, month=use[j].month, holiday=hol[j], origin_holiday=hol[i],
                             lag1_rel=y[i] - lev, lag7_rel=y[j - 7] - lev, lag14_rel=y[j - 14] - lev,
                             roll7_rel=roll7[i] - lev, target_rel=y[j] - lev))
    return pd.DataFrame(rows)


def dgb(ft):
    out = []
    cuts = list(range(S.FIRST_ORIGIN, S.N_ROWS - 1, S.RETRAIN_EVERY))
    ends = cuts[1:] + [S.N_ROWS - 1]
    for c, end in zip(cuts, ends):
        tr = ft[ft.target <= c]
        te = ft[(ft.origin >= c) & (ft.origin < end)]
        m = HistGradientBoostingRegressor(**S.HGBR_PARAMS, categorical_features=[FEATS27.index("dow")])
        m.fit(tr[FEATS27].values, tr["target_rel"].values)
        p = np.clip(m.predict(te[FEATS27].values) + te["level"].values, 0, None)
        out += [dict(origin=o, h=h, target=t, model="dgb", fc=v) for o, h, t, v in zip(te.origin, te.h, te.target, p)]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = S.load_aligned()
    assert len(df) == S.N_ROWS
    rows = standing_order(df) + dgb(detrended_features(df))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "10_forecasts_so_dgb.csv", index=False)
    print(out.groupby("model").fc.describe())


if __name__ == "__main__":
    main()
