#!/usr/bin/env python3
"""
Milestone 5, step 1: multi-year inventory test, 2012-2018.

For every test year Y in 2012..2018:
  * forecasts are out of sample: gradient boosting (GB) is trained only on
    days up to 31 Dec of Y-1 (expanding window); the baselines use only past
    days; Chronos-Bolt is zero-shot (no training); the source authors' LASSO
    and RNN forecasts are their own published out-of-sample forecasts.
  * the safety unit (sigma) is each model's out-of-sample 2-day miss in Y-1
    (GB trained only up to Y-2), so the test year never sets the cushion.
  * the realistic simulation of script 03 (German rules, blood groups, short
    deliveries, mixed life on arrival) runs with the same 30 paired seeds.
  * every model is matched to that year's hospital count of short days, and
    also to fixed 20 and 50 short days as a robustness check.
Reports waste %, emergency units, wasted + emergency units, and wins per year.

Educational / advisory only. Public Aachen data (CC BY 4.0). Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/08_multiyear_test.py
"""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd
from scipy import stats

import lib_m4 as L
import lib_m5 as M

RES = M.RESULTS
NAMES = {"naive": "Use yesterday", "last7": "Last-7-day average",
         "same_dow": "Same weekday last week", "dow4": "4-week weekday average",
         "hgbr": "Gradient boosting", "chronos": "Chronos-Bolt (zero-shot)",
         "lasso": "Authors' LASSO (ref.)", "rnn": "Authors' RNN (ref.)"}
CHRONOS_FILE = RES / "chronos_forecasts_2010-12-31_2018-12-30.csv"


def chronos_forecasts(y: pd.Series) -> pd.DataFrame | None:
    """Zero-shot Chronos-Bolt small, 512-day context, origins 2010-12-31..2018-12-30.
    Cached to CSV. Returns DataFrame[origin x h] of mean forecasts, or None."""
    if CHRONOS_FILE.exists():
        d = pd.read_csv(CHRONOS_FILE, index_col=0, parse_dates=True)
        d.columns = [int(c) for c in d.columns]
        return d
    try:
        import torch
        from chronos import BaseChronosPipeline
    except Exception as exc:  # pragma: no cover
        print("Chronos not available:", exc)
        return None
    for v in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
        os.environ.pop(v, None)
    pipe = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small",
                                               device_map="cpu", torch_dtype=torch.float32)
    vals = y.values.astype(float)
    pos = {d: i for i, d in enumerate(y.index)}
    origins = y.loc["2010-12-31":"2018-12-30"].index
    out = pd.DataFrame(index=origins, columns=[1, 2, 3, 4], dtype=float)
    t0 = time.time()
    for b in range(0, len(origins), 64):
        days = origins[b:b + 64]
        ctx = [torch.tensor(vals[max(0, pos[d] + 1 - 512):pos[d] + 1], dtype=torch.float32)
               for d in days]
        with torch.no_grad():
            _, mean = pipe.predict_quantiles(ctx, prediction_length=4, quantile_levels=[0.5])
        out.loc[days, :] = mean.cpu().numpy()
    print(f"Chronos forecasts: {len(origins)} origins in {time.time() - t0:.0f}s")
    out.to_csv(CHRONOS_FILE)
    return out


