#!/usr/bin/env python3
"""
Milestone 3: a more realistic inventory simulation on the REAL Aachen 2018 holdout.

Educational / advisory only. Never clinical. Not an ordering tool.
No patient-level data is used: the Aachen file is daily unit counts only.
Blood groups are NOT in the file. We *simulate* them from population
proportions, so every ABO/RhD number below is an assumption, not an observation.

What changes compared with milestone 2 (scripts/02_aachen_real_data.py):
  1. ABO/RhD split. Each day's real demand (units transfused) is split at random
     across 8 groups (multinomial, German population proportions). Stock,
     ordering and issuing are kept per group, with simple substitution rules
     when the matching group runs out. Substitutions are counted.
  2. Delivery shortfalls. On some days the supplier/apheresis unit delivers only
     part of the order, and units arrive with 3 OR 4 days of life left.
  3. Randomness. Steps 1-2 are random, so every setting is run with 30 seeds.
     All models see the SAME random draws for a given seed ("common random
     numbers"), so model-vs-model differences are paired and fair.
  4. Safety-stock sweep (k) and comparison at matched shortage days, plus a
     one-at-a-time sensitivity analysis of the assumptions.

The forecasts themselves are unchanged: we import them from script 02, so the
numbers are the same 2018 out-of-sample forecasts as in milestone 2.

Run:  python3 scripts/03_realistic_sim.py      (about 1-3 minutes)
"""

from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results/realistic"
CHART_DIR = PROJECT_ROOT / "charts"

# Re-use everything from milestone 2 (data loading, forecasts, ordering calendar).
_spec = importlib.util.spec_from_file_location("m2", PROJECT_ROOT / "scripts/02_aachen_real_data.py")
m2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m2)

# ---------------------------------------------------------------------------
# ASSUMPTIONS (all configurable). Real-world numbers carry their source.
# ---------------------------------------------------------------------------
GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
ABO = {g: g[:-1] for g in GROUPS}
RH = {g: g[-1] for g in GROUPS}

BASE = {
    # (1) Share of each ABO/RhD group in the German population.
    # Source: DRK-Blutspendedienste, "Verteilung von Blutgruppen"
    #   https://www.drk-blutspende.de/verteilung  (also BRK Blutspendedienst,
    #   https://www.blutspendedienst.com/blut-blutgruppen/verteilung-der-blutgruppen)
    #   A+ 37, A- 6, 0+ 35, 0- 6, B+ 9, B- 2, AB+ 4, AB- 1  (%; Rh+ 85 / Rh- 15).
    # DRK says patients show the same shares as the population. We assume the
    # Aachen patients who get platelets do too (unverified; e.g. haematology
    # patients are not a random sample).
    "group_share": {"O-": 0.06, "O+": 0.35, "A-": 0.06, "A+": 0.37,
                    "B-": 0.02, "B+": 0.09, "AB-": 0.01, "AB+": 0.04},
    "pooled": False,            # True = ignore blood groups (milestone-2 style)

    # (1b) How demand is split. "multinomial": every unit independently gets a
    # group. "episodes": units come in patient episodes (mean size below) that
    # share one group, which is closer to reality (a haem-onc patient often
    # needs several units over a few days) and is more lumpy.
    "demand_split": "multinomial",
    "episode_mean_units": 2.0,

    # (1c) Substitution when the identical group is out. Order of preference:
    #   identical ABO and RhD ->
    #   same ABO, RhD-neg unit for an RhD-pos patient ->
    #   ABO-compatible per the German table (patient A: A or 0; B: B or 0;
    #     AB: AB, A, B or 0; 0: 0 only). Source: AMBOSS SOP "Transfusion von
    #     Thrombozytenkonzentraten" (table "AB0-Kompatibilitaet bei TK-Transfusion"),
    #     consistent with BAEK Querschnitts-Leitlinien 2020, ch. 2.7.2
    #     ("AB0-identische TK vorzuziehen").
    #   -> "plasma-compatible" last resort (donor plasma has no antibody against
    #     the patient's red cells: AB units for anyone, A/B units for 0 patients).
    # Modes: "identical", "guideline" (table only), "guideline_plus_plasma"
    # (default), "any_abo" (anything ABO goes before an emergency buy).
    "abo_mode": "guideline_plus_plasma",
    # BAEK QLL 2020 2.7.2: RhD-neg patients should PREFERABLY get RhD-neg
    # platelets ("vorzuziehen", grade 1C); RhD-pos units are allowed when
    # unavoidable (anti-D prophylaxis for girls/women of child-bearing age).
    # True = allow RhD-pos to RhD-neg as a last resort (counted separately).
    "allow_rhpos_to_rhneg": True,

    # (2) Delivery shortfalls. INVENTED assumption, no published Aachen rate:
    # on this share of delivery days the order is only partly filled (e.g.
    # donor no-shows for in-house apheresis), filling a uniform fraction.
    "shortfall_day_prob": 0.10,
    "shortfall_fill_range": (0.5, 0.9),
    # (2b) Life left on arrival (days usable incl. arrival day). Aachen paper:
    # 4 days left after production. We add variability (INVENTED 70/30 split).
    "life_on_arrival": {4: 0.7, 3: 0.3},

    # (3) Safety stock per group: total safety = k x sigma (model's 2017
    # out-of-sample MAE of 2-day totals, as in milestone 2), split across
    # groups by "sqrt" (k*sigma*sqrt(share): small groups get relatively more,
    # the usual square-root rule for Poisson-like demand) or "proportional".
    "safety_split": "sqrt",
}

