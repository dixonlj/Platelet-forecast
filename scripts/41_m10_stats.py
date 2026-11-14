#!/usr/bin/env python3
"""Milestone 10: preregistered statistics for Aachen (prereg Sections 4.2-4.11, 5.1, 5.2).

ONE script computes all four primary comparisons together (safeguard 4).
Primary: forecast minus standing order (SO), waste % at each year's recorded short days,
calibrated simulation, R1. Block-level linear mixed model d ~ 1 + (1|year), REML,
CI mu +/- t(0.975, 6) SE, p from t with 6 df; fallback to the year-level paired t-test if
the model does not converge or is singular. Holm across the 4. Labels per Section 4.7.
Everything else is secondary/sensitivity, unadjusted.
Educational / advisory only. Public Aachen data. Not clinical.
Run: PYTHONPATH=scripts .venv/bin/python scripts/41_m10_stats.py
"""
from __future__ import annotations

import json
import pickle
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

import lib_m10 as X

OUT = X.OUT
RAW = OUT / "raw"
FC = ["gb", "dgb", "sarima", "cb"]
NAME = {"so": "Standing order", "wa4": "4-week weekday average", "gb": "Gradient boosting",
        "dgb": "Detrended gradient boosting", "sarima": "SARIMA", "cb": "Chronos-Bolt",
        "lasso": "Authors' LASSO (ref.)", "rnn": "Authors' RNN (ref.)"}
HYP = {"gb": "H1a", "dgb": "H1b", "sarima": "H1c", "cb": "H1d"}
MMD = 0.5


def load(scn, rule="R1"):
    out = {}
    for Y in X.TEST_YEARS:
        with open(RAW / f"{scn}__{rule}__{Y}.pkl", "rb") as fh:
            out[Y] = pickle.load(fh)
    return out


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def per_run_wpct(t):
    return 100 * t["waste_units"] / t["demand"]


def yearly(res, pol, base, target="recorded", outcome="waste_pct", cost=False):
    """7 yearly differences pol - base (mean over runs matched in both)."""
    d = []
    for Y in X.TEST_YEARS:
        a, b = res[Y]["policies"][pol][target], res[Y]["policies"][base][target]
        if outcome == "waste_pct":
            va, vb = per_run_wpct(a), per_run_wpct(b)
        elif outcome == "lost_units":
            va, vb = a["waste_units"] + a["short_units"], b["waste_units"] + b["short_units"]
        elif outcome == "emergency_units":
            va, vb = a["short_units"], b["short_units"]
        elif outcome == "emergency_per_short_day":
            va, vb = a["short_units"] / a["short_days"], b["short_units"] / b["short_days"]
        elif outcome == "cost":
            va = 350 * a["waste_units"] + 700 * a["short_units"]
            vb = 350 * b["waste_units"] + 700 * b["short_units"]
        d.append(np.nanmean(va) - np.nanmean(vb))
    return np.array(d)


def block_diffs(res, pol, base, target="recorded"):
    rows = []
    for Y in X.TEST_YEARS:
        a, b = res[Y]["policies"][pol][target], res[Y]["policies"][base][target]
        wa = 100 * a["blk_waste"] / a["blk_demand"]
        wb = 100 * b["blk_waste"] / b["blk_demand"]
        dd = np.nanmean(wa - wb, axis=0)
        for bi, v in enumerate(dd):
            rows.append(dict(year=Y, block=bi + 1, d=float(v)))
    return pd.DataFrame(rows)


def year_tests(d):
    d = np.asarray(d, float); n = len(d)
    m, se = d.mean(), d.std(ddof=1) / np.sqrt(n)
    t = stats.t.ppf(0.975, n - 1)
    return dict(yr_mean=m, yr_se=se, yr_ci_lo=m - t * se, yr_ci_hi=m + t * se,
                yr_p=float(2 * stats.t.sf(abs(m / se), n - 1)) if se > 0 else np.nan,
                years_lower=int((d < 0).sum()), sign_p=stats.binomtest(int((d < 0).sum()), n, 0.5).pvalue,
                wilcoxon_p=stats.wilcoxon(d, method="exact").pvalue if np.any(d != 0) else 1.0)