def dm_test(e1: np.ndarray, e2: np.ndarray, lag: int = 6):
    """Diebold-Mariano test on absolute 1-day errors (Newey-West variance)."""
    d = np.abs(e1) - np.abs(e2)
    d = d[~np.isnan(d)]
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    var = dc @ dc / n
    for h in range(1, lag + 1):
        w = 1 - h / (lag + 1)
        var += 2 * w * (dc[h:] @ dc[:-h]) / n
    stat = dbar / np.sqrt(var / n)
    return dbar, stat, 2 * (1 - stats.norm.cdf(abs(stat)))


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    base = L.m2.baseline_forecasts(y)
    feat = L.m2.hgbr_feature_table(y)
    chron = chronos_forecasts(y)
    gb = {Y: L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{Y}-12-31")) for Y in range(2010, 2018)}
    act1 = y.shift(-1)

    rows, wins, acc_rows, per_seed, hosp_rows = [], [], [], [], []
    for Y in M.YEARS:
        t0 = time.time()
        _, ev0, ev1 = L.year_window(Y)
        hosp = L.hospital_actual(df, ev0, ev1)
        dsub = df.loc[ev0:ev1]
        hosp["monday_share_of_purchase_days"] = float(
            ((dsub["purchase"] > 0) & (dsub.index.dayofweek == 0)).sum() / max(1, hosp["shortage_days"]))
        hosp_rows.append({"year": Y, **hosp})
        fcY = {**base, "hgbr": gb[Y - 1]}
        fcS = {**base, "hgbr": gb[Y - 2]}
        if chron is not None:
            fcY["chronos"] = chron
            fcS["chronos"] = chron
        sigma = L.sigma_for_year(y, fcS, Y)
        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcY.items()}
        prev = Y - 1
        o_prev = y.loc[pd.Timestamp(f"{prev - 1}-12-31"):pd.Timestamp(f"{prev}-12-30")].index
        act2 = L.m2.actual_window_sum(y, 2)
        for a in ("lasso", "rnn"):
            win[a] = (authors[f"{a}2"], authors[f"{a}4"])
            sigma[a] = L.m2.mae(act2[o_prev], authors[f"{a}2"][o_prev])
        models = list(win)

        # 1-day accuracy over the full calendar year (origins Dec 31 .. Dec 30)
        orig = y.loc[pd.Timestamp(f"{Y - 1}-12-31"):pd.Timestamp(f"{Y}-12-30")].index
        err = {}
        for k in models:
            if k in ("lasso", "rnn"):
                continue
            e = (act1[orig] - fcY[k].loc[orig, 1]).values
            err[k] = e
            acc_rows.append({"year": Y, "model": k, "mae_1d": float(np.nanmean(np.abs(e)))})
        for k in ("hgbr", "chronos"):
            if k in err:
                dbar, st, p = dm_test(err[k], err["dow4"])
                acc_rows.append({"year": Y, "model": f"DM_{k}_vs_dow4",
                                 "mae_1d": dbar, "dm_stat": st, "dm_p": p})

        res = L.run_config(L.m3.BASE, y, win, sigma, models, year=Y)
        for target_name, target in (("hospital", hosp["shortage_days"]), ("fixed20", 20), ("fixed50", 50)):
            mt = {k: M.match_at(res[k], target, hosp["demand"]) for k in models}
            for k in models:
                m = mt[k]
                d = m["waste_pct"] - mt["dow4"]["waste_pct"]
                dl = m["lost_units"] - mt["dow4"]["lost_units"]
                rows.append({
                    "year": Y, "target": target_name, "target_short_days": target, "model": k,
                    "sigma": sigma[k],
                    "waste_pct_mean": m["waste_pct"].mean(), "waste_pct_p05": M.p5(m["waste_pct"]),
                    "waste_pct_p95": M.p95(m["waste_pct"]),
                    "waste_units_mean": m["waste_units"].mean(),
                    "emergency_units_mean": m["short_units"].mean(),
                    "emergency_units_p05": M.p5(m["short_units"]), "emergency_units_p95": M.p95(m["short_units"]),
                    "wasted_plus_emergency_mean": m["lost_units"].mean(),
                    "k_mean": m["k"].mean(), "sim_monday_share_mean": m["monday_share"].mean(), "n_seeds": int(m["waste_pct"].notna().sum()),
                    "waste_gap_vs_dow4": d.mean(), "seeds_less_waste_than_dow4": int((d < 0).sum()),
                    "lost_gap_vs_dow4": dl.mean(), "seeds_fewer_lost_than_dow4": int((dl < 0).sum()),
                    "hospital_waste_pct": hosp["waste_pct"],
                    "hospital_monday_share": hosp["monday_share_of_purchase_days"], "hospital_emergency_units": hosp["short_units"],
                    "hospital_wasted_plus_emergency": hosp["waste_units"] + hosp["short_units"],
                    "demand": hosp["demand"],
                })
                if target_name == "hospital":
                    for s, r in m.iterrows():
                        per_seed.append({"year": Y, "model": k, "seed": 1000 + s, **r.drop("seed").to_dict()})
        print(f"{Y}: done in {time.time() - t0:.0f}s (target {hosp['shortage_days']} short days)")

    out = pd.DataFrame(rows)
    out.to_csv(RES / "08_multiyear_inventory.csv", index=False)
    pd.DataFrame(per_seed).to_csv(RES / "08_per_seed.csv", index=False)
    pd.DataFrame(acc_rows).to_csv(RES / "08_accuracy_by_year.csv", index=False)
    pd.DataFrame(hosp_rows).to_csv(RES / "08_hospital_by_year.csv", index=False)

    # Wins: which model had the lowest mean waste / lowest wasted+emergency each year.
    for target_name, g in out.groupby("target"):
        for metric in ("waste_pct_mean", "wasted_plus_emergency_mean"):
            for scope, mods in (("all_models", None), ("study_models", ["naive", "last7", "same_dow", "dow4", "hgbr", "chronos"]),
                                ("dow4_vs_hgbr", ["dow4", "hgbr"]), ("dow4_vs_chronos", ["dow4", "chronos"]),
                                ("hgbr_vs_chronos", ["hgbr", "chronos"])):
                gg = g if mods is None else g[g["model"].isin(mods)]
                best = gg.loc[gg.groupby("year")[metric].idxmin(), ["year", "model"]]
                for _, r in best.iterrows():
                    wins.append({"target": target_name, "metric": metric, "scope": scope,
                                 "year": r["year"], "winner": r["model"]})
    w = pd.DataFrame(wins)
    w.to_csv(RES / "08_winner_by_year.csv", index=False)
    cnt = w.groupby(["target", "metric", "scope", "winner"]).size().rename("years_won").reset_index()
    cnt.to_csv(RES / "08_wins_count.csv", index=False)

    lines = ["=== Milestone 5 step 1: multi-year inventory test 2012-2018 ===",
             "Matched to each year's hospital short days; 30 paired seeds; German-rules realistic sim."]
    h = out[out["target"] == "hospital"]
    piv = h.pivot(index="model", columns="year", values="waste_pct_mean").round(2)
    lines += ["Waste % (mean of 30 seeds):", piv.to_string()]
    piv = h.pivot(index="model", columns="year", values="emergency_units_mean").round(1)
    lines += ["Emergency units (mean):", piv.to_string()]
    piv = h.pivot(index="model", columns="year", values="wasted_plus_emergency_mean").round(1)
    lines += ["Wasted + emergency units (mean):", piv.to_string()]
    lines += ["Wins (years with lowest mean):", cnt.to_string(index=False)]
    lines += ["Accuracy:", pd.DataFrame(acc_rows).to_string(index=False)]
    txt = "\n".join(lines)
    print(txt)
    (RES / "08_run_log.txt").write_text(txt + "\n")