N_SEEDS = 30
K_GRID = m2.K_GRID                  # 0 to 6 in 0.25 steps, as before
HOSPITAL = {"waste_pct": 12.30, "shortage_days": 31}   # recorded, Jan 8 - Dec 18 2018
TARGET_SD = 31                      # match models at the hospital's shortage-day count
MAX_LIFE = 4

SENSITIVITY = {   # one change at a time from BASE
    "Base (all assumptions on)": {},
    "Pooled: no blood groups": {"pooled": True},
    "ABO identical only (no ABO substitution)": {"abo_mode": "identical"},
    "Guideline table only (no plasma-compatible)": {"abo_mode": "guideline"},
    "Any ABO before emergency buy": {"abo_mode": "any_abo"},
    "No RhD-pos to RhD-neg": {"allow_rhpos_to_rhneg": False},
    "Patient episodes (mean 2 units)": {"demand_split": "episodes"},
    "Patient episodes (mean 4 units)": {"demand_split": "episodes", "episode_mean_units": 4.0},
    "No delivery shortfalls": {"shortfall_day_prob": 0.0},
    "Heavy shortfalls (25% of days, 30-80% filled)": {"shortfall_day_prob": 0.25,
                                                      "shortfall_fill_range": (0.3, 0.8)},
    "All units arrive with 4 days": {"life_on_arrival": {4: 1.0}},
    "All units arrive with 3 days": {"life_on_arrival": {3: 1.0}},
    "Half arrive with 2 days (extreme)": {"life_on_arrival": {4: 0.5, 2: 0.5}},
    "Proportional safety split": {"safety_split": "proportional"},
}
SENS_MODELS = ["dow4", "hgbr"]


# ---------------------------------------------------------------------------
# Substitution lists
# ---------------------------------------------------------------------------
GUIDELINE_ABO = {"A": ["0"], "B": ["0"], "AB": ["A", "B", "0"], "0": []}
PLASMA_ABO = {"0": ["A", "B", "AB"], "A": ["AB"], "B": ["AB"], "AB": []}
GROUPS_ = [g.replace("O", "0") for g in GROUPS]  # internal: zero for O, like the German tables


def donor_list(recipient: str, cfg: dict) -> list[tuple[str, str]]:
    """Ordered (donor, substitution_type) list for one recipient, after identical."""
    abo, rh = recipient[:-1], recipient[-1]
    alt_abo = []
    if cfg["abo_mode"] in ("guideline", "guideline_plus_plasma", "any_abo"):
        alt_abo += [(a, "abo_guideline") for a in GUIDELINE_ABO[abo]]
    if cfg["abo_mode"] == "guideline_plus_plasma":
        alt_abo += [(a, "abo_plasma") for a in PLASMA_ABO[abo]]
    if cfg["abo_mode"] == "any_abo":
        alt_abo += [(a, "abo_other") for a in ["0", "A", "B", "AB"]
                    if a != abo and a not in GUIDELINE_ABO[abo]]
    out = []
    if rh == "+":
        out.append((abo + "-", "rhneg_to_rhpos"))
        for a, t in alt_abo:
            out += [(a + "+", t), (a + "-", t)]
    else:
        for a, t in alt_abo:
            out.append((a + "-", t))
        if cfg["allow_rhpos_to_rhneg"]:
            out.append((abo + "+", "rhpos_to_rhneg"))
            for a, t in alt_abo:
                out.append((a + "+", "rhpos_to_rhneg"))
    return out


