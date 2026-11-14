#!/usr/bin/env python3
"""Shared helpers for milestone 5 (multi-year test, reality check, US one-change runs).

Educational / advisory only. Never clinical. Public Aachen data only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lib_m4 as L

RESULTS = L.PROJECT_ROOT / "results/m5"
CHARTS = L.CHART_DIR
YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018]
K_GRID = L.K_GRID


def match_at(res_model: dict, target: float, demand_total: float, k_grid=K_GRID) -> pd.DataFrame:
    """Per seed, interpolate waste %, emergency units and k along the k grid to the
    first point where shortage days drop to <= target (same rule as script 03, but
    emergency units are now interpolated the same way as waste, not read at the
    nearest grid k)."""
    W, SD, SU = res_model["waste_pct"], res_model["shortage_days"], res_model["short_units"]
    MO = res_model["monday_share_of_short_days"]
    rows = []
    for s in range(W.shape[0]):
        idx = np.where(SD[s] <= target)[0]
        if not len(idx):
            rows.append(dict(seed=s, waste_pct=np.nan, short_units=np.nan, k=np.nan, monday_share=np.nan))
            continue
        j = idx[0]
        if j == 0 or SD[s, j - 1] == SD[s, j]:
            w, su, k, mo = W[s, j], SU[s, j], k_grid[j], MO[s, j]
        else:
            f = (SD[s, j - 1] - target) / (SD[s, j - 1] - SD[s, j])
            w = W[s, j - 1] + f * (W[s, j] - W[s, j - 1])
            su = SU[s, j - 1] + f * (SU[s, j] - SU[s, j - 1])
            k = k_grid[j - 1] + f * (k_grid[j] - k_grid[j - 1])
            mo = MO[s, j - 1] + f * (MO[s, j] - MO[s, j - 1])
        rows.append(dict(seed=s, waste_pct=w, short_units=su, k=k, monday_share=mo))
    out = pd.DataFrame(rows)
    out["waste_units"] = out["waste_pct"] * demand_total / 100
    out["lost_units"] = out["waste_units"] + out["short_units"]
    return out


def p5(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return np.percentile(x, 5) if len(x) else np.nan


def p95(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return np.percentile(x, 95) if len(x) else np.nan