def grouped_chart(per_seed: pd.DataFrame, metric: str, models: list, labels: dict, colors: dict,
                  title: str, ylabel: str, footnote: str, path, value_fmt="{:.1f}") -> None:
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    years = sorted(per_seed["year"].unique())
    fig, ax = plt.subplots(figsize=(13, 7.2))
    w = 0.8 / len(models)
    for i, m in enumerate(models):
        g = per_seed[per_seed["model"] == m].groupby("year")[metric]
        mean = g.mean().reindex(years)
        lo = g.quantile(0.05).reindex(years)
        hi = g.quantile(0.95).reindex(years)
        x = np.arange(len(years)) + (i - (len(models) - 1) / 2) * w
        ax.bar(x, mean, w * 0.95, color=colors[m], label=labels[m])
        ax.errorbar(x, mean, yerr=[mean - lo, hi - mean], fmt="none", ecolor="black", capsize=3, lw=1.2)
    ax.set_xticks(range(len(years)), [str(y) for y in years], fontsize=15)
    ax.tick_params(axis="y", labelsize=14)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_title(title, fontsize=17, pad=12)
    top = max(per_seed[per_seed["model"].isin(models)].groupby(["model", "year"])[metric].quantile(0.95))
    ax.set_ylim(0, top * 1.28)
    ax.legend(fontsize=13, frameon=False, loc="upper center", ncol=len(models))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.5, 0.012, "\n".join(textwrap.wrap(footnote, 120)), ha="center", va="bottom",
             fontsize=11, color="#444444")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_charts() -> None:
    ps = pd.read_csv(RES / "08_per_seed.csv")
    cnt = pd.read_csv(RES / "08_winner_by_year.csv")
    c = cnt[(cnt["target"] == "hospital") & (cnt["scope"] == "dow4_vs_hgbr") & (cnt["metric"] == "waste_pct_mean")]
    n_gb = int((c["winner"] == "hgbr").sum()); n_d = int((c["winner"] == "dow4").sum())
    labels = {"dow4": "Average of the last 4 same weekdays", "hgbr": "Machine learning (gradient boosting)",
              "chronos": "Free pretrained model (Chronos-Bolt)"}
    colors = {"dow4": "#1b9e77", "hgbr": "#d95f02", "chronos": "#7570b3"}
    foot = ("Aachen hospital public data, 8 Jan to 18 Dec of each year. Each forecast is set so it has the "
            "hospital's own number of short days that year. Bars = average of 30 simulated runs; black lines = "
            "5th to 95th percentile of runs. A learning exercise on public data, not a real-world result.")
    grouped_chart(ps, "waste_pct", ["dow4", "hgbr"], labels, colors,
                  f"No forecast won every year: machine learning wasted less in {n_gb} of 7 years,\n"
                  f"the simple weekday average in {n_d}",
                  "Platelets thrown away\n(% of units used)", foot, M.CHARTS / "m5_multiyear_waste.png")
    c2 = cnt[(cnt["target"] == "hospital") & (cnt["scope"] == "dow4_vs_chronos") & (cnt["metric"] == "wasted_plus_emergency_mean")]
    n_c = int((c2["winner"] == "chronos").sum())
    grouped_chart(ps, "lost_units", ["dow4", "hgbr", "chronos"], labels, colors,
                  f"Counting thrown-away plus emergency units, the pretrained model beat\n"
                  f"the simple weekday average in {n_c} of 7 years",
                  "Units thrown away + emergency units\n(per year)", foot, M.CHARTS / "m5_multiyear_lost_units.png")


if __name__ == "__main__":
    main()
    make_charts()