SUB_TYPES = ["rhneg_to_rhpos", "abo_guideline", "abo_plasma", "abo_other", "rhpos_to_rhneg"]


# ---------------------------------------------------------------------------
# Random draws for one seed (shared by every model: common random numbers)
# ---------------------------------------------------------------------------
def draw_randomness(demand: np.ndarray, cfg: dict, seed: int):
    """Return per-day group demand (T,G), fill fraction (T,), rounding noise
    (T,G) and life on arrival (T,G) for one seed."""
    rng = np.random.default_rng(seed)
    T = len(demand)
    p = np.array([cfg["group_share"][g] for g in GROUPS])
    p = p / p.sum()
    if cfg["pooled"]:
        gd = demand[:, None].astype(int)
    elif cfg["demand_split"] == "multinomial":
        gd = np.stack([rng.multinomial(int(d), p) for d in demand])
    else:  # patient episodes: geometric sizes, one group per episode
        gd = np.zeros((T, len(GROUPS)), dtype=int)
        q = 1.0 / cfg["episode_mean_units"]
        for t, d in enumerate(demand):
            left = int(d)
            while left > 0:
                size = min(left, rng.geometric(q))
                gd[t, rng.choice(len(GROUPS), p=p)] += size
                left -= size
    G = gd.shape[1]
    short_day = rng.random(T) < cfg["shortfall_day_prob"]
    lo, hi = cfg["shortfall_fill_range"]
    fill = np.where(short_day, rng.uniform(lo, hi, T), 1.0)
    u = rng.random((T, G))                   # stochastic rounding of partial fills
    lives, probs = zip(*cfg["life_on_arrival"].items())
    life = rng.choice(np.array(lives), size=(T, G), p=np.array(probs) / sum(probs))
    return gd, fill, u, life


