#!/usr/bin/env python3
"""Shared helpers for milestone 10: the preregistered journal revision.

Contract: paper/osf_preregistration_final.md (registered on OSF by the author,
14 Nov 2026). Educational / advisory only. Public data only. Not clinical.

What is new compared with lib_m4/lib_m5 (nothing there is changed):
  * simulate_m10: the lib_m4.simulate logic (German ABO/RhD mode, no protected
    RhD-neg demand, standard or expiry-aware ordering) with
      - a cushion unit per order length n (R1: k * sigma_m(n); R2: k * sigma_m(2)),
      - extra outputs per 28-day scoring block (for the mixed model).
    It is checked against lib_m4.simulate in scripts/37_m10_selftest.py.
  * match_weights / apply_match: the lib_m5.match_at interpolation rule,
    returned as weights so any outcome (blocks, weekdays) is interpolated
    with exactly the same weights.
"""
from __future__ import annotations

import importlib.util
from copy import deepcopy

import numpy as np
import pandas as pd

import lib_m4 as L

P = L.PROJECT_ROOT
OUT = P / "results/m10"
m2, m3 = L.m2, L.m3
K_GRID = np.round(np.arange(0, 6.01, 0.25), 2)
K_EXT = np.round(np.arange(6.25, 10.01, 0.25), 2)
SEED0 = 1000
N_SEEDS = 30
N_BLOCKS = 12
CAL_YEARS = [2009, 2010, 2011]
TEST_YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018]

CALENDARS = {"tue_sat": {1, 2, 3, 4, 5}, "mon_fri": {0, 1, 2, 3, 4}, "mon_sat": {0, 1, 2, 3, 4, 5},
             "tue_sun": {1, 2, 3, 4, 5, 6}, "daily": set(range(7))}
CAL_LABEL = {"tue_sat": "Tue-Sat (documented)", "mon_fri": "Mon-Fri", "mon_sat": "Mon-Sat",
             "tue_sun": "Tue-Sun", "daily": "Every day"}
P2_GRID = [0.0, 0.10, 0.20]
P3_GRID = [0.0, 0.15, 0.30, 0.45, 0.60]
LAGS = ["0", "+1", "+2", "next_workday"]
DEMAND = {"unit": {"demand_split": "multinomial"},
          "ep2": {"demand_split": "episodes", "episode_mean_units": 2.0},
          "ep4": {"demand_split": "episodes", "episode_mean_units": 4.0}}
SHORTFALL = {"none": {"shortfall_day_prob": 0.0},
             "v9_10pct": {"shortfall_day_prob": 0.10, "shortfall_fill_range": (0.5, 0.9)},
             "heavy_25pct": {"shortfall_day_prob": 0.25, "shortfall_fill_range": (0.3, 0.8)}}
V9_BASE = dict(calendar="tue_sat", p2=0.0, p3=0.30, lag="0", demand="unit", shortfall="v9_10pct")


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, P / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_window_fn(arrive: set):
    """day -> days the evening order covers (0 = no order). Same rule as script 26."""
    table = {}
    for dow in range(7):
        a = (dow + m2.LEAD_DAYS) % 7
        if a not in arrive:
            table[dow] = 0
            continue
        gap = next(g for g in range(1, 8) if (a + g) % 7 in arrive)
        table[dow] = 1 + gap
    return table


def life_dict(p2: float, p3: float) -> dict:
    d = {4: round(1 - p2 - p3, 10), 3: p3, 2: p2}
    return {k: v for k, v in d.items() if v > 1e-12}


def make_cfg(spec: dict, pooled: bool = False) -> dict:
    cfg = deepcopy(m3.BASE)
    cfg.update(deepcopy(DEMAND[spec["demand"]]))
    cfg.update(deepcopy(SHORTFALL[spec["shortfall"]]))
    cfg["life_on_arrival"] = life_dict(spec["p2"], spec["p3"])
    cfg["pooled"] = bool(pooled)
    return cfg