def mixed(bd):
    """Prereg 4.3 model; returns dict with estimate, SE, method and fit notes."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            fit = smf.mixedlm("d ~ 1", bd, groups=bd["year"]).fit(reml=True)
            ok = bool(fit.converged)
        except Exception as exc:  # noqa
            return dict(method="year-level t (mixed model error)", note=str(exc))
    msgs = [str(x.message) for x in w]
    tau2 = float(fit.cov_re.iloc[0, 0])
    singular = tau2 < 1e-8 * max(1e-12, fit.scale) or any("boundary" in m.lower() or "singular" in m.lower() for m in msgs)
    conv = ok and not any("converge" in m.lower() and "boundary" not in m.lower() for m in msgs)
    resid = bd["d"].values - fit.fittedvalues.values
    out = dict(mm_mu=float(fit.fe_params.iloc[0]), mm_se=float(fit.bse_fe.iloc[0]), mm_tau2=tau2,
               mm_sigma2=float(fit.scale), mm_converged=conv, mm_singular=bool(singular),
               mm_warnings=" | ".join(sorted(set(msgs)))[:300])
    # lag-1 correlation of residuals between consecutive blocks within a year
    r = pd.DataFrame(dict(year=bd["year"].values, block=bd["block"].values, e=resid)).sort_values(["year", "block"])
    pairs = [(g.e.values[:-1], g.e.values[1:]) for _, g in r.groupby("year")]
    x0 = np.concatenate([p[0] for p in pairs]); x1 = np.concatenate([p[1] for p in pairs])
    out["lag1_resid_corr"] = float(np.corrcoef(x0, x1)[0, 1])
    out["_resid"] = resid
    out["_fitted"] = fit.fittedvalues.values
    return out


def bootstrap2(bd, seed, B=10_000):
    rng = np.random.default_rng(seed)
    years = sorted(bd.year.unique())
    M = np.stack([bd[bd.year == y].sort_values("block").d.values for y in years])  # (7,12)
    ny, nb = M.shape
    yi = rng.integers(0, ny, size=(B, ny))
    bi = rng.integers(0, nb, size=(B, ny, nb))
    means = M[yi[:, :, None], bi].mean(axis=(1, 2))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def analyse(res, pol, base, target="recorded", seed=20261114, boot=True):
    yd = yearly(res, pol, base, target)
    bd = block_diffs(res, pol, base, target)
    yt = year_tests(yd)
    mm = mixed(bd)
    tcrit, t90 = stats.t.ppf(0.975, 6), stats.t.ppf(0.95, 6)
    if "mm_mu" in mm and mm["mm_converged"] and not mm["mm_singular"]:
        mu, se, method = mm["mm_mu"], mm["mm_se"], "mixed model (REML), t with 6 df"
    else:
        mu, se, method = yt["yr_mean"], yt["yr_se"], "year-level paired t (pre-declared fallback: mixed model " + \
            ("singular" if mm.get("mm_singular") else "did not converge") + ")"
    p = float(2 * stats.t.sf(abs(mu / se), 6)) if se > 0 else np.nan
    row = dict(policy=pol, vs=base, target=target, mu=mu, se=se, ci_lo=mu - tcrit * se, ci_hi=mu + tcrit * se,
               ci90_lo=mu - t90 * se, ci90_hi=mu + t90 * se, p=p, method=method,
               **{k: v for k, v in mm.items() if not k.startswith("_")}, **yt,
               yearly_diffs=";".join(f"{v:.3f}" for v in yd))
    if boot:
        row["boot2_ci_lo"], row["boot2_ci_hi"] = bootstrap2(bd, seed)
    return row, bd, mm


def label(r, holm_p):
    if holm_p < 0.05 and r["mu"] < 0:
        return "Waste reduction demonstrated" + (" and practically meaningful" if r["mu"] <= -MMD else
                                                 " (not practically meaningful: smaller than 0.5 points)")
    if holm_p < 0.05 and r["mu"] > 0:
        return "Waste increase demonstrated"
    if r["ci90_lo"] > -MMD and r["ci90_hi"] < MMD:
        return "Practically equivalent (90% CI within +/-0.5 points; TOST, unadjusted)"
    return f"Not demonstrated (inconclusive): compatible with {r['ci_lo']:+.2f} to {r['ci_hi']:+.2f} points"


def mean_waste(res, pol, target="recorded"):
    return float(np.mean([np.nanmean(per_run_wpct(res[Y]["policies"][pol][target])) for Y in X.TEST_YEARS]))


def tradeoff_summary(res, pol, base):
    """Mean waste gap vs base across short-day levels 20-50, mean over runs then years."""
    gaps, excl = [], 0
    for Y in X.TEST_YEARS:
        a, b = res[Y]["policies"][pol]["tradeoff"], res[Y]["policies"][base]["tradeoff"]
        ma = np.where(np.isnan(a).any(axis=0), np.nan, np.nanmean(a, axis=0)) if True else None
        mb = np.where(np.isnan(b).any(axis=0), np.nan, np.nanmean(b, axis=0))
        g = ma - mb
        excl += int(np.isnan(g).sum())
        gaps.append(np.nanmean(g) if np.isfinite(g).any() else np.nan)
    return np.array(gaps), excl


def main():
    main1 = load("main", "R1")
    rows, bds, mms = [], {}, {}
    for pol in FC:
        r, bd, mm = analyse(main1, pol, "so")
        rows.append(r); bds[pol] = bd; mms[pol] = mm
    prim = pd.DataFrame(rows)
    prim.insert(0, "hypothesis", [HYP[p] for p in prim.policy])
    prim["p_holm"] = holm(prim.p.values)
    prim["label"] = [label(r, hp) for (_, r), hp in zip(prim.iterrows(), prim.p_holm)]
    prim["mean_waste_policy"] = [mean_waste(main1, p) for p in prim.policy]
    prim["mean_waste_so"] = mean_waste(main1, "so")
    labs = prim.label.tolist()
    if any(l.startswith("Waste reduction") for l in labs):
        rq1 = "Yes"
    elif all(l.startswith("Practically equivalent") or l.startswith("Waste increase") for l in labs):
        rq1 = "No, and no forecast exceeds the MMD"
    else:
        rq1 = "Not demonstrated"
    prim.to_csv(OUT / "41_primary_H1.csv", index=False)
    pd.concat([bds[p].assign(policy=p) for p in FC]).to_csv(OUT / "41_primary_block_diffs.csv", index=False)

    # residual plots (assumption check 4.11)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5), sharey=True)
    for ax, pol in zip(axes, FC):
        mm = mms[pol]
        if "_resid" in mm:
            ax.scatter(mm["_fitted"], mm["_resid"], s=14, color="#555555")
            ax.axhline(0, color="k", lw=0.8)
        ax.set_title(f"{NAME[pol]} minus standing order", fontsize=11)
        ax.set_xlabel("Fitted block gap (points)")
    axes[0].set_ylabel("Residual (points)")
    fig.suptitle("Mixed-model residuals by block: no strong pattern expected (assumption check)", fontsize=13)
    fig.tight_layout(); fig.savefig(OUT / "41_residual_plots.png", dpi=120); plt.close(fig)

    # ---------------- secondary ----------------
    sec = []
    for pol in FC + ["so"]:   # RQ2 vs WA4
        r, _, _ = analyse(main1, pol, "wa4", seed=20261114)
        sec.append(dict(analysis="RQ2 vs 4-week weekday average (R1, recorded short days)", **r))
    for rule in ("R2", "R3"):  # RQ4
        rr = load("main", rule)
        for pol in FC:
            r, _, _ = analyse(rr, pol, "so", seed=20261114)
            r["mean_waste_policy"] = mean_waste(rr, pol); r["mean_waste_so"] = mean_waste(rr, "so")
            sec.append(dict(analysis=f"RQ4 rule {rule} vs standing order (recorded short days)", **r))
    for tgt in ("fixed20", "fixed50"):   # 5.2.7
        for base in ("so", "wa4"):
            for pol in FC + (["so"] if base == "wa4" else []):
                r, _, _ = analyse(main1, pol, base, target=tgt, seed=20261114)
                sec.append(dict(analysis=f"Sensitivity 5.2.7: {tgt[5:]} short days a year vs {base}", **r))
    secdf = pd.DataFrame(sec)
    secdf.to_csv(OUT / "41_secondary_waste.csv", index=False)

    # RQ3 trade-off summary
    tro = []
    for base in ("so", "wa4"):
        for pol in FC + (["so"] if base == "wa4" else []):
            g, excl = tradeoff_summary(main1, pol, base)
            yt = year_tests(g)
            tro.append(dict(policy=pol, vs=base, mean_gap_20_50=float(np.nanmean(g)), **yt,
                            excluded_year_levels=excl, yearly=";".join(f"{v:.3f}" for v in g)))
    pd.DataFrame(tro).to_csv(OUT / "41_tradeoff_summary.csv", index=False)
    # pooled curves (mean over years) for the chart
    curves = {}
    for pol in ["so", "wa4"] + FC:
        M = []
        for Y in X.TEST_YEARS:
            a = main1[Y]["policies"][pol]["tradeoff"]
            M.append(np.where(np.isnan(a).any(axis=0), np.nan, np.nanmean(a, axis=0)))
        curves[pol] = np.nanmean(np.array(M), axis=0)
    cdf = pd.DataFrame(curves, index=list(range(20, 51)))
    cdf.index.name = "short_days_per_year"
    cdf.to_csv(OUT / "41_tradeoff_curves_pooled.csv")

    # other secondary outcomes (year-level)
    oth = []
    for outcome in ("lost_units", "emergency_units", "emergency_per_short_day", "cost"):
        for base in ("so", "wa4"):
            for pol in FC + (["so"] if base == "wa4" else []):
                d = yearly(main1, pol, base, outcome=outcome)
                oth.append(dict(outcome=outcome, policy=pol, vs=base, **year_tests(d)))
    pd.DataFrame(oth).to_csv(OUT / "41_secondary_other_outcomes.csv", index=False)

    # ---------------- sensitivities 5.2.1-5.2.5 ----------------
    import glob
    scns = sorted(set(p.split("/")[-1].split("__")[0] for p in glob.glob(str(RAW / "*__R1__*.pkl"))) - {"main"})
    sens = []
    for scn in scns:
        rr = load(scn, "R1")
        for pol in FC + [p for p in ("lasso", "rnn") if p in rr[2012]["policies"]]:
            r, _, _ = analyse(rr, pol, "so", boot=False)
            r["mean_waste_policy"] = mean_waste(rr, pol); r["mean_waste_so"] = mean_waste(rr, "so")
            r["mean_waste_wa4"] = mean_waste(rr, "wa4")
            sens.append(dict(scenario=scn, **r))
    sensdf = pd.DataFrame(sens)
    sensdf.to_csv(OUT / "41_sensitivity_vs_so.csv", index=False)

    # 5.2.6 cushion chosen in advance (k matched to previous year's recorded short days, held)
    adv = []
    for pol in ["so", "wa4"] + FC:
        for Y in X.TEST_YEARS[1:]:
            k_prev = float(np.nanmean(main1[Y - 1]["policies"][pol]["recorded"]["k"]))
            c = main1[Y]["policies"][pol]["curves"]
            kg = c["k_grid"]
            w = np.array([np.interp(k_prev, kg, c["waste_units"][s]) for s in range(c["waste_units"].shape[0])])
            sd = np.array([np.interp(k_prev, kg, c["short_days"][s]) for s in range(c["short_days"].shape[0])])
            dem = c["demand"][0, 0]
            adv.append(dict(policy=pol, year=Y, k_from_prev_year=k_prev, waste_pct=100 * w.mean() / dem,
                            short_days=sd.mean(), recorded_short_days=main1[Y]["target_recorded"]))
    advdf = pd.DataFrame(adv)
    advdf.to_csv(OUT / "41_cushion_in_advance_by_year.csv", index=False)
    advs = []
    for pol in FC + ["wa4"]:
        a = advdf[advdf.policy == pol].set_index("year"); b = advdf[advdf.policy == "so"].set_index("year")
        dw, ds = (a.waste_pct - b.waste_pct).values, (a.short_days - b.short_days).values
        yt = year_tests(dw)
        advs.append(dict(policy=pol, vs="so", mean_waste_policy=a.waste_pct.mean(), mean_waste_so=b.waste_pct.mean(),
                         mean_short_days_policy=a.short_days.mean(), mean_short_days_so=b.short_days.mean(),
                         waste_gap=yt["yr_mean"], waste_gap_ci_lo=yt["yr_ci_lo"], waste_gap_ci_hi=yt["yr_ci_hi"],
                         short_day_gap=ds.mean(), years="2013-2018"))
    pd.DataFrame(advs).to_csv(OUT / "41_cushion_in_advance_summary.csv", index=False)

    # bookkeeping: fallbacks, extensions, dropped / flagged runs
    bk = []
    for scn in ["main"] + scns:
        for rule in (("R1", "R2", "R3") if scn == "main" else ("R1",)):
            rr = load(scn, rule)
            for Y, res in rr.items():
                for pol, pr in res["policies"].items():
                    st = np.array(pr["recorded"]["status"])
                    bk.append(dict(scenario=scn, rule=rule, year=Y, policy=pol, wa4_fallback_origins=pr["fallbacks"],
                                   k_grid_extended_to_10=pr["extended"], runs_unmatched=int((st == "unmatched").sum()),
                                   runs_below_target_at_k0=int((st == "below_at_k0").sum()),
                                   sigma_units=json.dumps({str(k): round(v, 3) for k, v in pr["units"].items()})))
    pd.DataFrame(bk).to_csv(OUT / "41_bookkeeping.csv", index=False)

    summ = dict(rq1_answer=rq1, primary=prim.drop(columns=["yearly_diffs"]).to_dict(orient="records"))
    (OUT / "41_primary_summary.json").write_text(json.dumps(summ, indent=2, default=float))
    pd.set_option("display.width", 250)
    print(prim[["hypothesis", "policy", "mu", "ci_lo", "ci_hi", "p", "p_holm", "method", "label", "years_lower",
                "boot2_ci_lo", "boot2_ci_hi", "lag1_resid_corr", "mean_waste_policy", "mean_waste_so"]].round(3).to_string())
    print("RQ1:", rq1)


if __name__ == "__main__":
    main()