# ---------------------------------------------------------------------------
# Vectorised simulation: all seeds x all k values at once, for one model.
# State stock[s, k, g, r]: units of group g with r+1 usable days left
# (r = 0 means "expires tonight").
# ---------------------------------------------------------------------------
def simulate(days, demand_by_seed, fill_by_seed, u_by_seed, life_by_seed,
             f2, f4, sigma, cfg, k_grid=K_GRID):
    S = len(demand_by_seed)
    K = len(k_grid)
    gnames = ["ALL"] if cfg["pooled"] else GROUPS_
    G = len(gnames)
    gi = {g: i for i, g in enumerate(gnames)}
    T = len(days)
    p = np.array([1.0]) if cfg["pooled"] else np.array(
        [cfg["group_share"][g] for g in GROUPS]) / sum(cfg["group_share"].values())
    split = np.sqrt(p) if cfg["safety_split"] == "sqrt" else p
    safety = k_grid[None, :, None] * sigma * split[None, None, :]       # (1,K,G)

    D = np.stack(demand_by_seed)            # (S,T,G)
    FILL = np.stack(fill_by_seed)           # (S,T)
    U = np.stack(u_by_seed)                 # (S,T,G)
    LIFE = np.stack(life_by_seed)           # (S,T,G)

    stock = np.zeros((S, K, G, MAX_LIFE))
    # Same start as milestone 2: 20 units, half expiring tomorrow, half the day after
    init = np.round(m2.INITIAL_STOCK * p / 2)
    stock[:, :, :, 1] = init
    stock[:, :, :, 2] = init
    ordered = np.zeros((T + 3, S, K, G))    # promised quantity by arrival day index
    order_life = {}                         # filled at arrival time

    eval_mask = (days >= m2.EVAL_START) & (days <= m2.EVAL_END)
    acc = {k: np.zeros((S, K)) for k in ("waste", "short", "short_days", "demand",
                                          "end_stock", "short_mondays")}
    subs = {t: np.zeros((S, K)) for t in SUB_TYPES}
    donor_lists = None if cfg["pooled"] else {
        g: [(gi[d], typ) for d, typ in donor_list(g, cfg)] for g in gnames}
    # recipients with fewest options first: RhD-neg, then rare ABO
    rec_order = None if cfg["pooled"] else sorted(
        gnames, key=lambda g: (g[-1] == "+", {"AB": 0, "B": 1, "A": 2, "0": 3}[g[:-1]]))

    def take(need, g):
        """Issue oldest-first from group g; returns units still needed."""
        for r in range(MAX_LIFE):
            t_ = np.minimum(stock[:, :, g, r], need)
            stock[:, :, g, r] -= t_
            need = need - t_
        return need

    for ti, day in enumerate(days):
        # --- morning: delivery (possibly short-filled, variable life) ---
        promised = ordered[ti]
        if promised.any():
            got = np.minimum(promised, np.floor(promised * FILL[:, ti, None, None]
                                                + U[:, ti, None, :]))
            for s in range(S):
                for g in range(G):
                    stock[s, :, g, LIFE[s, ti, g] - 1] += got[s, :, g]
        # --- daytime: issue identical first, then substitutes ---
        need = np.broadcast_to(D[:, ti, None, :], (S, K, G)).astype(float).copy()
        for g in range(G):
            need[:, :, g] = take(need[:, :, g], g)
        if not cfg["pooled"]:
            for rec in rec_order:
                r_ = gi[rec]
                for d_, typ in donor_lists[rec]:
                    before = need[:, :, r_].copy()
                    if not before.any():
                        break
                    need[:, :, r_] = take(before, d_)
                    if eval_mask[ti]:   # count scored days only
                        subs[typ] += before - need[:, :, r_]
        short = need.sum(axis=2)            # emergency purchases (all groups)
        # --- evening: outdate, age, order ---
        wasted = stock[:, :, :, 0].sum(axis=2)
        stock[:, :, :, :-1] = stock[:, :, :, 1:]
        stock[:, :, :, -1] = 0
        on_hand = stock.sum(axis=3)         # (S,K,G)
        n = m2.order_window(day)
        if n:
            fc = f2[day] if n == 2 else f4[day]
            target = fc * p[None, None, :] + safety
            in_transit = ordered[ti + 1]
            ordered[ti + m2.LEAD_DAYS] = np.maximum(0, np.round(target - on_hand - in_transit))
        if eval_mask[ti]:
            acc["waste"] += wasted
            acc["short"] += short
            acc["short_days"] += short > 0
            acc["short_mondays"] += (short > 0) * (day.dayofweek == 0)
            acc["demand"] += D[:, ti].sum(axis=1)[:, None]
            acc["end_stock"] += on_hand.sum(axis=2)
    n_eval = eval_mask.sum()
    out = {"waste_pct": 100 * acc["waste"] / acc["demand"],
           "shortage_days": acc["short_days"],
           "short_units": acc["short"],
           "shortage_pct": 100 * acc["short"] / acc["demand"],
           "monday_share_of_short_days": acc["short_mondays"] / np.maximum(acc["short_days"], 1),
           "mean_end_stock": acc["end_stock"] / n_eval}
    for t in SUB_TYPES:
        out[f"subs_{t}"] = subs[t]          # units issued as this substitution type
    return out                              # each value: array (S, K)


# ---------------------------------------------------------------------------
# Matching: waste at a target shortage-day count, per seed
# ---------------------------------------------------------------------------
def waste_at_shortage_days(waste_sk, sd_sk, target=TARGET_SD, k_grid=K_GRID):
    """For each seed, linearly interpolate along k to the first point where
    shortage days drop to <= target. NaN if never reached."""
    out = np.full(waste_sk.shape[0], np.nan)
    kout = np.full(waste_sk.shape[0], np.nan)
    for s in range(waste_sk.shape[0]):
        sd, w = sd_sk[s], waste_sk[s]
        idx = np.where(sd <= target)[0]
        if not len(idx):
            continue
        j = idx[0]
        if j == 0 or sd[j - 1] == sd[j]:
            out[s], kout[s] = w[j], k_grid[j]
        else:
            frac = (sd[j - 1] - target) / (sd[j - 1] - sd[j])
            out[s] = w[j - 1] + frac * (w[j] - w[j - 1])
            kout[s] = k_grid[j - 1] + frac * (k_grid[j] - k_grid[j - 1])
    return out, kout


