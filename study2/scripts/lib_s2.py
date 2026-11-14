#!/usr/bin/env python3
"""Shared helpers for study 2 (Stanford `pip` day3_data, public, GPL >= 2).

Educational / advisory only. Not clinical. No patient-level data. Nothing deployed.

Index convention used everywhere in study 2 (0-based row i of day3_data):
  y[i]          = platelet units used on calendar day use_date[i]
  use_date[i]   = date_inferred[i] - 1 day   (see 01_load_align.py: the usage column
                  is one day behind the weekday labels)
  "origin i"    = end of usage day i: we know y[0..i] and the clinical row(s) chosen
                  by the feature-lag setting.
  horizon h     = forecast of y[i+h]  (h = 1, 2, 3)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

STUDY = Path(__file__).resolve().parent.parent
DATA = STUDY / "data"
DERIVED = DATA / "derived"
RESULTS = STUDY / "results" / "s2m1"
CHARTS = STUDY / "charts"
RDA = DATA / "public" / "stanford_pip" / "day3_data.rda"

DOW_COLS = ["M", "T", "W", "Th", "F", "S", "Sn"]
CBC_COLS = ["PLTlow", "WBChigh", "RBClow", "HGBlow", "MCVlow", "MCHlow", "MCHClow", "RDW", "ALYM"]
CENSUS_COLS = ["B1", "B2", "B3", "C1", "C2", "C3", "CAPR.XFER.OVERFL", "CATH.PACU",
               "CDU.CLIN.DEC.UNIT", "D1CC", "D1CS", "D2", "D3", "DGR", "E1", "E2.ICU", "E29.ICU",
               "E3", "EMERGENCY.DEPARTMENT", "F3", "FGR", "G1", "G2P", "G2S", "H1", "H2"]
GUAN_COLS = DOW_COLS + ["seven_lag"] + CBC_COLS + CENSUS_COLS  # the 43 covariates, pip order
CLIN_COLS = CBC_COLS + CENSUS_COLS                               # 35 clinical drivers

# Rolling-origin design, matching Guan et al. (PNAS 2017): first 200 days train only,
# test from day 201 (0-based row 200) to day 880, retrain every 7 days.
FIRST_ORIGIN = 199          # 0-based; first forecast targets row 200 (= day 201)
N_ROWS = 880
RETRAIN_EVERY = 7
WINDOW_DAYS = 28            # rolling test windows for "who wins" counts
H_MAX = 3

# HistGradientBoosting settings reused from study 1 (scripts/02_aachen_real_data.py)
HGBR_PARAMS = dict(max_depth=4, learning_rate=0.05, max_iter=300, l2_regularization=1.0,
                   random_state=42)


def load_aligned() -> pd.DataFrame:
    p = DERIVED / "stanford_day3_aligned.csv"
    df = pd.read_csv(p, parse_dates=["label_date", "use_date"])
    return df


def pos(x):
    return np.maximum(x, 0)


def pip_inventory(y: np.ndarray, t_pred: np.ndarray, start: int,
                  initial_expiry=(0.0, 0.0), initial_collection=None) -> dict:
    """Line-by-line Python port of pip::compute_prediction_statistics (R/func.R,
    github.com/bnaras/pip commit 6834939, GPL >= 2).

    Arrays are 0-based here; `start` is the 0-based index of pip's 1-based `start`.
    Units arriving on day i are usable on days i, i+1, i+2 (3 days), used oldest first.
    r[:,0] = units left that expire at the end of the next day, r[:,1] = fresher units left.
    Order rule: x[i+3] = floor( max(t_pred[i] - x[i+1] - x[i+2] - r1[i] - r2[i] + 1, 0) ).
    s = shortage (units asked for but not on the shelf), w = expired (wasted) units.
    """
    N = len(y)
    r = np.zeros((N, 2)); x = np.zeros(N + 3); w = np.zeros(N); s = np.zeros(N)
    if initial_collection is None:
        initial_collection = y[start + 1:start + 4]
    x[start:start + 3] = initial_collection
    for i in range(start, N):
        if i == start:
            e1, e2 = initial_expiry
        else:
            e1, e2 = r[i - 1, 0], r[i - 1, 1]
        w[i] = pos(e1 - y[i])
        r[i, 0] = pos(e1 + e2 - y[i] - w[i])
        s[i] = pos(y[i] - e1 - e2 - x[i])
        r[i, 1] = pos(x[i] - pos(y[i] - e1 - e2))
        if i + 3 < N + 3 and not np.isnan(t_pred[i]):
            x[i + 3] = np.floor(pos(t_pred[i] - x[i + 1] - x[i + 2] - r[i, 0] - r[i, 1] + 1))
    return dict(x=x, r=r, w=w, s=s)


def windows_for(idx: np.ndarray) -> np.ndarray:
    """28-day window number for each scored row (0 = first 28 days of the test)."""
    return (idx - (FIRST_ORIGIN + 1)) // WINDOW_DAYS
