#!/usr/bin/env python3
"""Milestone 10, step 6 (prereg Section 2.5 / 4.4): Stanford replication (RQ5).

Simulator unchanged from S2-1 (lib_s2.pip_inventory: daily orders, arrive day i+3, 3 usable
days, oldest first, order-up-to = 3-day forecast + constant buffer b). R1 = R2 here; R3 not run.
Simulation starts 1 Jan 2014 (row 364); scoring 8 Jan 2014 - 31 May 2015 (rows 371-879, 509 days).
Primary target: shortage on 1% of scored days (5 days); b matched by linear interpolation between
integer buffers (grid -40..+80). Sensitivity targets 0 and 25 days.
Primary analysis: each of GB, dGB, SARIMA, CB minus SO, block waste % over 18 four-week blocks
(last block has 33 days); mean of block differences; 95% CI from a moving-block bootstrap
(blocks of 3 consecutive four-week blocks, 10,000 resamples, seed 20261115); two-sided p = share of
|centred bootstrap mean| >= |observed mean|; Holm across the 4. Also t-interval over blocks and
number of blocks lower. MMD (locked): 6% of SO's Stanford waste at the matched point.
Educational / advisory only. Public data (pip, GPL >= 2). Not clinical.
Run: PYTHONPATH=study2/scripts .venv/bin/python study2/scripts/11_m10_stanford_replication.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

import lib_s2 as S

OUT = S.STUDY / "results" / "s2m10"
B_GRID = np.arange(-40, 81, 1)
START, SC0, N = 364, 371, 880
FC = ["gb_noclin", "dgb", "sarima", "cb"]
NAME = {"so": "Standing order", "wd_avg4": "4-week weekday average", "gb_noclin": "Gradient boosting",
        "dgb": "Detrended gradient boosting", "sarima": "SARIMA", "cb": "Chronos-Bolt",
        "gb_clin_strict": "GB + clinical (strict)", "gb_clin_pip": "GB + clinical (pip)",
        "lasso_guan_strict": "Guan-style lasso (strict)", "lasso_guan_pip": "Guan-style lasso (pip)",
        "guan_lp_strict": "Guan LP (strict)", "guan_lp_pip": "Guan LP (pip)"}


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def t3_series(fc, model):
    f = fc[fc.model == model]
    cnt = f.groupby("origin").h.nunique()
    s = f.groupby("origin").fc.sum()
    s = s[cnt == 3]
    t = np.full(N, np.nan)
    t[s.index.values] = s.values
    return t


def blocks():
    idx = np.arange(SC0, N)
    b = np.minimum((idx - SC0) // 28, 17)
    return idx, b


def sweep(y, t):
    idx, bl = blocks()
    used = y[idx].sum()
    rows, bw = [], []
    for b in B_GRID:
        rr = S.pip_inventory(y, t + b, START)
        w, s = rr["w"][idx], rr["s"][idx]
        rows.append(dict(b=b, waste_units=w.sum(), waste_pct=100 * w.sum() / used,
                         short_days=int((s > 0).sum()), short_units=s.sum()))
        bw.append([w[bl == k].sum() for k in range(18)])
    return pd.DataFrame(rows), np.array(bw)


def match(cv, bw, target):
    sd = cv.short_days.values
    ix = np.where(sd <= target)[0]
    if not len(ix):
        return None
    j = ix[0]
    if j == 0:
        f, j0, flag = 0.0, 0, ("below_at_min_b" if sd[0] < target else "ok")
    else:
        j0, f, flag = j - 1, (sd[j - 1] - target) / (sd[j - 1] - sd[j]), "ok"
    lerp = lambda a: a[j0] + f * (a[j] - a[j0])
    return dict(b=lerp(cv.b.values.astype(float)), waste_pct=lerp(cv.waste_pct.values),
                waste_units=lerp(cv.waste_units.values), short_units=lerp(cv.short_units.values),
                short_days=lerp(sd.astype(float)), blk_waste=lerp(bw), flag=flag)


def mbb(d, seed=20261115, B=10_000, L=3):
    rng = np.random.default_rng(seed)
    n = len(d); nb = int(np.ceil(n / L))
    st = rng.integers(0, n - L + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(B, -1)[:, :n]
    return d[idx].mean(axis=1)


def main():
    df = S.load_aligned(); y = df["y"].values
    assert str(df.use_date.iloc[START].date()) == "2014-01-01" and str(df.use_date.iloc[SC0].date()) == "2014-01-08"
    assert N - SC0 == 509
    old = pd.read_csv(S.RESULTS / "02_forecasts.csv")
    new = pd.concat([pd.read_csv(OUT / "10_forecasts_so_dgb.csv"), pd.read_csv(OUT / "10b_forecasts_chronos.csv")])
    fc = pd.concat([old, new])
    models = ["so", "wd_avg4", "gb_noclin", "dgb", "sarima", "cb", "gb_clin_strict", "gb_clin_pip",
              "lasso_guan_strict", "lasso_guan_pip"]
    T = {m: t3_series(fc, m) for m in models}
    for v in ("pip", "strict"):
        T[f"guan_lp_{v}"] = pd.read_csv(S.RESULTS / f"03_guan_lp_tpred_{v}.csv")["t_pred"].values
    miss = {m: int(np.isnan(T[m][START:N - 3]).sum()) for m in T}
    idx, bl = blocks()
    dem_blk = np.array([y[idx][bl == k].sum() for k in range(18)])
    res = {}
    curves = []
    for m, t in T.items():
        cv, bw = sweep(y, t)
        curves.append(cv.assign(model=m))
        res[m] = {tg: match(cv, bw, tg) for tg in (0, 5, 25)}
    pd.concat(curves).to_csv(OUT / "11_buffer_sweep.csv", index=False)
    lev = []
    for m in T:
        for tg in (0, 5, 25):
            r = res[m][tg]
            lev.append(dict(model=m, target_short_days=tg, **({k: v for k, v in r.items() if k != "blk_waste"} if r else {})))
    lev = pd.DataFrame(lev)
    lev.to_csv(OUT / "11_matched_levels.csv", index=False)

    def compare(m, base, tg):
        a, b = res[m][tg], res[base][tg]
        d = 100 * a["blk_waste"] / dem_blk - 100 * b["blk_waste"] / dem_blk
        obs = d.mean()
        bm = mbb(d)
        p = float(np.mean(np.abs(bm - obs) >= abs(obs)))
        se = d.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(0.975, len(d) - 1)
        mmd = 0.06 * b["waste_pct"]
        return dict(policy=m, vs=base, target=tg, mean_block_diff=obs, boot_ci_lo=np.percentile(bm, 2.5),
                    boot_ci_hi=np.percentile(bm, 97.5), boot90_lo=np.percentile(bm, 5), boot90_hi=np.percentile(bm, 95),
                    p_boot=p, t_ci_lo=obs - tc * se, t_ci_hi=obs + tc * se, blocks_lower=int((d < 0).sum()),
                    window_waste_policy=a["waste_pct"], window_waste_base=b["waste_pct"],
                    window_diff=a["waste_pct"] - b["waste_pct"], mmd_points=mmd,
                    relative_diff_pct=100 * (a["waste_pct"] - b["waste_pct"]) / b["waste_pct"],
                    flag_policy=a["flag"], flag_base=b["flag"])

    prim = pd.DataFrame([compare(m, "so", 5) for m in FC])
    prim["p_holm"] = holm(prim.p_boot.values)

    def lab(r):
        if r.p_holm < 0.05 and r.mean_block_diff < 0:
            return "Waste reduction demonstrated" + (" and practically meaningful" if r.mean_block_diff <= -r.mmd_points
                                                     else " (smaller than the 6% minimum meaningful difference)")
        if r.p_holm < 0.05 and r.mean_block_diff > 0:
            return "Waste increase demonstrated"
        if r.boot90_lo > -r.mmd_points and r.boot90_hi < r.mmd_points:
            return "Practically equivalent (90% bootstrap interval within +/-6% of SO waste; unadjusted)"
        return f"Not demonstrated (inconclusive): compatible with {r.boot_ci_lo:+.2f} to {r.boot_ci_hi:+.2f} points"
    prim["label"] = prim.apply(lab, axis=1)
    prim.to_csv(OUT / "11_primary_stanford.csv", index=False)
    sec = [compare(m, "so", tg) for tg in (0, 25) for m in FC]
    sec += [compare(m, "wd_avg4", 5) for m in FC + ["so"]]
    sec += [compare(m, "so", 5) for m in ["wd_avg4", "gb_clin_strict", "gb_clin_pip", "lasso_guan_strict",
                                          "lasso_guan_pip", "guan_lp_strict", "guan_lp_pip"]]
    sec = pd.DataFrame(sec)
    sec.to_csv(OUT / "11_secondary_stanford.csv", index=False)
    (OUT / "11_missing_forecast_origins.json").write_text(json.dumps(miss, indent=2))
    pd.set_option("display.width", 250)
    print(lev[lev.target_short_days == 5].round(3).to_string())
    print(prim.drop(columns=["flag_policy", "flag_base"]).round(3).to_string())
    print(sec[["policy", "vs", "target", "mean_block_diff", "boot_ci_lo", "boot_ci_hi", "p_boot", "window_waste_policy",
               "window_waste_base", "blocks_lower"]].round(3).to_string())
    print("missing t_pred origins in sim:", miss)


if __name__ == "__main__":
    main()
