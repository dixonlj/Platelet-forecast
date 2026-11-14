#!/usr/bin/env python3
"""
Milestone 8, step 2: statistics asked for by the second internal review.

  A. Year-level tests of each forecast minus the weekday average at the
     hospital's recorded short days (7 yearly differences per comparison):
     exact two-sided sign test, exact Wilcoxon signed-rank test, and a
     t-based 95% CI of the mean yearly difference. Also for the prior-year
     cushion run of script 19.
  B. Holm correction across the 35 one-day Diebold-Mariano tests already in
     scripts 08 and 13, plus one pooled DM test per comparison over all
     2,555 test days (2012-2018).
  C. Accuracy at the ordering horizons: MAE and mean error (bias) of 2-day
     and 4-day totals, per year and model, including the source authors'
     LASSO and RNN (which only exist as 2- and 4-day totals), with DM tests
     against the weekday average (Holm-corrected within each horizon).

No new simulation. Educational / advisory only. Public Aachen data. Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/20_horizon_accuracy_and_stats.py
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
from scipy import stats

import lib_m4 as L
import lib_m5 as M

P = L.PROJECT_ROOT
OUT = P / "results/m8"
NAMES = {"dow4": "Weekday average", "hgbr": "Gradient boosting", "chronos": "Chronos-Bolt",
         "sarima": "SARIMA", "lasso": "Authors' LASSO", "rnn": "Authors' RNN"}


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s08 = _load("s08", "08_multiyear_test.py")
s12 = _load("s12", "12_sarima.py")


def year_tests(d: np.ndarray) -> dict:
    d = np.asarray(d, float)
    n = len(d)
    better = int((d < 0).sum())
    sign_p = stats.binomtest(better, n, 0.5).pvalue
    wil_p = stats.wilcoxon(d, method="exact").pvalue
    m, se = d.mean(), d.std(ddof=1) / np.sqrt(n)
    t = stats.t.ppf(0.975, n - 1)
    return {"years_better": better, "n_years": n, "sign_p": sign_p, "wilcoxon_p": wil_p,
            "mean_diff": m, "ci_lo": m - t * se, "ci_hi": m + t * se}


def holm(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def part_a() -> pd.DataFrame:
    inv = pd.concat([pd.read_csv(P / "results/m5/08_multiyear_inventory.csv"),
                     pd.read_csv(P / "results/m6/13_multiyear_inventory.csv").query("model == 'sarima'")])
    inv = inv[inv.target == "hospital"]
    rows = []
    for src, tab, wcol, lcol in (
            ("matched to test-year short days (main)", inv, "waste_pct_mean", "wasted_plus_emergency_mean"),
            ("cushion set from prior year (script 19)", pd.read_csv(OUT / "19_prior_year_cushion.csv"),
             "waste_pct_mean", "wasted_plus_emergency_mean")):
        for outcome, col in (("Waste (points)", wcol), ("Wasted + emergency units a year", lcol)):
            pv = tab.pivot(index="year", columns="model", values=col)
            for m in ("hgbr", "chronos", "sarima", "lasso", "rnn"):
                rows.append({"analysis": src, "outcome": outcome, "model": m,
                             **year_tests((pv[m] - pv["dow4"]).values)})
        if "short_days_mean" in tab:
            pv = tab.pivot(index="year", columns="model", values="short_days_mean")
            for m in ("hgbr", "chronos", "sarima", "lasso", "rnn"):
                rows.append({"analysis": src, "outcome": "Short days", "model": m,
                             **year_tests((pv[m] - pv["dow4"]).values)})
    return pd.DataFrame(rows)


def part_b() -> tuple[pd.DataFrame, pd.DataFrame]:
    a = pd.concat([pd.read_csv(P / "results/m5/08_accuracy_by_year.csv"),
                   pd.read_csv(P / "results/m6/13_accuracy_by_year.csv")])
    dm = a[a.model.str.startswith("DM_")].drop_duplicates(["year", "model"]).copy()
    dm["holm_p"] = holm(dm["dm_p"].values)
    dm = dm.rename(columns={"mae_1d": "mean_abs_err_diff"})
    return dm, a


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    A = part_a()
    A.to_csv(OUT / "20_year_level_tests.csv", index=False)
    dm, _ = part_b()
    dm.to_csv(OUT / "20_dm_1day_holm.csv", index=False)

    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = s08.chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2011, 2018)}
    sar = {c: s12.load_sarima(c).reindex(y.index) for c in range(2011, 2018)}
    act = {1: y.shift(-1), 2: L.m2.actual_window_sum(y, 2), 4: L.m2.actual_window_sum(y, 4)}
    rows, errs = [], {}
    for Y in M.YEARS:
        orig = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        fc = {"dow4": base["dow4"], "hgbr": gb[Y - 1], "chronos": chron, "sarima": sar[Y - 1]}
        for n in (1, 2, 4):
            for m in ("dow4", "hgbr", "chronos", "sarima", "lasso", "rnn"):
                if m in ("lasso", "rnn"):
                    if n == 1:
                        continue
                    f = authors[f"{m}{n}"].reindex(orig)
                else:
                    f = (fc[m].loc[orig, 1] if n == 1 else L.m2.window_sum(fc[m], n).reindex(orig))
                e = (act[n][orig] - f).values  # actual minus forecast: positive = under-forecast
                errs[(Y, n, m)] = e
                ok = ~np.isnan(e)
                rows.append({"year": Y, "horizon_days": n, "model": m, "n_origins": int(ok.sum()),
                             "mae": float(np.mean(np.abs(e[ok]))), "mean_error_actual_minus_fc": float(np.mean(e[ok]))})
    acc = pd.DataFrame(rows)
    acc.to_csv(OUT / "20_accuracy_by_horizon.csv", index=False)

    # Check the 1-day MAE against scripts 08/13.
    a1 = pd.concat([pd.read_csv(P / "results/m5/08_accuracy_by_year.csv"),
                    pd.read_csv(P / "results/m6/13_accuracy_by_year.csv")]).drop_duplicates(["year", "model"])
    chk = acc[acc.horizon_days == 1].merge(a1, on=["year", "model"])
    maxdiff = float(np.abs(chk["mae"] - chk["mae_1d"]).max())

    # DM tests vs weekday average at each horizon, per year, Holm within horizon; plus pooled over years.
    dmr = []
    for n in (1, 2, 4):
        for m in ("hgbr", "chronos", "sarima", "lasso", "rnn"):
            if n == 1 and m in ("lasso", "rnn"):
                continue
            pool_a, pool_b = [], []
            for Y in M.YEARS:
                e1, e0 = errs[(Y, n, m)], errs[(Y, n, "dow4")]
                ok = ~np.isnan(e1) & ~np.isnan(e0)
                dbar, st, p = s08.dm_test(e1[ok], e0[ok])
                dmr.append({"horizon_days": n, "model": m, "year": Y, "mean_abs_err_diff": dbar, "dm_p": p})
                pool_a.append(e1[ok]); pool_b.append(e0[ok])
            dbar, st, p = s08.dm_test(np.concatenate(pool_a), np.concatenate(pool_b))
            dmr.append({"horizon_days": n, "model": m, "year": "pooled 2012-2018", "mean_abs_err_diff": dbar, "dm_p": p})
    dmr = pd.DataFrame(dmr)
    dmr["holm_p_within_horizon"] = np.nan
    for n in (1, 2, 4):
        sel = (dmr.horizon_days == n) & (dmr.year != "pooled 2012-2018")
        dmr.loc[sel, "holm_p_within_horizon"] = holm(dmr.loc[sel, "dm_p"].values)
    dmr.to_csv(OUT / "20_dm_by_horizon.csv", index=False)

    # Pooled DM for the five 1-day comparisons of the paper (incl. SARIMA vs GB and vs CB).
    pooled = []
    for a_, b_ in (("hgbr", "dow4"), ("chronos", "dow4"), ("sarima", "dow4"), ("sarima", "hgbr"), ("sarima", "chronos")):
        e1 = np.concatenate([errs[(Y, 1, a_)] for Y in M.YEARS]); e0 = np.concatenate([errs[(Y, 1, b_)] for Y in M.YEARS])
        ok = ~np.isnan(e1) & ~np.isnan(e0)
        dbar, st, p = s08.dm_test(e1[ok], e0[ok])
        pooled.append({"comparison": f"{a_} vs {b_}", "n_days": int(ok.sum()), "mean_abs_err_diff": dbar, "dm_p": p})
    pooled = pd.DataFrame(pooled)
    pooled.to_csv(OUT / "20_dm_1day_pooled.csv", index=False)

    lines = ["=== Milestone 8 step 2: year-level tests, Holm, horizon accuracy ===",
             f"1-day MAE check vs scripts 08/13: max diff {maxdiff:.2e} ({len(chk)} rows)",
             "A. Year-level tests:", A.round(4).to_string(index=False),
             "B. 1-day DM with Holm across all 35:", dm.round(4).to_string(index=False),
             "B2. pooled 1-day DM:", pooled.round(5).to_string(index=False)]
    for n in (2, 4):
        g = acc[acc.horizon_days == n]
        lines += [f"C. {n}-day MAE:", g.pivot(index="year", columns="model", values="mae").round(2).to_string(),
                  f"mean: {g.groupby('model').mae.mean().round(2).to_dict()}",
                  f"{n}-day mean error (actual - forecast):",
                  g.pivot(index="year", columns="model", values="mean_error_actual_minus_fc").round(2).to_string(),
                  f"mean: {g.groupby('model').mean_error_actual_minus_fc.mean().round(2).to_dict()}"]
    lines += ["C2. DM by horizon:", dmr.round(4).to_string(index=False)]
    txt = "\n".join(lines)
    print(txt)
    (OUT / "20_run_log.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