def block_ids(days: pd.DatetimeIndex, eval_start, eval_end) -> np.ndarray:
    """-1 outside the scoring window; blocks 0..10 are 28 days from 8 Jan, block 11 the rest."""
    off = (days - pd.Timestamp(eval_start)).days.values
    b = np.minimum(off // 28, N_BLOCKS - 1)
    b[(days < pd.Timestamp(eval_start)) | (days > pd.Timestamp(eval_end))] = -1
    return b


def simulate_m10(days, D, FILL, U, LIFE, fwin, unit_by_n, cfg, k_grid, eval_start, eval_end,
                 window_table, order_rule="standard", daily_fc=None):
    """lib_m4.simulate logic for the German mode, with per-n cushion units and block outputs.

    D: (S,T,G) demand; FILL (S,T); U (S,T,G); LIFE (S,T,G).
    fwin: {n: Series of n-day forecast totals}; unit_by_n: {n: sigma used for the cushion}.
    """
    k_grid = np.asarray(k_grid, float)
    lives = list(cfg.get("life_on_arrival", {4: 1.0}).keys())
    max_life = max([4] + lives)
    S, T, G = D.shape
    K = len(k_grid)
    pooled = cfg["pooled"]
    gnames = ["ALL"] if pooled else L.GROUPS_
    gi = {g: i for i, g in enumerate(gnames)}
    p = np.array([1.0]) if pooled else np.array(
        [cfg["group_share"][g] for g in L.GROUPS]) / sum(cfg["group_share"].values())
    split = np.sqrt(p) if cfg["safety_split"] == "sqrt" else p
    safety_n = {n: k_grid[None, :, None] * float(u) * split[None, None, :] for n, u in unit_by_n.items()}

    stock = np.zeros((S, K, G, max_life))
    init = np.round(m2.INITIAL_STOCK * p / 2)
    stock[:, :, :, 1] = init
    stock[:, :, :, 2] = init
    ordered = np.zeros((T + 3, S, K, G))
    eval_mask = (days >= pd.Timestamp(eval_start)) & (days <= pd.Timestamp(eval_end))
    blk = block_ids(days, eval_start, eval_end)
    acc = {k: np.zeros((S, K)) for k in ("waste", "short", "short_days", "demand")}
    by_dow = {k: np.zeros((S, K, 7)) for k in ("waste", "short", "short_days")}
    by_blk = {k: np.zeros((S, K, N_BLOCKS)) for k in ("waste", "short", "short_days", "demand")}
    if not pooled:
        unprot = {g: [(gi[d], t) for d, t in m3.donor_list(g, cfg)] for g in L.GROUPS_}
        rec_order = sorted(gnames, key=lambda g: (g[-1] == "+", {"AB": 0, "B": 1, "A": 2, "0": 3}[g[:-1]]))

    def take(need, g):
        for r in range(max_life):
            t_ = np.minimum(stock[:, :, g, r], need)
            stock[:, :, g, r] -= t_
            need = need - t_
        return need

    def expiry_order(in_transit, transit_life, n, day, safety):
        path = np.zeros((n, S, K, G))
        for h in range(1, n + 1):
            fc_h = np.nan
            if daily_fc is not None and day in daily_fc.index:
                fc_h = float(daily_fc.loc[day, h])
            if not np.isfinite(fc_h):
                fc_h = float(fwin[n][day]) / n
            path[h - 1] = fc_h * p[None, None, :]
        proj = stock.copy()
        L._add_life(proj, in_transit, transit_life, max_life)
        uncovered_late = np.zeros((S, K, G))
        for h in range(n):
            need = path[h].copy()
            for r in range(max_life):
                t_ = np.minimum(proj[:, :, :, r], need)
                proj[:, :, :, r] -= t_
                need = need - t_
            if h >= 1:
                uncovered_late += need
            proj[:, :, :, :-1] = proj[:, :, :, 1:]
            proj[:, :, :, -1] = 0
        leftover = proj.sum(axis=3)
        return np.maximum(0, np.round(uncovered_late + safety - leftover))

    for ti, day in enumerate(days):
        promised = ordered[ti]
        if promised.any():
            got = np.minimum(promised, np.floor(promised * FILL[:, ti, None, None] + U[:, ti, None, :]))
            L._add_life(stock, got, LIFE[:, ti, :], max_life)
        need = np.broadcast_to(D[:, ti, None, :], (S, K, G)).astype(float).copy()
        for g in range(G):
            need[:, :, g] = take(need[:, :, g], g)
        if not pooled:
            for rec in rec_order:
                r_ = gi[rec]
                for d_, typ in unprot[rec]:
                    before = need[:, :, r_].copy()
                    if not before.any():
                        break
                    need[:, :, r_] = take(before, d_)
        short = need.sum(axis=2)
        wasted = stock[:, :, :, 0].sum(axis=2)
        stock[:, :, :, :-1] = stock[:, :, :, 1:]
        stock[:, :, :, -1] = 0
        on_hand = stock.sum(axis=3)
        n = window_table[day.dayofweek]
        if n:
            fc = fwin[n][day]
            safety = safety_n[n]
            in_transit = ordered[ti + 1]
            if order_rule == "expiry_aware" and not pooled:
                tlife = LIFE[:, ti + 1, :] if ti + 1 < T else np.full((S, G), max_life)
                ordered[ti + m2.LEAD_DAYS] = expiry_order(in_transit, tlife, n, day, safety)
            else:
                ordered[ti + m2.LEAD_DAYS] = np.maximum(0, np.round(fc * p[None, None, :] + safety
                                                                     - on_hand - in_transit))
        if eval_mask[ti]:
            dem = D[:, ti].sum(axis=1)[:, None]
            acc["waste"] += wasted
            acc["short"] += short
            acc["short_days"] += short > 0
            acc["demand"] += dem
            wd = day.dayofweek
            by_dow["waste"][:, :, wd] += wasted
            by_dow["short"][:, :, wd] += short
            by_dow["short_days"][:, :, wd] += short > 0
            b = blk[ti]
            by_blk["waste"][:, :, b] += wasted
            by_blk["short"][:, :, b] += short
            by_blk["short_days"][:, :, b] += short > 0
            by_blk["demand"][:, :, b] += dem
    out = {"waste_units": acc["waste"], "short_units": acc["short"], "short_days": acc["short_days"],
           "demand": acc["demand"], "k_grid": k_grid}
    for k_, v in by_dow.items():
        out[f"{k_}_dow"] = v
    for k_, v in by_blk.items():
        out[f"blk_{k_}"] = v
    return out


def draws_for(y, cfg, year, n_seeds=N_SEEDS, seed0=SEED0):
    sim_start, ev0, ev1 = L.year_window(year)
    days = pd.date_range(sim_start, ev1)
    demand = y.loc[days].values.astype(int)
    dr = [L.draw_randomness(demand, cfg, seed0 + s) for s in range(n_seeds)]
    gd, fill, u, life, _ = map(list, zip(*dr))
    return days, ev0, ev1, np.stack(gd), np.stack(fill), np.stack(u), np.stack(life)


def concat_k(a: dict, b: dict) -> dict:
    out = {}
    for k in a:
        if k == "k_grid":
            out[k] = np.concatenate([a[k], b[k]])
        else:
            out[k] = np.concatenate([a[k], b[k]], axis=1)
    return out


def run_policy(draws, fwin, unit_by_n, cfg, window_table, need_reach=20, order_rule="standard",
               daily_fc=None):
    """Run k = 0..6; if any run has not reached `need_reach` short days at k = 6, extend to 10."""
    days, ev0, ev1, D, FILL, U, LIFE = draws
    r = simulate_m10(days, D, FILL, U, LIFE, fwin, unit_by_n, cfg, K_GRID, ev0, ev1, window_table,
                     order_rule, daily_fc)
    if (r["short_days"][:, -1] > need_reach).any():
        r2 = simulate_m10(days, D, FILL, U, LIFE, fwin, unit_by_n, cfg, K_EXT, ev0, ev1, window_table,
                          order_rule, daily_fc)
        r = concat_k(r, r2)
        r["extended"] = True
    else:
        r["extended"] = False
    return r


def match_weights(SD: np.ndarray, target: float):
    """lib_m5.match_at rule, as (j0, j1, f, status) per run.

    status: 'ok', 'below_at_k0' (already <= target at k = 0; k = 0 values used, flagged),
    or 'unmatched' (never reached; run dropped)."""
    out = []
    for s in range(SD.shape[0]):
        idx = np.where(SD[s] <= target)[0]
        if not len(idx):
            out.append((0, 0, 0.0, "unmatched"))
            continue
        j = idx[0]
        if j == 0:
            out.append((0, 0, 0.0, "below_at_k0" if SD[s, 0] < target else "ok"))
        elif SD[s, j - 1] == SD[s, j]:
            out.append((j, j, 0.0, "ok"))
        else:
            f = (SD[s, j - 1] - target) / (SD[s, j - 1] - SD[s, j])
            out.append((j - 1, j, float(f), "ok"))
    return out


def apply_match(A: np.ndarray, w) -> np.ndarray:
    """A: (S,K,...) -> (S,...) interpolated; NaN for unmatched runs."""
    res = []
    for s, (j0, j1, f, st) in enumerate(w):
        if st == "unmatched":
            res.append(np.full(A.shape[2:], np.nan))
        else:
            res.append(A[s, j0] + f * (A[s, j1] - A[s, j0]))
    return np.array(res, dtype=float)


def matched_summary(r: dict, target: float) -> dict:
    """Per-run matched outcomes at a short-day target."""
    w = match_weights(r["short_days"], target)
    kk = np.broadcast_to(r["k_grid"][None, :], r["short_days"].shape)
    d = {"waste_units": apply_match(r["waste_units"], w), "short_units": apply_match(r["short_units"], w),
         "short_days": apply_match(r["short_days"], w), "demand": apply_match(r["demand"], w),
         "k": apply_match(kk, w), "waste_dow": apply_match(r["waste_dow"], w),
         "short_dow": apply_match(r["short_dow"], w), "short_days_dow": apply_match(r["short_days_dow"], w),
         "blk_waste": apply_match(r["blk_waste"], w), "blk_demand": apply_match(r["blk_demand"], w),
         "status": [x[3] for x in w]}
    d["waste_pct"] = 100 * d["waste_units"] / d["demand"]
    return d


def lag_shares(waste_dow: np.ndarray, lag: str) -> np.ndarray:
    """Weekday shares (Mon..Sun) of waste after a logging lag (applied after simulation)."""
    w = np.asarray(waste_dow, float)
    if lag == "0":
        x = w
    elif lag == "+1":
        x = np.roll(w, 1)
    elif lag == "+2":
        x = np.roll(w, 2)
    elif lag == "next_workday":
        x = w.copy(); x[0] += x[5] + x[6]; x[5] = 0; x[6] = 0
    else:
        raise ValueError(lag)
    return x / x.sum()


def recorded(df, years):
    rows = []
    wd = np.zeros(7)
    for Y in years:
        _, ev0, ev1 = L.year_window(Y)
        d = df.loc[ev0:ev1]
        rows.append({"year": Y, "demand": int(d.transfused.sum()), "waste_units": int(d.waste.sum()),
                     "emergency_units": int(d.purchase.sum()), "short_days": int((d.purchase > 0).sum())})
        wd += d.groupby(d.index.dayofweek).waste.sum().reindex(range(7), fill_value=0).values
    r = pd.DataFrame(rows)
    r["waste_pct"] = 100 * r.waste_units / r.demand
    r["eps"] = r.emergency_units / r.short_days
    return r, wd / wd.sum()


def mae_ntotal(y, fc: pd.DataFrame, n: int, origins) -> float:
    a = m2.actual_window_sum(y, n)
    f = m2.window_sum(fc, n)
    return m2.mae(a[origins], f[origins])


def prev_year_origins(y, year):
    prev = year - 1
    return y.loc[pd.Timestamp(f"{prev - 1}-12-31"):pd.Timestamp(f"{prev}-12-30")].index