def summarise(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if not len(x):
        return {"mean": np.nan, "sd": np.nan, "p05": np.nan, "p95": np.nan, "n": 0}
    return {"mean": x.mean(), "sd": x.std(ddof=1) if len(x) > 1 else 0.0,
            "p05": np.percentile(x, 5), "p95": np.percentile(x, 95), "n": len(x)}


# ---------------------------------------------------------------------------
# Forecasts (identical to milestone 2)
# ---------------------------------------------------------------------------
def build_forecasts():
    df = m2.load_data()
    y = df["transfused"].astype(float)
    base = m2.baseline_forecasts(y)
    feat = m2.hgbr_feature_table(y)
    authors = {c: m2.author_window(df, c) for c in ("lasso2", "lasso4", "rnn2", "rnn4")}
    fc17 = {**base, "hgbr": m2.hgbr_forecasts(feat, pd.Timestamp("2016-12-31"))}
    fc18 = {**base, "hgbr": m2.hgbr_forecasts(feat, pd.Timestamp("2017-12-31"))}
    # safety unit = 2017 out-of-sample MAE of 2-day totals (same as milestone 2)
    o17 = y.loc[pd.Timestamp("2016-12-31"):pd.Timestamp("2017-12-30")].index
    act2 = m2.actual_window_sum(y, 2)
    sigma = {k: m2.mae(act2[o17], m2.window_sum(fc, 2)[o17]) for k, fc in fc17.items()}
    for k in m2.AUTHOR_MODELS:
        sigma[k] = m2.mae(act2[o17], authors[f"{k}2"][o17])
    win = {k: (m2.window_sum(fc, 2), m2.window_sum(fc, 4)) for k, fc in fc18.items()}
    win.update({k: (authors[f"{k}2"], authors[f"{k}4"]) for k in m2.AUTHOR_MODELS})
    return y, win, sigma


ALL_MODELS = {**m2.MODELS, **m2.AUTHOR_MODELS}


def run_config(cfg, y, win, sigma, models, n_seeds=N_SEEDS, seed0=1000):
    days = pd.date_range(m2.SIM_START, m2.EVAL_END)
    demand = y.loc[days].values.astype(int)
    draws = [draw_randomness(demand, cfg, seed0 + s) for s in range(n_seeds)]
    gd, fill, u, life = map(list, zip(*draws))
    return {key: simulate(days, gd, fill, u, life, win[key][0], win[key][1],
                          sigma[key], cfg) for key in models}


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart_tradeoff(res, matched, path):
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.8), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    for key, name in ALL_MODELS.items():
        r = res[key]
        w, sd = r["waste_pct"], r["shortage_days"]
        mw, msd = w.mean(0), sd.mean(0)
        ls = "--" if key in m2.AUTHOR_MODELS else "-"
        lw, alpha = (1.0, 0.5) if key in ("naive", "last7", "same_dow") else (2.0, 1.0)
        ax.plot(mw, msd, ls, color=m2.COLORS[key], lw=lw, alpha=alpha, label=name)
        # band: 5-95% of waste across seeds at each k, and of shortage days
        ax.fill_betweenx(msd, np.percentile(w, 5, 0), np.percentile(w, 95, 0),
                         color=m2.COLORS[key], alpha=0.12 if alpha == 1 else 0.05, lw=0)
        ax.fill_between(mw, np.percentile(sd, 5, 0), np.percentile(sd, 95, 0),
                        color=m2.COLORS[key], alpha=0.12 if alpha == 1 else 0.05, lw=0)
    ax.plot(HOSPITAL["waste_pct"], HOSPITAL["shortage_days"], "*", ms=22, color="black",
            label="Hospital actual 2018 (12.3% waste, 31 days)", zorder=5)
    ax.axhline(TARGET_SD, color="black", lw=0.8, ls=":")
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 110)
    ax.set_xlabel("Waste (% of units transfused)")
    ax.set_ylabel("Shortage days (days with any emergency buy)")
    ax.set_title("Trade-off as safety stock k rises (line = mean of 30 seeds; "
                 "shading = 5-95% range)", fontsize=10)
    ax.annotate("Hospital actual 2018:\n12.3% waste, 31 days", (HOSPITAL["waste_pct"], TARGET_SD),
                xytext=(25, 40), textcoords="offset points", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="black"))
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.11),
              ncol=3, markerscale=0.6)
    m2._style(ax)

    ax = axes[1]
    keys = list(ALL_MODELS)
    data = [matched[k][~np.isnan(matched[k])] for k in keys]
    bp = ax.boxplot(data, orientation="horizontal", patch_artist=True, widths=0.6,
                    tick_labels=[ALL_MODELS[k] for k in keys], showfliers=False)
    for patch, k in zip(bp["boxes"], keys):
        patch.set_facecolor(m2.COLORS[k])
        patch.set_alpha(0.55)
    for i, d in enumerate(data):
        ax.plot(d, np.full(len(d), i + 1) + np.random.default_rng(i).uniform(-0.18, 0.18, len(d)),
                ".", color="black", ms=2.5, alpha=0.5)
    ax.axvline(HOSPITAL["waste_pct"], color="black", ls="--", lw=1)
    ax.text(HOSPITAL["waste_pct"], len(keys) + 0.55, " hospital 12.3%", fontsize=9, va="center")
    ax.invert_yaxis()
    ax.set_xlabel("Simulated waste % at the hospital's 31 shortage days")
    ax.set_title("Fair comparison: each model's waste when it is tuned to\n"
                 "have the same 31 shortage days (one dot per seed)", fontsize=10)
    m2._style(ax)
    fig.suptitle("Aachen 2018 holdout, realistic simulation: ABO/RhD split with substitution, "
                 "delivery shortfalls, 3-4 day life on arrival.\n"
                 "Blood groups are simulated from German population shares; not the "
                 "hospital's real process. Educational only.", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_sensitivity(sens, path):
    fig, ax = plt.subplots(figsize=(12, 7))
    names = list(SENSITIVITY)
    ypos = np.arange(len(names))
    h = 0.38
    for j, key in enumerate(SENS_MODELS):
        sub = sens[sens["model"] == key].set_index("scenario").loc[names]
        y_ = ypos + (j - 0.5) * h
        ax.barh(y_, sub["waste_at31_mean"], height=h, color=m2.COLORS[key], alpha=0.8,
                label=ALL_MODELS[key])
        ax.errorbar(sub["waste_at31_mean"], y_,
                    xerr=[sub["waste_at31_mean"] - sub["waste_at31_p05"],
                          sub["waste_at31_p95"] - sub["waste_at31_mean"]],
                    fmt="none", ecolor="black", lw=0.8, capsize=2)
    base = sens[(sens["scenario"] == names[0]) & (sens["model"] == "dow4")]["waste_at31_mean"].iloc[0]
    ax.axvline(base, color=m2.COLORS["dow4"], ls=":", lw=1)
    ax.axvline(HOSPITAL["waste_pct"], color="black", ls="--", lw=1)
    ax.text(HOSPITAL["waste_pct"], -0.9, "hospital 12.3%", fontsize=9, ha="center")
    ax.set_yticks(ypos, names)
    ax.invert_yaxis()
    ax.set_ylim(len(names) - 0.4, -1.2)
    ax.set_xlabel("Simulated waste % at 31 shortage days (bar = mean of 30 seeds; "
                  "whisker = 5-95%)")
    ax.set_title("Which assumption moves waste most? One change at a time from the base "
                 "realistic simulation\n(Aachen 2018 holdout; each model re-tuned to the "
                 "hospital's 31 shortage days)", fontsize=11)
    ax.legend(frameon=False, loc="lower right")
    m2._style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_headline(matched, path):
    """One simple chart for Liam: waste when every option has the hospital's
    31 short days. Same shortage level by design, so only waste differs."""
    items = [("Use yesterday's\nnumber", matched["naive"], m2.COLORS["naive"]),
             ("Average of the\nlast 4 same weekdays", matched["dow4"], m2.COLORS["dow4"]),
             ("Machine learning\n(gradient boosting)", matched["hgbr"], m2.COLORS["hgbr"]),
             ("What the hospital\nactually did (2018)", np.array([HOSPITAL["waste_pct"]]), "#222222")]
    fig, ax = plt.subplots(figsize=(12, 7.5))
    for i, (label, vals, color) in enumerate(items):
        v = vals[~np.isnan(vals)]
        mean = v.mean()
        ax.bar(i, mean, color=color, alpha=0.85, width=0.65)
        top = np.percentile(v, 95) if len(v) > 1 else mean
        if len(v) > 1:  # range across the 30 simulated runs
            ax.errorbar(i, mean, yerr=[[mean - np.percentile(v, 5)], [np.percentile(v, 95) - mean]],
                        color="black", capsize=8, lw=1.5)
        ax.text(i, top + 0.8, f"{mean:.1f}% wasted\n31 short days", ha="center",
                fontsize=15, fontweight="bold")
    ax.set_xticks(range(len(items)), [it[0] for it in items], fontsize=14)
    ax.set_ylabel("Platelets thrown away\n(% of units transfused)", fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.set_ylim(0, 30)
    ax.set_title("With the same 31 short days as the hospital, the machine learning forecast\n"
                 "would have thrown away the fewest platelets in our simulation",
                 fontsize=17, pad=14)
    fig.text(0.5, 0.01, "Aachen hospital, 2018. Simulated ordering with blood groups and short "
             "deliveries.\nBlack lines = 5th to 95th percentile of 30 simulated runs. A learning exercise, "
             "not a real result.", ha="center", fontsize=11, color="#444444")
    m2._style(ax)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    y, win, sigma = build_forecasts()
    (RESULTS_DIR / "assumptions_base.json").write_text(json.dumps(
        {**BASE, "life_on_arrival": {str(k): v for k, v in BASE["life_on_arrival"].items()},
         "n_seeds": N_SEEDS, "k_grid": list(map(float, K_GRID)),
         "safety_unit_sigma": {k: round(v, 3) for k, v in sigma.items()},
         "substitution_lists": {g: donor_list(g, BASE) for g in GROUPS_}}, indent=2))

    # --- 0. sanity check: pooled, no shortfalls, all 4 days == milestone 2 ---
    check_cfg = {**BASE, "pooled": True, "shortfall_day_prob": 0.0, "life_on_arrival": {4: 1.0}}
    chk = run_config(check_cfg, y, win, sigma, list(ALL_MODELS), n_seeds=1)
    m2_sweep = pd.read_csv(PROJECT_ROOT / "results/aachen/inventory_k_sweep.csv")
    diffs = []
    for key in ALL_MODELS:
        ref = m2_sweep[m2_sweep["model"] == key].sort_values("k")
        diffs.append(np.abs(chk[key]["waste_pct"][0] - ref["waste_pct"].values).max())
        diffs.append(np.abs(chk[key]["shortage_days"][0] - ref["shortage_days"].values).max())
    print("Reproduces milestone-2 sweep (max abs diff):", round(max(diffs), 4))

    # --- 1. base realistic run, all models ---
    res = run_config(BASE, y, win, sigma, list(ALL_MODELS))
    rows, matched, matched_k = [], {}, {}
    for key in ALL_MODELS:
        r = res[key]
        for ki, k in enumerate(K_GRID):
            row = {"model": key, "k": k}
            for m in ("waste_pct", "shortage_days", "short_units", "shortage_pct",
                      "mean_end_stock", "monday_share_of_short_days") + tuple(
                          f"subs_{t}" for t in SUB_TYPES):
                row[f"{m}_mean"] = r[m][:, ki].mean()
                row[f"{m}_sd"] = r[m][:, ki].std(ddof=1)
            rows.append(row)
        matched[key], matched_k[key] = waste_at_shortage_days(r["waste_pct"], r["shortage_days"])
    sweep = pd.DataFrame(rows)
    sweep.to_csv(RESULTS_DIR / "k_sweep_base_mean_sd.csv", index=False)

    # summary table
    k1 = list(K_GRID).index(1.0)
    k2 = list(K_GRID).index(2.0)
    summ = []
    for key, name in ALL_MODELS.items():
        r = res[key]
        mw, mk = summarise(matched[key]), summarise(matched_k[key])
        # substitutions and units short at the matched k (nearest grid k per seed)
        kidx = np.clip(np.round(matched_k[key] / 0.25).astype("float"), 0, len(K_GRID) - 1)
        def at_k(m):
            v = [r[m][s, int(kidx[s])] for s in range(N_SEEDS) if not np.isnan(kidx[s])]
            return np.mean(v) if v else np.nan
        summ.append({
            "model": name,
            "k1_waste_pct": r["waste_pct"][:, k1].mean(), "k1_waste_sd": r["waste_pct"][:, k1].std(ddof=1),
            "k1_shortage_days": r["shortage_days"][:, k1].mean(),
            "k1_shortage_days_sd": r["shortage_days"][:, k1].std(ddof=1),
            "k2_waste_pct": r["waste_pct"][:, k2].mean(),
            "k2_shortage_days": r["shortage_days"][:, k2].mean(),
            "at31_k_mean": mk["mean"],
            "at31_waste_mean": mw["mean"], "at31_waste_sd": mw["sd"],
            "at31_waste_p05": mw["p05"], "at31_waste_p95": mw["p95"], "at31_n_seeds": mw["n"],
            "at31_units_short": at_k("short_units"),
            "at31_monday_share": at_k("monday_share_of_short_days"),
            **{f"at31_subs_{t}": at_k(f"subs_{t}") for t in SUB_TYPES},
        })
    summ = pd.DataFrame(summ).round(2)
    summ.to_csv(RESULTS_DIR / "summary_base.csv", index=False)

    # paired difference vs 4-week weekday average (same seeds)
    paired = []
    for key in ALL_MODELS:
        d = matched[key] - matched["dow4"]
        s = summarise(d)
        paired.append({"model": ALL_MODELS[key], "diff_vs_dow4_mean": s["mean"],
                       "diff_sd": s["sd"], "diff_p05": s["p05"], "diff_p95": s["p95"],
                       "share_of_seeds_better_than_dow4": np.nanmean(d < 0)})
    paired = pd.DataFrame(paired).round(3)
    paired.to_csv(RESULTS_DIR / "paired_vs_dow4_at31.csv", index=False)
    pd.DataFrame({k: v for k, v in matched.items()}).to_csv(
        RESULTS_DIR / "per_seed_waste_at31.csv", index_label="seed")

    # --- 2. sensitivity, one change at a time ---
    sens_rows = []
    for name, change in SENSITIVITY.items():
        cfg = {**deepcopy(BASE), **change}
        rr = run_config(cfg, y, win, sigma, SENS_MODELS) if change else {k: res[k] for k in SENS_MODELS}
        for key in SENS_MODELS:
            wm, km = waste_at_shortage_days(rr[key]["waste_pct"], rr[key]["shortage_days"])
            s = summarise(wm)
            sens_rows.append({"scenario": name, "model": key, "waste_at31_mean": s["mean"],
                              "waste_at31_p05": s["p05"], "waste_at31_p95": s["p95"],
                              "waste_at31_sd": s["sd"], "k_at31_mean": np.nanmean(km),
                              "n_seeds_reaching_31": s["n"],
                              "k2_waste_mean": rr[key]["waste_pct"][:, k2].mean(),
                              "k2_shortage_days_mean": rr[key]["shortage_days"][:, k2].mean()})
        print("done:", name)
    sens = pd.DataFrame(sens_rows)
    base_w = sens[sens["scenario"] == "Base (all assumptions on)"].set_index("model")["waste_at31_mean"]
    sens["change_vs_base_pp"] = sens.apply(lambda r: r["waste_at31_mean"] - base_w[r["model"]], axis=1)
    sens = sens.round(2)
    sens.to_csv(RESULTS_DIR / "sensitivity.csv", index=False)

    # --- 3. charts ---
    chart_tradeoff(res, matched, CHART_DIR / "realistic_tradeoff_uncertainty.png")
    chart_sensitivity(sens, CHART_DIR / "realistic_sensitivity.png")
    chart_headline(matched, CHART_DIR / "realistic_headline_simple.png")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(summ.to_string(index=False))
    print(paired.to_string(index=False))
    print(sens.to_string(index=False))


if __name__ == "__main__":
    main()
