#!/usr/bin/env python3
"""Shared helpers for milestone 4 scripts.

Educational / advisory only. Never clinical. Not an ordering tool.
Builds on scripts/02_aachen_real_data.py and scripts/03_realistic_sim.py.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results/m4"
CHART_DIR = PROJECT_ROOT / "charts"

_spec2 = importlib.util.spec_from_file_location("m2", PROJECT_ROOT / "scripts/02_aachen_real_data.py")
m2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(m2)

_spec3 = importlib.util.spec_from_file_location("m3", PROJECT_ROOT / "scripts/03_realistic_sim.py")
m3 = importlib.util.module_from_spec(_spec3)
_spec3.loader.exec_module(m3)

GROUPS = m3.GROUPS
GROUPS_ = m3.GROUPS_
SUB_TYPES_BASE = list(m3.SUB_TYPES)
SUB_TYPES = SUB_TYPES_BASE + ["abo_o_last"]
N_SEEDS = m3.N_SEEDS
K_GRID = m3.K_GRID
SEED0 = 1000

# Stanford Blood Center, "Blood Types", opened 2026-11-13:
# https://stanfordbloodcenter.org/donate-blood/blood-donation-facts/blood-types/
# Page footnote: "general estimations for educational purposes only...
# Original source: AABB Technical Manual 18th Edition".
US_GROUP_SHARE = {
    "O-": 0.066, "O+": 0.374, "A-": 0.063, "A+": 0.357,
    "B-": 0.015, "B+": 0.085, "AB-": 0.006, "AB+": 0.034,
}
US_GROUP_SHARE_SOURCE = (
    "Stanford Blood Center, Blood Types "
    "(https://stanfordbloodcenter.org/donate-blood/blood-donation-facts/blood-types/), "
    "opened 13 Nov 2026. Estimates attributed there to AABB Technical Manual, 18th Edition."
)

# Plasma-compatible (minor-compatible) ABO: donor plasma vs recipient red cells.
# O patient can receive A, B, or AB plasma; A or B can receive AB; AB has no extra.
US_PLASMA_ABO = {"0": ["A", "B", "AB"], "A": ["AB"], "B": ["AB"], "AB": []}
# Other non-O (not plasma-compatible, not identical): A<->B, and A or B to AB.
US_OTHER_NON_O = {"0": [], "A": ["B"], "B": ["A"], "AB": ["A", "B"]}

# Default assumption: share of RhD-negative demand from females aged 50 or under.
# No source gives this share for platelet recipients (see research/us_platelet_policies.md).
# 15% is a round figure: roughly the share of a mixed-age hospital population that is
# female and 50 or under, applied only to already RhD-negative demand. Sensitivity
# in script 07 varies this.
DEFAULT_RHDNEG_FEMALE_LE50_SHARE = 0.15


def year_window(year: int) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    """Warm-up and scoring window matching milestone 2/3, shifted to `year`."""
    sim_start = pd.Timestamp(f"{year - 1}-12-25")
    eval_start = pd.Timestamp(f"{year}-01-08")
    eval_end = pd.Timestamp(f"{year}-12-18")
    return sim_start, eval_start, eval_end


@contextmanager
def use_year_window(year: int):
    """Temporarily point script 02 date constants at a test year."""
    old = (m2.SIM_START, m2.EVAL_START, m2.EVAL_END)
    m2.SIM_START, m2.EVAL_START, m2.EVAL_END = year_window(year)
    try:
        yield year_window(year)
    finally:
        m2.SIM_START, m2.EVAL_START, m2.EVAL_END = old


def hospital_actual(df: pd.DataFrame, start, end) -> dict:
    d = df.loc[start:end]
    demand = int(d["transfused"].sum())
    waste = int(d["waste"].sum())
    short = int(d["purchase"].sum())
    return {
        "demand": demand,
        "waste_units": waste,
        "short_units": short,
        "shortage_days": int((d["purchase"] > 0).sum()),
        "waste_pct": 100 * waste / demand,
        "shortage_pct": 100 * short / demand,
        "n_days": int(len(d)),
    }


def load_series():
    df = m2.load_data()
    y = df["transfused"].astype(float)
    authors = {c: m2.author_window(df, c) for c in ("lasso2", "lasso4", "rnn2", "rnn4")}
    return df, y, authors


def sigma_for_year(y, fcs, year: int) -> dict:
    """Out-of-sample 2-day average miss in the year *before* the test year.

    Used as the fixed safety-stock unit, so the test year does not leak into k.
    """
    prev = year - 1
    origins = y.loc[pd.Timestamp(f"{prev - 1}-12-31"):pd.Timestamp(f"{prev}-12-30")].index
    act2 = m2.actual_window_sum(y, 2)
    return {k: m2.mae(act2[origins], m2.window_sum(fc, 2)[origins]) for k, fc in fcs.items()}


def us_donor_list(recipient: str, protected: bool) -> list[tuple[str, str]]:
    """US fallback after identical: plasma-compatible, then other non-O, then O last.

    Within each ABO step, same RhD is tried before a mismatch. RhD-pos units are
    never offered to a protected (RhD-neg female <=50) recipient.
    """
    abo, rh = recipient[:-1], recipient[-1]
    steps = ([(a, "abo_plasma") for a in US_PLASMA_ABO[abo]]
             + [(a, "abo_other") for a in US_OTHER_NON_O[abo]])
    if abo != "0":
        steps.append(("0", "abo_o_last"))
    out = []
    if rh == "+":
        out.append((abo + "-", "rhneg_to_rhpos"))
        for a, typ in steps:
            out += [(a + "+", typ), (a + "-", typ)]
    else:
        if not protected:
            out.append((abo + "+", "rhpos_to_rhneg"))
        for a, typ in steps:
            out.append((a + "-", typ))
            if not protected:
                out.append((a + "+", "rhpos_to_rhneg"))
    return out


def donor_lists_for(cfg: dict):
    """Return (unprotected lists, protected lists) keyed by internal group name."""
    mode = cfg.get("abo_mode", "guideline_plus_plasma")
    if mode == "us_plasma_first" or mode == "fifo_any_abo":
        unprot = {g: us_donor_list(g, protected=False) for g in GROUPS_}
        prot = {g: us_donor_list(g, protected=True) for g in GROUPS_}
        return unprot, prot
    # German / existing modes: same list for everyone (m3 already has last-resort
    # RhD-pos to RhD-neg if allow_rhpos_to_rhneg). Protected lists drop RhD-pos.
    unprot = {g: m3.donor_list(g, cfg) for g in GROUPS_}
    prot = {g: [(d, t) for d, t in unprot[g] if not d.endswith("+")] for g in GROUPS_}
    return unprot, prot


def draw_randomness(demand: np.ndarray, cfg: dict, seed: int):
    """Group demand, fill, rounding, life, and optional protected RhD-neg demand.

    The first four draws match script 03 when cfg matches, because the protected
    split is drawn *after* those, from the same Generator.
    """
    gd, fill, u, life = m3.draw_randomness(demand, cfg, seed)
    rng = np.random.default_rng(seed)
    # Replay the draws script 03 already made, so the next state is after them.
    # Re-calling draw_randomness above already consumed a fresh Generator; the
    # protected split needs its own stream that does not change the 03 draws.
    rng_p = np.random.default_rng(seed + 17_000_000)
    share = float(cfg.get("rhdneg_female_le50_share", 0.0) or 0.0)
    if cfg.get("pooled") or share <= 0:
        prot = np.zeros_like(gd)
        return gd, fill, u, life, prot
    prot = np.zeros_like(gd)
    gnames = GROUPS if gd.shape[1] == len(GROUPS) else ["ALL"]
    for i, g in enumerate(gnames):
        if str(g).endswith("-"):
            prot[:, i] = rng_p.binomial(gd[:, i].astype(int), min(1.0, share))
    return gd, fill, u, life, prot


def _add_life(stock, qty, life_arr, max_life):
    """Add qty (S,K,G) into the remaining-life slot given by life_arr (S,G)."""
    S, K, G, L = stock.shape
    for s in range(S):
        for g in range(G):
            r = int(life_arr[s, g]) - 1
            if 0 <= r < max_life:
                stock[s, :, g, r] += qty[s, :, g]


def _issue_identical(stock, need, take_fn):
    G = need.shape[2]
    for g in range(G):
        need[:, :, g] = take_fn(need[:, :, g], g)
    return need


def simulate(days, demand_by_seed, fill_by_seed, u_by_seed, life_by_seed,
             f2, f4, sigma, cfg, k_grid=None,
             eval_start=None, eval_end=None, max_life=None,
             safety_daily=None, order_rule="standard",
             daily_fc=None, prot_by_seed=None,
             order_window_fn=None, f3=None):
    """Inventory simulation, backwards-compatible with script 03 when defaults are used.

    Extra options (all off by default):
      safety_daily: {2: Series, 4: Series} of per-origin uncertainty. Then
        safety = k * safety_daily[n][day] * split, instead of k * sigma * split.
      order_rule: "standard" (script 03) or "expiry_aware" (ignore units that
        will expire before they can be used, and use group shares).
      daily_fc: DataFrame origin x horizon, used only by expiry_aware.
      prot_by_seed: list of (T,G) arrays of demand that cannot take RhD-pos units.
      max_life: warehouse depth; default is max(4, max life-on-arrival).
      order_window_fn: day -> days the evening order must cover (0 = no order);
        default m2.order_window (the documented Aachen calendar). Added in v6
        (script 26) to test other delivery calendars.
      f3: 3-day forecast totals, needed only when order_window_fn returns 3.
    Extra outputs (v6, do not change any earlier number): waste, emergency units
    and short days by weekday of the scored days (arrays S x K x 7).
    """
    order_window_fn = m2.order_window if order_window_fn is None else order_window_fn
    fwin = {2: f2, 3: f3, 4: f4}
    k_grid = K_GRID if k_grid is None else k_grid
    eval_start = m2.EVAL_START if eval_start is None else pd.Timestamp(eval_start)
    eval_end = m2.EVAL_END if eval_end is None else pd.Timestamp(eval_end)
    lives = list(cfg.get("life_on_arrival", {4: 1.0}).keys())
    max_life = max([4] + lives) if max_life is None else int(max_life)

    S = len(demand_by_seed)
    K = len(k_grid)
    gnames = ["ALL"] if cfg["pooled"] else GROUPS_
    G = len(gnames)
    gi = {g: i for i, g in enumerate(gnames)}
    T = len(days)
    p = np.array([1.0]) if cfg["pooled"] else np.array(
        [cfg["group_share"][g] for g in GROUPS]) / sum(cfg["group_share"].values())
    split = np.sqrt(p) if cfg["safety_split"] == "sqrt" else p
    safety_fixed = k_grid[None, :, None] * float(sigma) * split[None, None, :]

    D = np.stack(demand_by_seed)
    FILL = np.stack(fill_by_seed)
    U = np.stack(u_by_seed)
    LIFE = np.stack(life_by_seed)
    if prot_by_seed is None:
        PROT = np.zeros_like(D)
    else:
        PROT = np.stack(prot_by_seed)
        if PROT.ndim == 2:
            PROT = PROT[:, :, None]
        if PROT.shape[-1] == 1 and G > 1:
            PROT = np.zeros_like(D)
    UNPROT = D - PROT

    stock = np.zeros((S, K, G, max_life))
    init = np.round(m2.INITIAL_STOCK * p / 2)
    stock[:, :, :, 1] = init
    stock[:, :, :, 2] = init
    ordered = np.zeros((T + 3, S, K, G))

    eval_mask = (days >= eval_start) & (days <= eval_end)
    acc = {k: np.zeros((S, K)) for k in ("waste", "short", "short_days", "demand",
                                          "end_stock", "short_mondays")}
    subs = {t: np.zeros((S, K)) for t in SUB_TYPES}
    by_dow = {k: np.zeros((S, K, 7)) for k in ("waste", "short", "short_days")}
    unprot_lists, prot_lists = (None, None) if cfg["pooled"] else donor_lists_for(cfg)
    if unprot_lists is not None:
        unprot_lists = {g: [(gi[d], typ) for d, typ in lst] for g, lst in unprot_lists.items()}
        prot_lists = {g: [(gi[d], typ) for d, typ in lst] for g, lst in prot_lists.items()}
    rec_order = None if cfg["pooled"] else sorted(
        gnames, key=lambda g: (g[-1] == "+", {"AB": 0, "B": 1, "A": 2, "0": 3}[g[:-1]]))

    def take(need, g):
        for r in range(max_life):
            t_ = np.minimum(stock[:, :, g, r], need)
            stock[:, :, g, r] -= t_
            need = need - t_
        return need

    fifo_any = (not cfg["pooled"]) and cfg.get("abo_mode") == "fifo_any_abo"
    rhneg_idx = [i for i, g in enumerate(gnames) if str(g).endswith("-")]
    rhpos_idx = [i for i, g in enumerate(gnames) if str(g).endswith("+")]

    def issue_fifo_any(need_prot, need_unprot):
        # Oldest remaining life first. At a tied age, identical ABO is tried first,
        # then other groups. Protected demand may only take RhD-neg units.
        for r in range(max_life):
            for rec in rec_order:
                r_ = gi[rec]
                # identical first at this age
                t_ = np.minimum(stock[:, :, r_, r], need_prot[:, :, r_])
                stock[:, :, r_, r] -= t_
                need_prot[:, :, r_] -= t_
            for d in rhneg_idx:
                for rec in rec_order:
                    r_ = gi[rec]
                    if not str(rec).endswith("-"):
                        continue
                    before = need_prot[:, :, r_].copy()
                    t_ = np.minimum(stock[:, :, d, r], before)
                    stock[:, :, d, r] -= t_
                    need_prot[:, :, r_] -= t_
                    if eval_mask_today:
                        typ = "abo_plasma" if ABO_same(d, r_) else "abo_other"
                        # classify roughly
                        subs[_fifo_typ(gnames[d], rec)] += t_
            for rec in rec_order:
                r_ = gi[rec]
                t_ = np.minimum(stock[:, :, r_, r], need_unprot[:, :, r_])
                stock[:, :, r_, r] -= t_
                need_unprot[:, :, r_] -= t_
            for d in list(range(G)):
                for rec in rec_order:
                    r_ = gi[rec]
                    before = need_unprot[:, :, r_].copy()
                    t_ = np.minimum(stock[:, :, d, r], before)
                    stock[:, :, d, r] -= t_
                    need_unprot[:, :, r_] -= t_
                    if eval_mask_today:
                        subs[_fifo_typ(gnames[d], rec)] += t_
        return need_prot, need_unprot

    def _expiry_order(on_hand, in_transit, transit_life, n, day, safety):
        """Order-up-to forecast+safety, not counting units that expire unused."""
        # Expected demand path for days day+1 .. day+n, split by group.
        path = np.zeros((n, S, K, G))
        for h in range(1, n + 1):
            if daily_fc is not None and day in daily_fc.index and h in daily_fc.columns:
                fc_h = float(daily_fc.loc[day, h])
            else:
                tot = float(fwin[n][day])
                fc_h = tot / n
            path[h - 1] = fc_h * p[None, None, :]
        proj = stock.copy()
        _add_life(proj, in_transit, transit_life, max_life)
        uncovered_late = np.zeros((S, K, G))
        for h in range(n):
            need = path[h].copy()
            for r in range(max_life):
                t_ = np.minimum(proj[:, :, :, r], need)
                proj[:, :, :, r] -= t_
                need = need - t_
            # The new order arrives on the morning of day+2, so it cannot cover h=0.
            if h >= 1:
                uncovered_late += need
            proj[:, :, :, :-1] = proj[:, :, :, 1:]
            proj[:, :, :, -1] = 0
        leftover = proj.sum(axis=3)
        return np.maximum(0, np.round(uncovered_late + safety - leftover))

    eval_mask_today = False
    for ti, day in enumerate(days):
        eval_mask_today = bool(eval_mask[ti])
        promised = ordered[ti]
        if promised.any():
            got = np.minimum(promised, np.floor(promised * FILL[:, ti, None, None]
                                                + U[:, ti, None, :]))
            _add_life(stock, got, LIFE[:, ti, :], max_life)

        need_prot = np.broadcast_to(PROT[:, ti, None, :], (S, K, G)).astype(float).copy()
        need_unprot = np.broadcast_to(UNPROT[:, ti, None, :], (S, K, G)).astype(float).copy()

        if cfg["pooled"]:
            need = need_prot + need_unprot
            need = _issue_identical(stock, need, take)
            short = need.sum(axis=2)
        elif fifo_any:
            need_prot, need_unprot = issue_fifo_any(need_prot, need_unprot)
            short = need_prot.sum(axis=2) + need_unprot.sum(axis=2)
        else:
            need_prot = _issue_identical(stock, need_prot, take)
            need_unprot = _issue_identical(stock, need_unprot, take)
            for rec in rec_order:
                r_ = gi[rec]
                for d_, typ in prot_lists[rec]:
                    before = need_prot[:, :, r_].copy()
                    if not before.any():
                        break
                    need_prot[:, :, r_] = take(before, d_)
                    if eval_mask_today:
                        subs[typ] += before - need_prot[:, :, r_]
            for rec in rec_order:
                r_ = gi[rec]
                for d_, typ in unprot_lists[rec]:
                    before = need_unprot[:, :, r_].copy()
                    if not before.any():
                        break
                    need_unprot[:, :, r_] = take(before, d_)
                    if eval_mask_today:
                        subs[typ] += before - need_unprot[:, :, r_]
            short = need_prot.sum(axis=2) + need_unprot.sum(axis=2)

        wasted = stock[:, :, :, 0].sum(axis=2)
        stock[:, :, :, :-1] = stock[:, :, :, 1:]
        stock[:, :, :, -1] = 0
        on_hand = stock.sum(axis=3)
        n = order_window_fn(day)
        if n:
            fc = fwin[n][day]
            if safety_daily is not None:
                sd = safety_daily[n]
                unit = float(sd.loc[day]) if day in sd.index else float(sigma)
                safety = k_grid[None, :, None] * unit * split[None, None, :]
            else:
                safety = safety_fixed
            target = fc * p[None, None, :] + safety
            in_transit = ordered[ti + 1]
            if order_rule == "expiry_aware" and not cfg["pooled"]:
                tlife = LIFE[:, ti + 1, :] if ti + 1 < T else np.full((S, G), max_life)
                ordered[ti + m2.LEAD_DAYS] = _expiry_order(
                    on_hand, in_transit, tlife, n, day, safety)
            else:
                ordered[ti + m2.LEAD_DAYS] = np.maximum(
                    0, np.round(target - on_hand - in_transit))
        if eval_mask_today:
            acc["waste"] += wasted
            acc["short"] += short
            acc["short_days"] += short > 0
            acc["short_mondays"] += (short > 0) * (day.dayofweek == 0)
            acc["demand"] += D[:, ti].sum(axis=1)[:, None]
            acc["end_stock"] += on_hand.sum(axis=2)
            wd = day.dayofweek
            by_dow["waste"][:, :, wd] += wasted
            by_dow["short"][:, :, wd] += short
            by_dow["short_days"][:, :, wd] += short > 0

    n_eval = int(eval_mask.sum())
    out = {"waste_pct": 100 * acc["waste"] / acc["demand"],
           "shortage_days": acc["short_days"],
           "short_units": acc["short"],
           "shortage_pct": 100 * acc["short"] / acc["demand"],
           "monday_share_of_short_days": acc["short_mondays"] / np.maximum(acc["short_days"], 1),
           "mean_end_stock": acc["end_stock"] / n_eval}
    for t in SUB_TYPES:
        out[f"subs_{t}"] = subs[t]
    for k_, v_ in by_dow.items():
        out[f"{k_}_by_dow"] = v_
    return out


def ABO_same(d_idx, r_idx):
    return GROUPS_[d_idx][:-1] == GROUPS_[r_idx][:-1]


def _fifo_typ(donor: str, rec: str) -> str:
    if donor == rec:
        return "abo_plasma"  # unused; identical already subtracted
    if donor[:-1] == rec[:-1]:
        return "rhneg_to_rhpos" if donor.endswith("-") else "rhpos_to_rhneg"
    d_abo, r_abo = donor[:-1], rec[:-1]
    if d_abo in US_PLASMA_ABO.get(r_abo, []):
        return "abo_plasma"
    if d_abo == "0" and r_abo != "0":
        return "abo_o_last"
    return "abo_other"


def run_config(cfg, y, win, sigma, models, n_seeds=N_SEEDS, seed0=SEED0,
               year=None, safety_daily=None, order_rule="standard",
               daily_fc=None, k_grid=None, order_window_fn=None):
    if year is None:
        sim_start, eval_start, eval_end = m2.SIM_START, m2.EVAL_START, m2.EVAL_END
    else:
        sim_start, eval_start, eval_end = year_window(year)
    days = pd.date_range(sim_start, eval_end)
    demand = y.loc[days].values.astype(int)
    draws = [draw_randomness(demand, cfg, seed0 + s) for s in range(n_seeds)]
    gd, fill, u, life, prot = map(list, zip(*draws))
    out = {}
    for key in models:
        sdaily = None
        if safety_daily is not None and key in safety_daily:
            sdaily = safety_daily[key]
        dfc = None
        if daily_fc is not None and key in daily_fc:
            dfc = daily_fc[key]
        elif daily_fc is not None and "default" in (daily_fc or {}):
            dfc = daily_fc["default"]
        # daily_fc may also be a bare DataFrame meant for every model
        if daily_fc is not None and isinstance(daily_fc, pd.DataFrame):
            dfc = daily_fc
        out[key] = simulate(days, gd, fill, u, life, win[key][0], win[key][1],
                            sigma[key], cfg, k_grid=k_grid,
                            eval_start=eval_start, eval_end=eval_end,
                            safety_daily=sdaily, order_rule=order_rule,
                            daily_fc=dfc, prot_by_seed=prot,
                            order_window_fn=order_window_fn,
                            f3=win[key][2] if len(win[key]) > 2 else None)
    return out


def matched_table(res, target_sd, models):
    rows = []
    matched = {}
    k_at = {}
    for key in models:
        wm, km = m3.waste_at_shortage_days(res[key]["waste_pct"], res[key]["shortage_days"],
                                           target=target_sd)
        matched[key] = wm
        k_at[key] = km
        s = m3.summarise(wm)
        rows.append({
            "model": key,
            "target_shortage_days": target_sd,
            "waste_mean": s["mean"], "waste_sd": s["sd"],
            "waste_p05": s["p05"], "waste_p95": s["p95"],
            "n_seeds": s["n"],
            "k_mean": float(np.nanmean(km)),
        })
    return pd.DataFrame(rows), matched, k_at


def paired_vs(matched, baseline="dow4", models=None):
    models = list(matched) if models is None else models
    rows = []
    base = np.asarray(matched[baseline], float)
    for key in models:
        d = np.asarray(matched[key], float) - base
        ok = ~np.isnan(d)
        d = d[ok]
        rows.append({
            "model": key,
            "diff_vs_%s_mean" % baseline: d.mean() if len(d) else np.nan,
            "diff_sd": d.std(ddof=1) if len(d) > 1 else 0.0,
            "n": int(ok.sum()),
            "n_better": int((d < 0).sum()) if key != baseline else 0,
            "share_better": float((d < 0).mean()) if key != baseline and len(d) else 0.0,
        })
    return pd.DataFrame(rows)


def simple_bar_chart(path, title, ylabel, items, footnote, ylim=None, value_fmt="{:.1f}"):
    """One-idea bar chart: large labels, takeaway title, optional 5-95% whiskers.

    items: list of (label, value_or_array, color)
    """
    import textwrap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 7.8))
    tops, means = [], []
    for i, (label, vals, color) in enumerate(items):
        arr = np.asarray(vals, float)
        arr = arr[~np.isnan(arr)]
        mean = float(arr.mean())
        means.append(mean)
        ax.bar(i, mean, color=color, alpha=0.85, width=0.65)
        if len(arr) > 1:
            lo, hi = np.percentile(arr, 5), np.percentile(arr, 95)
            ax.errorbar(i, mean, yerr=[[mean - lo], [hi - mean]],
                        color="black", capsize=8, lw=1.5)
            top = hi
        else:
            top = mean
        tops.append(top)
    # Leave room above the tallest whisker for the bold labels and the title.
    needed = (max(tops) if tops else 1) * 1.18 + 1.2
    ymin, ymax = (ylim if ylim else (0, needed))
    if ymax < needed:
        ymax = needed
    ax.set_ylim(ymin, ymax)
    pad = 0.03 * (ymax - ymin)
    for i, (top, mean) in enumerate(zip(tops, means)):
        ax.text(i, top + pad, value_fmt.format(mean), ha="center", va="bottom",
                fontsize=15, fontweight="bold")
    ax.set_xticks(range(len(items)), [it[0] for it in items], fontsize=14)
    ax.set_ylabel(ylabel, fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.set_title(title, fontsize=16, pad=12)
    wrapped = "\n".join(textwrap.wrap(footnote.replace("\n", " "), width=108))
    fig.text(0.5, 0.015, wrapped, ha="center", va="bottom", fontsize=10, color="#444444")
    m2._style(ax)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def log_trackio(run_name: str, metrics: dict, config: dict | None = None) -> str:
    """Log metrics locally with Trackio. Never syncs to a Space or signs in."""
    os.environ.pop("TRACKIO_SPACE_ID", None)
    os.environ.pop("TRACKIO_SERVER_URL", None)
    os.environ.pop("HF_TOKEN", None)
    os.environ.pop("HUGGING_FACE_HUB_TOKEN", None)
    local = PROJECT_ROOT / "results/m4/trackio"
    local.mkdir(parents=True, exist_ok=True)
    os.environ["TRACKIO_DIR"] = str(local)
    try:
        import trackio
    except ImportError:
        return "skipped: trackio not installed"
    try:
        clean = {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v))
                 for k, v in metrics.items()}
        trackio.init(project="platelet-forecast-m4", name=run_name,
                     config=config or {}, space_id=None)
        trackio.log(clean)
        trackio.finish()
        return f"logged locally to {local} (project platelet-forecast-m4 / {run_name})"
    except Exception as exc:
        return f"skipped: {type(exc).__name__}: {exc}"
