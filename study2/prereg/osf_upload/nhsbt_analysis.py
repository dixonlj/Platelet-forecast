#!/usr/bin/env python3
"""
Pre-registered Study 2 analysis: NHSBT monthly blood-product issues,
England, April 2016 - October 2025 (pre-registration v3).

This single script runs the WHOLE pre-registered analysis end to end:
load the sheet -> monthly totals to units per day -> expanding-window
forecasts (seasonal naive, ETS, SARIMA, calendar regression; plus the
red-cell level-shift regression) at 1-3 months -> MAE and secondary metrics
-> circular moving-block bootstrap CIs and paired differences joined by
target month -> DM tests with the HLN correction -> Holm on the three
primary 1-month platelet tests -> the verdict rule (both must agree) and
the 7 units/day practical label -> secondary products and sensitivity
analyses -> output tables and logs.

Modes
  --synthetic-test   Builds a MADE-UP workbook with the same layout, runs the
                     full pipeline on it, then runs unit checks. Never reads
                     the NHSBT file. Outputs are labelled SYNTHETIC.
  --check-structure  Opens the NHSBT snapshot and reports structure only
                     (sheet, column names, row count, first/last month, gaps,
                     hash). No values printed, no forecasts, no errors.
  --nhsbt            The confirmatory run. Guarded, not locked: it refuses to
                     start unless (1) --osf-url begins with https://osf.io/,
                     (2) this script's and inference.py's SHA-256 match
                     FROZEN_CODE.sha256 AND the hashes written in the plan,
                     and (3) the snapshot hash matches. It cannot confirm that
                     the registration exists or was posted first; that is
                     shown by the OSF timestamp preceding the run time in
                     run_manifest.json. Do not use before posting.

Software: Python 3.13.5, statsmodels 0.15.0, numpy 2.5.5, scipy 1.18.1,
openpyxl 3.1.5. Random seed: 20261118 (inference.SEED).
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import hashlib
import json
import platform
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

HERE = Path(__file__).resolve().parent
STUDY2 = HERE.parent
NHSBT_SNAPSHOT = STUDY2 / "data/public/NHSBT_issues_2016-2025_snapshot_2026-11-18.xlsx"
NHSBT_SHA256 = "f0e3fbc52250d210bfa5bbf655063759b079cb6eebbe0ccee75326c0eab4e696"
NHSBT_OUT = STUDY2 / "results/nhsbt_confirmatory"
STRUCTURE_LOG = STUDY2 / "results/nhsbt_structure_check/check_structure_log.txt"
# Expected code hashes live OUTSIDE the scripts (no self-hashing loop):
#   FROZEN_CODE.sha256  - small manifest, sha256sum format, read by the code
#   PLAN_FILE           - the pre-registration; its hashes must agree too
FROZEN_MANIFEST = HERE / "FROZEN_CODE.sha256"
PLAN_FILE = HERE / "osf_prereg_study2_draft_v3.md"
FROZEN_FILES = ("nhsbt_analysis.py", "inference.py")
SYNTH_OUT = HERE / "synthetic_test_output"

SHEET = "Blood Products Issued by Month"
PRODUCTS = {  # key -> column header in the sheet
    "platelets": "Platelets",
    "red_cells": "Red Blood Cells",
    "ffp": "Fresh Frozen Plasma",
    "cryo": "Cryoprecipitate",
}
PRIMARY_PRODUCT = "platelets"
START, END, N_MONTHS = (2016, 4), (2025, 10), 115
FIRST_ORIGIN = (2022, 10)          # first training window ends Oct 2022
HORIZONS = (1, 2, 3)
COVID_START, COVID_END = (2020, 3), (2021, 12)
SEP_OCT_2025 = {(2025, 9), (2025, 10)}
RBC_SHIFT_FROM = (2024, 4)         # level-shift indicator = 1 from Apr 2024
RBC_SHIFT_MIN_LAST_TRAIN = (2024, 7)  # shift used only if training includes Jul 2024+
CONFIRMATORY_METHODS = ("ets", "sarima", "regression")
SARIMA_UNRELIABLE_SHARE = 0.5   # fallback share above this -> unreliable
OMITTED_UNRELIABLE_SHARE = 0.5  # share of origins omitted (failed fits) above this -> unreliable


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------

def days_in(ym) -> int:
    return calendar.monthrange(ym[0], ym[1])[1]


def next_month(ym):
    y, m = ym
    return (y + 1, 1) if m == 12 else (y, m + 1)


def month_range(start, n):
    out, ym = [], start
    for _ in range(n):
        out.append(ym)
        ym = next_month(ym)
    return out


def in_covid(ym) -> bool:
    return COVID_START <= ym <= COVID_END


def fmt(ym) -> str:
    return f"{ym[0]:04d}-{ym[1]:02d}"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def read_sheet(path: Path):
    """
    Read the 'Blood Products Issued by Month' sheet.
    Layout: a title row, a blank row, a header row starting 'Month', then one
    row per month (first cell a date) until the first empty first cell.
    Returns (months, {product_key: np.array of monthly totals}, header).
    Raises ValueError on any structural problem (missing columns, gaps,
    non-numeric or non-positive values, wrong span).
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if SHEET not in wb.sheetnames:
        raise ValueError(f"sheet {SHEET!r} not found; sheets are {wb.sheetnames}")
    rows = list(wb[SHEET].iter_rows(values_only=True))
    wb.close()
    hdr_i = next((i for i, r in enumerate(rows) if r and r[0] == "Month"), None)
    if hdr_i is None:
        raise ValueError("no header row starting with 'Month'")
    header = [c for c in rows[hdr_i] if c is not None]
    col = {}
    for key, name in PRODUCTS.items():
        if name not in rows[hdr_i]:
            raise ValueError(f"column {name!r} missing; header is {header}")
        col[key] = list(rows[hdr_i]).index(name)
    months, totals = [], {k: [] for k in PRODUCTS}
    for r in rows[hdr_i + 1:]:
        if r is None or r[0] is None:
            break
        d = r[0]
        if not isinstance(d, (dt.datetime, dt.date)):
            raise ValueError(f"non-date month cell {d!r}")
        months.append((d.year, d.month))
        for k, j in col.items():
            v = r[j]
            if not isinstance(v, (int, float)) or not np.isfinite(v) or v <= 0:
                raise ValueError(f"bad value for {k} in {fmt(months[-1])}")
            totals[k].append(float(v))
    expected = month_range(START, N_MONTHS)
    if months != expected:
        gaps = [fmt(a) for a, b in zip(months, months[1:]) if next_month(a) != b]
        raise ValueError(
            f"month sequence is not {fmt(START)}..{fmt(END)} ({N_MONTHS} months, no gaps): "
            f"got {len(months)} months, first {fmt(months[0]) if months else None}, "
            f"last {fmt(months[-1]) if months else None}, breaks after {gaps}"
        )
    return months, {k: np.array(v) for k, v in totals.items()}, header


def to_per_day(months, totals):
    """Monthly total / days in that month (leap Februaries have 29 days)."""
    days = np.array([days_in(ym) for ym in months], dtype=float)
    return np.asarray(totals, dtype=float) / days


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------

def calendar_regression_forecast(train_values, train_pos, train_months, future_pos, future_months, rbc_shift=False):
    """
    OLS of units per day on an intercept, 11 month indicators (Feb..Dec) and
    a linear time trend. The time variable is each month's REAL position in
    the full series (0 = April 2016), in training and forecasting alike, so
    dropping rows (COVID sensitivity) does not renumber time (plan v3,
    COVID rule).
    rbc_shift: add a level-shift indicator (1 from April 2024) only if the
    training window includes July 2024 or later. Returns (preds, used_shift).
    """
    tv = np.asarray(train_values, dtype=float)

    def design(pos, mons):
        mm = np.array([m for (_, m) in mons], dtype=int)
        cols = [np.ones(len(pos)), *[(mm == k).astype(float) for k in range(2, 13)], np.asarray(pos, dtype=float)]
        return cols

    use_shift = bool(rbc_shift and train_months[-1] >= RBC_SHIFT_MIN_LAST_TRAIN)
    Xc = design(train_pos, train_months)
    Fc = design(future_pos, future_months)
    if use_shift:
        Xc.append(np.array([1.0 if ym >= RBC_SHIFT_FROM else 0.0 for ym in train_months]))
        Fc.append(np.array([1.0 if ym >= RBC_SHIFT_FROM else 0.0 for ym in future_months]))
    X, F = np.column_stack(Xc), np.column_stack(Fc)
    beta, *_ = np.linalg.lstsq(X, tv, rcond=None)
    return F @ beta, use_shift


def covid_naive(months, values, origin_i, target_i):
    """Most recent same calendar month outside the COVID window, known at the origin."""
    ty, tm = months[target_i]
    pos = {ym: i for i, ym in enumerate(months)}
    for back in range(1, 30):
        cand = (ty - back, tm)
        ci = pos.get(cand)
        if ci is None:
            break
        if ci <= origin_i and not in_covid(cand):
            return float(values[ci])
    return float("nan")


def run_forecasts(months, values, product, covid_missing=False):
    """
    Expanding-window forecasts. At each origin (end of month t, Oct 2022 ..
    Sep 2025) every model is fitted ONCE on data up to t and forecasts t+1..t+3.
    Returns:
      fc[method][h] = {target_month: forecast_per_day}
      fit_rows: one row per (method, origin) with the spec used / omitted
      log_rows: every captured warning or failure, with origin and method
    """
    n = len(values)
    o0 = months.index(FIRST_ORIGIN)
    methods = ["naive", "ets", "sarima", "regression"] + (["regression_shift"] if product == "red_cells" else [])
    fc = {m: {h: {} for h in HORIZONS} for m in methods}
    fit_rows, log_rows = [], []
    for origin in range(o0, n - 1):
        train = values[: origin + 1]
        tmonths = months[: origin + 1]
        targets = [(h, origin + h) for h in HORIZONS if origin + h < n]
        maxh = max(h for h, _ in targets)
        o_lab = fmt(months[origin])

        # Seasonal naive
        for h, ti in targets:
            yhat = covid_naive(months, values, origin, ti) if covid_missing else inf.seasonal_naive_forecast(train, h)
            fc["naive"][h][months[ti]] = yhat

        # ETS and SARIMA
        if covid_missing:
            tr_mis = np.array([np.nan if in_covid(ym) else v for v, ym in zip(train, tmonths)])
            ets_fc, ets_logs = inf.fit_ets_statespace_missing(tr_mis, maxh)
            ets_spec = "ets_statespace"
            sar_fc, sar_lab, _spec, sar_logs = inf.fit_sarima_on_array(tr_mis, maxh)
        else:
            ets_fc, ets_logs = inf.fit_ets_primary(train, maxh)
            ets_spec = "ets_holtwinters"
            sar_fc, sar_lab, _spec, sar_logs = inf.fit_sarima_primary(train, maxh)
        for method, f, logs, lab in (
            ("ets", ets_fc, ets_logs, ets_spec if ets_fc is not None else "omitted"),
            ("sarima", sar_fc, sar_logs, sar_lab if sar_fc is not None else "omitted"),
        ):
            fit_rows.append({"method": method, "origin": o_lab, "spec_used": lab})
            for l in logs:
                log_rows.append({"method": method, "origin": o_lab, **l})
            if f is not None:
                for h, ti in targets:
                    fc[method][h][months[ti]] = float(f[h - 1])

        # Calendar regression (real time index; COVID rows dropped in the sensitivity)
        keep = [i for i in range(origin + 1) if not (covid_missing and in_covid(months[i]))]
        fut_pos = [ti for _, ti in targets]
        fut_m = [months[ti] for ti in fut_pos]
        variants = [("regression", False)] + ([("regression_shift", True)] if product == "red_cells" else [])
        for name, shift in variants:
            preds, used = calendar_regression_forecast(
                train[keep], keep, [months[i] for i in keep], fut_pos, fut_m, rbc_shift=shift
            )
            fit_rows.append({"method": name, "origin": o_lab, "spec_used": "with_shift" if used else "no_shift"})
            for (h, ti), p in zip(targets, preds):
                fc[name][h][months[ti]] = float(p)
    return fc, fit_rows, log_rows


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def scoring_sets(product, run):
    """Pre-specified target-month subsets. None = all test targets."""
    sets = {"all": None}
    if run == "primary":
        sets["drop_sep_oct_2025"] = lambda ym: ym not in SEP_OCT_2025
        if product == "red_cells":
            sets["rbc_from_2024_04"] = lambda ym: ym >= RBC_SHIFT_FROM
            sets["rbc_before_2024_04"] = lambda ym: ym < RBC_SHIFT_FROM
    return sets


def evaluate(months, per_day, fc, product, run):
    """Accuracy rows and comparison rows (method vs seasonal naive), keyed by target month."""
    actuals = dict(zip(months, per_day))
    acc, comp = [], []
    for set_name, pred in scoring_sets(product, run).items():
        for h in HORIZONS:
            for method, by_h in fc.items():
                f = by_h[h]
                targets = None if pred is None else [ym for ym in f if pred(ym)]
                if pred is not None and not targets:
                    continue
                keep, y, yhat = inf.single_errors(f, actuals, targets)
                m, lo, hi, nn = inf.mae_ci_keyed(f, actuals, h, targets)
                days = np.array([days_in(ym) for ym in keep], dtype=float)
                acc.append({
                    "run": run, "product": product, "scoring_set": set_name, "horizon": h, "method": method,
                    "n": nn, "first_target": fmt(keep[0]) if keep else "", "last_target": fmt(keep[-1]) if keep else "",
                    "mae_per_day": m, "mae_ci_lo": lo, "mae_ci_hi": hi,
                    "mae_monthly_total": float(np.mean(np.abs(y - yhat) * days)) if nn else float("nan"),
                    "rmse_per_day": float(np.sqrt(np.mean((y - yhat) ** 2))) if nn else float("nan"),
                    "mape_per_day_pct": float(np.mean(np.abs(y - yhat) / y) * 100) if nn else float("nan"),
                    "note": "each method scored on its own forecast months; for like-for-like MAE see comparisons_vs_naive.csv (paired months)",
                })
            for method in fc:
                if method == "naive":
                    continue
                f, g = fc[method][h], fc["naive"][h]
                targets = None if pred is None else [ym for ym in set(f) | set(g) if pred(ym)]
                d, lo, hi, info = inf.mae_diff_ci_keyed(f, g, actuals, h, targets)
                dm = inf.dm_hln_keyed(f, g, actuals, h, targets)
                confirm = (run == "primary" and product == PRIMARY_PRODUCT and set_name == "all"
                           and h == 1 and method in CONFIRMATORY_METHODS)
                comp.append({
                    "run": run, "product": product, "scoring_set": set_name, "horizon": h,
                    "comparison": f"{method} - naive", "method": method,
                    "role": "confirmatory" if confirm else "descriptive",
                    "n_paired": info["n_paired"], "n_dropped": info["n_dropped"],
                    "months_missing_method": ";".join(fmt(x) for x in info["missing_a"]),
                    "months_missing_naive": ";".join(fmt(x) for x in info["missing_b"]),
                    "mae_method_on_paired_months": _paired_mae(f, actuals, targets, g)[0],
                    "mae_naive_on_paired_months": _paired_mae(f, actuals, targets, g)[1],
                    "mae_diff_per_day": d, "diff_ci_lo": lo, "diff_ci_hi": hi,
                    "dm_hln": dm["dm_hln"], "p_value": dm["p_value"], "computable": dm["computable"],
                    "p_holm": "", "holm_reject": "", "verdict": "", "practical": "",
                })
    return acc, comp


def _paired_mae(f, actuals, targets, g):
    """MAE of method and of naive on the same (month-joined) months."""
    _, ea, eb, _ = inf.align_by_target(f, g, actuals, targets)
    if len(ea) == 0:
        return float("nan"), float("nan")
    return float(ea.mean()), float(eb.mean())


def apply_primary_rule(comp):
    """Holm over exactly the three confirmatory rows, then the joint verdict and 7 units/day label."""
    prim = [r for r in comp if r["role"] == "confirmatory"]
    if sorted(r["method"] for r in prim) != sorted(CONFIRMATORY_METHODS):
        raise RuntimeError(f"expected exactly 3 confirmatory comparisons, got {[r['method'] for r in prim]}")
    holm = inf.holm_adjust({r["method"]: (r["p_value"] if r["computable"] else float("nan")) for r in prim})
    for r in prim:
        hr = holm[r["method"]]
        r["p_holm"], r["holm_reject"] = hr["p_holm"], hr["reject"]
        r["verdict"] = inf.primary_verdict(r["mae_diff_per_day"], r["diff_ci_lo"], r["diff_ci_hi"], hr["reject"], r["computable"])
        r["practical"] = inf.practical_label(r["verdict"], r["mae_diff_per_day"], r["diff_ci_lo"], r["diff_ci_hi"])
    for r in comp:
        if r["role"] == "descriptive":
            r["verdict"] = inf.descriptive_verdict(r["mae_diff_per_day"], r["diff_ci_lo"], r["diff_ci_hi"], r["p_value"], r["computable"])
    return prim, holm


def lag2_check(months, per_day, fc):
    """N10: descriptive DM at 1 month with 2 Bartlett lags (primary platelet run)."""
    actuals = dict(zip(months, per_day))
    rows = []
    for method in CONFIRMATORY_METHODS:
        for lags in (0, 2):
            out = inf.dm_hln_keyed(fc[method][1], fc["naive"][1], actuals, 1, lags=lags)
            rows.append({"comparison": f"{method} - naive", "horizon": 1, "nw_lags": lags,
                         "n": out["n"], "dm_hln": out["dm_hln"], "p_value": out["p_value"],
                         "role": "confirmatory input" if lags == 0 else "descriptive check only"})
    return rows


def naive_2021_vs_2019(months, per_day):
    """Seasonal-naive inputs for Nov/Dec 2022 in the primary run (2021) and COVID sensitivity (2019)."""
    pos = {ym: i for i, ym in enumerate(months)}
    rows = []
    for ym in ((2022, 11), (2022, 12)):
        rows.append({"target": fmt(ym), "naive_primary_uses": fmt((ym[0] - 1, ym[1])),
                     "naive_primary_per_day": per_day[pos[(ym[0] - 1, ym[1])]],
                     "naive_sensitivity_uses": fmt((ym[0] - 3, ym[1])),
                     "naive_sensitivity_per_day": per_day[pos[(ym[0] - 3, ym[1])]],
                     "actual_per_day": per_day[pos[ym]]})
    return rows


def summarise_fits(fit_rows, run, product):
    out = []
    by = {}
    for r in fit_rows:
        by.setdefault(r["method"], []).append(r["spec_used"])
    for method, specs in by.items():
        n = len(specs)
        row = {"run": run, "product": product, "method": method, "n_origins": n}
        for s in sorted(set(specs)):
            row[f"n_{s}"] = specs.count(s)
        reasons = []
        if method in ("ets", "sarima"):
            omit = specs.count("omitted") / n if n else float("nan")
            row["omitted_share"] = omit
            if omit > OMITTED_UNRELIABLE_SHARE:
                reasons.append("more than half of origins omitted (fit failed)")
        if method == "sarima":
            share = specs.count("fallback") / n if n else float("nan")
            row["fallback_share"] = share
            if share > SARIMA_UNRELIABLE_SHARE:
                reasons.append("more than half of origins used the fallback")
        row["reliability"] = ("treat as unreliable (" + "; ".join(reasons) + ")") if reasons else "ok"
        out.append(row)
    return out


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in keys})


def run_pipeline(xlsx: Path, out: Path, label: str, input_sha: str):
    """The whole pre-registered analysis. `label` is 'SYNTHETIC' or 'NHSBT'."""
    out.mkdir(parents=True, exist_ok=True)
    months, totals, header = read_sheet(xlsx)
    per_day = {k: to_per_day(months, v) for k, v in totals.items()}
    all_fc, long_rows, acc, comp, fits, logs = {}, [], [], [], [], []
    for run, covid in (("primary", False), ("covid_sensitivity", True)):
        for product in PRODUCTS:
            fc, fit_rows, log_rows = run_forecasts(months, per_day[product], product, covid_missing=covid)
            all_fc[(run, product)] = fc
            fits += summarise_fits(fit_rows, run, product)
            logs += [{"run": run, "product": product, **l} for l in log_rows]
            pos = {ym: i for i, ym in enumerate(months)}
            for method, by_h in fc.items():
                for h, d in by_h.items():
                    for ym, v in sorted(d.items()):
                        i = pos[ym]
                        long_rows.append({"run": run, "product": product, "method": method, "horizon": h,
                                          "origin": fmt(months[i - h]), "target": fmt(ym),
                                          "actual_per_day": per_day[product][i], "forecast_per_day": v,
                                          "days_in_month": days_in(ym), "actual_total": totals[product][i],
                                          "forecast_total": v * days_in(ym)})
            a, c = evaluate(months, per_day[product], fc, product, run)
            acc += a
            comp += c
    rel = {(f["run"], f["product"], f["method"]): f["reliability"] for f in fits}
    for r in comp:
        r["method_reliability"] = rel.get((r["run"], r["product"], r["method"]), "ok")
    prim, holm = apply_primary_rule(comp)
    lag2 = lag2_check(months, per_day[PRIMARY_PRODUCT], all_fc[("primary", PRIMARY_PRODUCT)])
    nv = naive_2021_vs_2019(months, per_day[PRIMARY_PRODUCT])

    tag = "SYNTHETIC_" if label == "SYNTHETIC" else ""
    write_csv(out / f"{tag}forecasts_long.csv", long_rows)
    write_csv(out / f"{tag}accuracy.csv", acc)
    write_csv(out / f"{tag}comparisons_vs_naive.csv", comp)
    write_csv(out / f"{tag}dm_lag2_check.csv", lag2)
    write_csv(out / f"{tag}naive_2021_vs_2019.csv", nv)
    write_csv(out / f"{tag}fit_summary.csv", fits)
    write_csv(out / f"{tag}fit_warning_log.csv", logs or [{"run": "", "product": "", "method": "", "origin": "",
                                                          "spec": "", "category": "", "message": "(no warnings)",
                                                          "counts_as_failure": ""}])
    manifest = {
        "data_label": label,
        "input_file": str(xlsx), "input_sha256": input_sha,
        "months": [fmt(months[0]), fmt(months[-1]), len(months)], "columns": header,
        "seed": inf.SEED, "n_boot": inf.N_BOOT,
        "python": platform.python_version(),
        "software": _versions(),
        "script_sha256": {"nhsbt_analysis.py": sha256_of(Path(__file__)), "inference.py": sha256_of(Path(inf.__file__))},
        "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    (out / f"{tag}run_manifest.json").write_text(json.dumps(manifest, indent=2))
    lines = [f"# Primary result ({label})", ""]
    if label == "SYNTHETIC":
        lines += ["**MADE-UP DATA. These numbers are a code test, not a result about NHSBT or any blood service.**", ""]
    lines += ["Platelet units per day, 1 month ahead, method minus seasonal naive (negative = method had lower MAE).",
              "Holm over these three tests at 5%; 'better' needs Holm rejection AND a 95% circular block-bootstrap",
              "interval that excludes zero. Smallest meaningful difference: 7 units/day.", "",
              "| Comparison | n | MAE diff | 95% CI | HLN-DM p | Holm p | Verdict | Practical | Fit reliability |", "|---|---|---|---|---|---|---|---|---|"]
    for r in prim:
        lines.append(f"| {r['comparison']} | {r['n_paired']} | {r['mae_diff_per_day']:.2f} | "
                     f"{r['diff_ci_lo']:.2f} to {r['diff_ci_hi']:.2f} | {r['p_value']:.4f} | {r['p_holm']:.4f} | "
                     f"{r['verdict']} | {r['practical']} | {r['method_reliability']} |")
    sar = [f for f in fits if f["method"] == "sarima"]
    ets = [f for f in fits if f["method"] == "ets"]
    lines += ["", "SARIMA fallback / omitted share per run and product: " +
              "; ".join(f"{f['run']}/{f['product']} fallback {f['fallback_share']:.2f}, omitted {f['omitted_share']:.2f} ({f['reliability']})" for f in sar),
              "", "ETS omitted share per run and product: " +
              "; ".join(f"{f['run']}/{f['product']} {f['omitted_share']:.2f} ({f['reliability']})" for f in ets),
              "", "Everything else in the output tables is descriptive."]
    (out / f"{tag}primary_result.md").write_text("\n".join(lines) + "\n")
    return {"months": months, "per_day": per_day, "totals": totals, "fc": all_fc,
            "acc": acc, "comp": comp, "prim": prim, "holm": holm, "fits": fits, "logs": logs, "out": out}


def _versions():
    import openpyxl
    import scipy
    import statsmodels
    return {"statsmodels": statsmodels.__version__, "numpy": np.__version__,
            "scipy": scipy.__version__, "openpyxl": openpyxl.__version__}


# ---------------------------------------------------------------------------
# Synthetic workbook (MADE-UP numbers, same layout as the NHSBT sheet)
# ---------------------------------------------------------------------------

def synthetic_totals(seed=inf.SEED):
    """Made-up seasonal monthly TOTALS for four products. Not NHSBT."""
    rng = np.random.default_rng(seed)
    months = month_range(START, N_MONTHS)
    t = np.arange(N_MONTHS)
    mon = np.array([m for _, m in months])
    covid = np.array([in_covid(ym) for ym in months])
    shift = np.array([ym >= RBC_SHIFT_FROM for ym in months])
    base = {
        "platelets": 680 + 0.05 * t + 20 * np.sin(2 * np.pi * mon / 12) + rng.normal(0, 15, N_MONTHS) - 80 * covid,
        "red_cells": 4500 - 2 * t + 120 * np.cos(2 * np.pi * mon / 12) + rng.normal(0, 60, N_MONTHS) - 400 * covid - 150 * shift,
        "ffp": 600 + 15 * np.sin(2 * np.pi * mon / 12) + rng.normal(0, 20, N_MONTHS) - 50 * covid,
        "cryo": 300 + 0.3 * t + 10 * np.sin(2 * np.pi * mon / 12) + rng.normal(0, 12, N_MONTHS) - 20 * covid,
    }
    days = np.array([days_in(ym) for ym in months])
    return months, {k: np.round(v * days * 4) / 4 for k, v in base.items()}


def write_synthetic_workbook(path: Path, months, totals, drop_month=None):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append(["SYNTHETIC TEST DATA - made-up numbers in the NHSBT sheet layout, April 2016 - October 2025"])
    ws.append([])
    ws.append(["Month", "Red Blood Cells", "Platelets", "Fresh Frozen Plasma", "Cryoprecipitate"])
    for i, ym in enumerate(months):
        if drop_month is not None and ym == drop_month:
            continue
        ws.append([dt.datetime(ym[0], ym[1], 1), totals["red_cells"][i], totals["platelets"][i],
                   totals["ffp"][i], totals["cryo"][i]])
    wb.save(path)


# ---------------------------------------------------------------------------
# Synthetic test suite
# ---------------------------------------------------------------------------

class _Checks:
    def __init__(self):
        self.n_ok = 0
        self.failed = []

    def __call__(self, cond, name):
        if cond:
            self.n_ok += 1
            print(f"  PASS  {name}")
        else:
            self.failed.append(name)
            print(f"  FAIL  {name}")


def run_synthetic_test() -> int:
    check = _Checks()
    SYNTH_OUT.mkdir(parents=True, exist_ok=True)
    months_s, totals_s = synthetic_totals()
    xlsx = SYNTH_OUT / "SYNTHETIC_workbook_made_up_numbers.xlsx"
    write_synthetic_workbook(xlsx, months_s, totals_s)
    print("SYNTHETIC TEST: made-up workbook written; the NHSBT snapshot is not opened in this mode.")

    print("[1] Loader")
    months, totals, header = read_sheet(xlsx)
    check(len(months) == 115 and months[0] == (2016, 4) and months[-1] == (2025, 10), "115 months, Apr 2016 - Oct 2025")
    check(all(np.allclose(totals[k], totals_s[k]) for k in PRODUCTS), "values round-trip through the sheet")
    with tempfile.TemporaryDirectory() as td:
        gapped = Path(td) / "gap.xlsx"
        write_synthetic_workbook(gapped, months_s, totals_s, drop_month=(2019, 6))
        try:
            read_sheet(gapped)
            check(False, "loader refuses a sheet with a missing month")
        except ValueError:
            check(True, "loader refuses a sheet with a missing month")

    print("[2] Units per day")
    pdp = to_per_day(months, totals["platelets"])
    i_feb20, i_feb19, i_jan20 = months.index((2020, 2)), months.index((2019, 2)), months.index((2020, 1))
    check(np.isclose(pdp[i_feb20], totals["platelets"][i_feb20] / 29), "Feb 2020 divided by 29 (leap year)")
    check(np.isclose(pdp[i_feb19], totals["platelets"][i_feb19] / 28), "Feb 2019 divided by 28")
    check(np.isclose(pdp[i_jan20], totals["platelets"][i_jan20] / 31), "Jan 2020 divided by 31")

    print("[3] Full pipeline on made-up data (all runs, products, horizons, sensitivities)")
    res = run_pipeline(xlsx, SYNTH_OUT, "SYNTHETIC", sha256_of(xlsx))
    fc = res["fc"][("primary", "platelets")]
    n1, n2, n3 = (len(fc["naive"][h]) for h in HORIZONS)
    check((n1, n2, n3) == (36, 35, 34), f"target counts per horizon 36/35/34 (got {n1}/{n2}/{n3})")
    check(min(fc["naive"][1]) == (2022, 11) and max(fc["naive"][1]) == (2025, 10), "1-month targets Nov 2022 - Oct 2025")
    check(min(fc["naive"][3]) == (2023, 1) and max(fc["naive"][3]) == (2025, 10), "3-month targets Jan 2023 - Oct 2025")
    for name in ("forecasts_long", "accuracy", "comparisons_vs_naive", "dm_lag2_check", "naive_2021_vs_2019",
                 "fit_summary", "fit_warning_log"):
        check((SYNTH_OUT / f"SYNTHETIC_{name}.csv").exists(), f"output SYNTHETIC_{name}.csv written")
    check((SYNTH_OUT / "SYNTHETIC_primary_result.md").exists(), "output SYNTHETIC_primary_result.md written")
    man = json.loads((SYNTH_OUT / "SYNTHETIC_run_manifest.json").read_text())
    check(man["data_label"] == "SYNTHETIC" and "NHSBT_issues" not in man["input_file"], "manifest labelled SYNTHETIC, input is the made-up file")
    prim = res["prim"]
    check(len(prim) == 3 and all(r["p_holm"] != "" and r["verdict"] for r in prim),
          "Holm and the joint verdict were applied to exactly 3 confirmatory rows")
    check(all(r["role"] == "descriptive" for r in res["comp"] if not (r["run"] == "primary" and r["product"] == "platelets"
              and r["scoring_set"] == "all" and r["horizon"] == 1)), "every other comparison is descriptive")
    runs_products = {(r["run"], r["product"]) for r in res["comp"]}
    check(len(runs_products) == 8, "primary + COVID sensitivity for all 4 products")
    sets = {(r["product"], r["scoring_set"]) for r in res["comp"] if r["run"] == "primary"}
    check(("platelets", "drop_sep_oct_2025") in sets and ("red_cells", "rbc_from_2024_04") in sets
          and ("red_cells", "rbc_before_2024_04") in sets, "Sep-Oct 2025 drop and red-cell split/start-Apr-2024 sets present")
    so = [r for r in res["acc"] if r["run"] == "primary" and r["product"] == "platelets"
          and r["scoring_set"] == "drop_sep_oct_2025" and r["horizon"] == 1 and r["method"] == "naive"][0]
    check(so["n"] == 34 and so["last_target"] == "2025-08", "Sep-Oct 2025 sensitivity scores 34 one-month targets ending Aug 2025")
    check(any(r["method"] == "regression_shift" for r in res["comp"] if r["product"] == "red_cells"),
          "red-cell regression is reported both with and without the April 2024 shift")
    acc_keys = set(res["acc"][0])
    check({"mae_monthly_total", "rmse_per_day", "mape_per_day_pct"} <= acc_keys, "secondary metrics computed")

    print("[4] Pairing by target month (N2)")
    actuals = dict(zip(months, pdp))
    ets = dict(fc["ets"][1])
    naive = fc["naive"][1]
    dropped = sorted(ets)[5]
    del ets[dropped]
    keep, ea, eb, info = inf.align_by_target(ets, naive, actuals)
    check(info["n_paired"] == 35 and info["n_dropped"] == 1 and info["missing_a"] == [dropped],
          "dropping one ETS forecast leaves 35 pairs and reports the dropped month")
    check(dropped not in keep and keep == sorted(keep), "kept months are in time order and exclude the dropped month")
    manual = np.mean([abs(actuals[k] - ets[k]) - abs(actuals[k] - naive[k]) for k in keep])
    d, lo, hi, _ = inf.mae_diff_ci_keyed(ets, naive, actuals, 1)
    check(np.isclose(d, manual), "paired MAE difference equals the month-by-month hand calculation")
    pos_wrong = np.mean([abs(actuals[k] - ets[k]) for k in sorted(ets)]) - np.mean([abs(actuals[k] - naive[k]) for k in sorted(naive)[:35]])
    print(f"        (by-month diff {d:.3f}; old position-based diff would have been {pos_wrong:.3f})")
    try:
        inf.block_bootstrap_mae_diff([(1, 1)] * 35, [(1, 1)] * 36, 1)
        check(False, "positional helper refuses unequal-length lists")
    except ValueError:
        check(True, "positional helper refuses unequal-length lists")
    dmk = inf.dm_hln_keyed(ets, naive, actuals, 1)
    check(dmk["n"] == 35 and dmk["pairing"]["n_dropped"] == 1, "DM-HLN uses the same 35 month-matched pairs")

    print("[5] COVID rules")
    fcc = res["fc"][("covid_sensitivity", "platelets")]
    check(np.isclose(fcc["naive"][1][(2022, 11)], pdp[months.index((2019, 11))]), "sensitivity naive for Nov 2022 = Nov 2019")
    check(np.isclose(fcc["naive"][1][(2022, 12)], pdp[months.index((2019, 12))]), "sensitivity naive for Dec 2022 = Dec 2019")
    check(np.isclose(fcc["naive"][1][(2023, 1)], pdp[months.index((2022, 1))]), "sensitivity naive for Jan 2023 = Jan 2022 (outside window)")
    check(np.isclose(fc["naive"][1][(2022, 11)], pdp[months.index((2021, 11))]), "primary naive for Nov 2022 = Nov 2021")
    # Regression time index: noise-free trend + season; dropping COVID rows must still recover it exactly.
    pos_all = np.arange(len(months))
    mon = np.array([m for _, m in months])
    truth = 500 + 0.8 * pos_all + 10 * (mon == 7) - 6 * (mon == 2)
    o = months.index((2022, 10))
    keep_i = [i for i in range(o + 1) if not in_covid(months[i])]
    fut = [o + 1, o + 2, o + 3]
    preds, _ = calendar_regression_forecast(truth[keep_i], keep_i, [months[i] for i in keep_i], fut, [months[i] for i in fut])
    check(np.allclose(preds, truth[fut]), "COVID-dropped regression uses real time positions (exact on a noise-free series)")
    renum = list(range(len(keep_i)))
    bad, _ = calendar_regression_forecast(truth[keep_i], renum, [months[i] for i in keep_i],
                                          [len(keep_i), len(keep_i) + 1, len(keep_i) + 2], [months[i] for i in fut])
    check(not np.allclose(bad, truth[fut]), "renumbered time (the v2 bug) would NOT recover it")

    print("[6] Red-cell April 2024 shift rule")
    def used_shift(last):
        oi = months.index(last)
        tr = list(range(oi + 1))
        _, u = calendar_regression_forecast(pdp[tr], tr, [months[i] for i in tr], [oi + 1], [months[oi + 1]], rbc_shift=True)
        return u
    check(used_shift((2024, 6)) is False, "no shift when training ends June 2024")
    check(used_shift((2024, 7)) is True, "shift used when training includes July 2024")
    rs = [f for f in res["fits"] if f["run"] == "primary" and f["product"] == "red_cells" and f["method"] == "regression_shift"][0]
    rn = [f for f in res["fits"] if f["run"] == "primary" and f["product"] == "red_cells" and f["method"] == "regression"][0]
    exp_shift = len([ym for ym in month_range((2022, 10), 36) if ym >= (2024, 7)])
    check(rs.get("n_with_shift", 0) == exp_shift and rn.get("n_with_shift", 0) == 0,
          f"shift used at exactly the {exp_shift} origins from July 2024; never in the no-shift variant")

    print("[7] Holm, verdict and 7 units/day label")
    h = inf.holm_adjust({"a": 0.01, "b": 0.02, "c": 0.04})
    check(all(h[k]["reject"] for k in "abc") and np.allclose([h[k]["p_holm"] for k in "abc"], [0.03, 0.04, 0.04]),
          "Holm (0.01, 0.02, 0.04): all rejected, adjusted 0.03/0.04/0.04")
    h = inf.holm_adjust({"a": 0.01, "b": 0.03, "c": 0.04})
    check(h["a"]["reject"] and not h["b"]["reject"] and not h["c"]["reject"], "Holm (0.01, 0.03, 0.04): only the first rejected")
    h = inf.holm_adjust({"a": float("nan"), "b": 0.001, "c": 0.5})
    check(not h["a"]["reject"] and h["a"]["p_holm"] == 1.0 and h["b"]["reject"], "non-computable p is treated as 1, never rejected")
    v = inf.primary_verdict(-10, -15, -8, True, True)
    check(v.startswith("lower MAE"), "both agree, interval below zero -> lower MAE")
    check(inf.primary_verdict(-10, -15, -8, False, True).startswith("couldn't"), "Holm not rejected -> couldn't tell apart")
    check(inf.primary_verdict(-10, -15, 2, True, True).startswith("couldn't"), "interval includes 0 -> couldn't tell apart")
    check(inf.primary_verdict(-10, -15, -8, True, False).startswith("couldn't"), "test not computable -> couldn't tell apart")
    check(inf.primary_verdict(9, 3, 12, True, True).startswith("higher MAE"), "both agree, interval above zero -> naive better")
    check(inf.practical_label(v, -10, -15, -8).startswith("practically meaningful"), "diff -10, CI -15 to -8 -> practically meaningful")
    check(inf.practical_label(v, -10, -15, -4).startswith("meets 7"), "diff -10, CI includes -4 -> may be smaller than what matters")
    check(inf.practical_label(v, -3, -5, -1).startswith("below the 7"), "diff -3 -> below the smallest meaningful difference")
    check(inf.practical_label("couldn't tell them apart", -10, -15, 1) == "no claim", "no verdict -> no practical claim")
    vw = inf.primary_verdict(10, 8, 15, True, True)
    check(inf.practical_label(vw, 10, 8, 15).startswith("practically meaningful"),
          "naive better by 10, CI 8 to 15 -> 'worse, practically meaningful'")
    check(inf.practical_label(vw, 10, 4, 15).startswith("meets 7"), "naive better by 10, CI 4 to 15 -> may be smaller than what matters")

    print("[8] Fit failure rule and fallback")
    real_sarimax = inf.SARIMAX

    class _FailPrimary:
        def __init__(self, endog, order, seasonal_order, trend=None, **kw):
            if order == (0, 1, 1):
                raise RuntimeError("forced failure for test")
            self._m = real_sarimax(endog, order=order, seasonal_order=seasonal_order, trend=trend, **kw)

        def fit(self, **kw):
            return self._m.fit(**kw)

    class _FakeFit:
        def __init__(self, conv, warn):
            self.mle_retvals = {"converged": conv}
            self._warn = warn

        def forecast(self, h):
            if self._warn:
                warnings.warn("Maximum Likelihood optimization failed to converge.", inf.ConvergenceWarning)
            return np.ones(h)

    class _FakeModel:
        conv, warn = False, False

        def __init__(self, *a, **k):
            pass

        def fit(self, **k):
            return _FakeFit(type(self).conv, type(self).warn)

    train = pdp[: months.index((2022, 10)) + 1]
    try:
        inf.SARIMAX = _FailPrimary
        f, lab, spec, logs = inf.fit_sarima_primary(train, 3)
        check(lab == "fallback" and spec[2] == "c" and f is not None, "forced primary failure -> fallback with constant")
        check(any(l["category"] == "Exception" and "forced failure" in l["message"] for l in logs), "the failure is kept in the log")
        inf.SARIMAX = type("M", (_FakeModel,), {"conv": False, "warn": False})
        f, lab, _, logs = inf.fit_sarima_primary(train, 3)
        check(lab == "failed" and any(l["message"] == "converged=False" for l in logs), "mle_retvals['converged'] False -> failure")
        inf.SARIMAX = type("M", (_FakeModel,), {"conv": True, "warn": True})
        f, lab, _, logs = inf.fit_sarima_primary(train, 3)
        check(lab == "failed" and any(l["category"] == "ConvergenceWarning" for l in logs), "ConvergenceWarning -> failure, warning logged")
        inf.SARIMAX = type("M", (_FakeModel,), {"conv": True, "warn": False})
        f, lab, _, logs = inf.fit_sarima_primary(train, 3)
        check(lab == "primary" and f is not None, "converged, no warnings -> primary kept")
    finally:
        inf.SARIMAX = real_sarimax
    check(inf.warning_is_failure(UserWarning, "Optimization failed to optimize") and
          not inf.warning_is_failure(UserWarning, "frequency not set"), "warning rule (c) 'failed to'+'optim' and a harmless warning")
    sar = [f for f in res["fits"] if f["method"] == "sarima"]
    check(all(f["n_origins"] == 36 for f in sar), "SARIMA fallback counted per origin (36 origins per run/product)")
    check(all("fallback_share" in f and "omitted_share" in f and "reliability" in f for f in sar),
          "SARIMA fallback share, omitted share and >50% reliability label reported")
    print("        SARIMA fallback shares: " + ", ".join(f"{f['run']}/{f['product']}={f['fallback_share']:.2f}" for f in sar))

    print("[9] Circular block bootstrap")
    rng = np.random.default_rng(1)
    idx = inf.circular_block_indices(10, 5, 20000, rng)
    counts = np.bincount(idx.ravel(), minlength=10) / idx.size
    check(np.all(np.abs(counts - 0.1) < 0.005), "every month equally likely (n=10, block 5)")
    m1 = inf.bootstrap_mean_ci(np.arange(36.0), 1)
    m2 = inf.bootstrap_mean_ci(np.arange(36.0), 1)
    check(m1 == m2, "seeded bootstrap is reproducible")

    print("[10] NHSBT guard")
    check(_osf_url_ok(None) is False and _osf_url_ok("https://example.com/x") is False and _osf_url_ok("https://osf.io/abcd1"),
          "--nhsbt refuses without an https://osf.io/ registration URL")
    try:
        got = verify_frozen_code()
        check(True, "frozen-code check: both scripts match FROZEN_CODE.sha256 and the plan")
    except SystemExit as e:
        check(False, f"frozen-code check: both scripts match FROZEN_CODE.sha256 and the plan ({e})")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for n in FROZEN_FILES:
            (td / n).write_bytes((HERE / n).read_bytes())
        (td / "inference.py").write_bytes((HERE / "inference.py").read_bytes() + b"\n# edited\n")
        try:
            verify_frozen_code(code_dir=td)
            check(False, "an edited inference.py is refused (hash mismatch stop)")
        except SystemExit as e:
            check("inference.py" in str(e) and "manifest" in str(e) and "plan" in str(e),
                  "an edited inference.py is refused (hash mismatch stop)")
        bad_manifest = td / "bad.sha256"
        bad_manifest.write_text("0" * 64 + "  nhsbt_analysis.py\n" + "0" * 64 + "  inference.py\n")
        try:
            verify_frozen_code(manifest=bad_manifest)
            check(False, "a manifest that disagrees with the code is refused")
        except SystemExit:
            check(True, "a manifest that disagrees with the code is refused")
        try:
            verify_snapshot(xlsx, expected="0" * 64)
            check(False, "snapshot hash mismatch stops the run")
        except SystemExit:
            check(True, "snapshot hash mismatch stops the run")

    print("[11] Unreliable rule for omitted fits (ETS and SARIMA)")
    fake = [{"method": "ets", "spec_used": "omitted" if i < 19 else "ets_holtwinters"} for i in range(36)]
    fake += [{"method": "sarima", "spec_used": "omitted" if i < 18 else "primary"} for i in range(36)]
    sf = {f["method"]: f for f in summarise_fits(fake, "x", "y")}
    check(sf["ets"]["reliability"].startswith("treat as unreliable") and np.isclose(sf["ets"]["omitted_share"], 19 / 36),
          "ETS omitted at 19 of 36 origins -> unreliable")
    check(sf["sarima"]["reliability"] == "ok", "exactly half omitted (18 of 36) -> not labelled unreliable")
    for f in res["fits"]:
        if f["method"] == "ets":
            exp = f["omitted_share"] > 0.5
            if exp != f["reliability"].startswith("treat as unreliable"):
                check(False, f"pipeline ETS label consistent for {f['run']}/{f['product']}")
                break
    else:
        check(True, "pipeline ETS reliability label matches the omitted share for every run/product")
    print("        ETS omitted shares: " + ", ".join(f"{f['run']}/{f['product']}={f['omitted_share']:.2f}"
                                                 for f in res["fits"] if f["method"] == "ets"))
    rc = [f for f in res["fits"] if f["run"] == "covid_sensitivity" and f["product"] == "red_cells" and f["method"] == "ets"][0]
    rcc = [r for r in res["comp"] if r["run"] == "covid_sensitivity" and r["product"] == "red_cells" and r["method"] == "ets"]
    check(rc["omitted_share"] > 0.5 and all(r["method_reliability"].startswith("treat as unreliable") for r in rcc),
          "made-up red-cell COVID-sensitivity ETS (most origins omitted) is labelled unreliable in every comparison row")
    check(all("method_reliability" in r for r in res["comp"]), "every comparison row carries the method's reliability label")
    check(all("n_paired" in r and "mae_method_on_paired_months" in r for r in res["comp"]),
          "every comparison row shows n_paired and paired-month MAEs")

    print("[12] ETS failure at one origin omits all its horizons")
    real_ets = inf.fit_ets_primary
    fail_len = months.index((2023, 6)) + 1
    def _ets_fail_once(train, horizon):
        if len(train) == fail_len:
            return None, [{"spec": "ets_holtwinters", "category": "Exception", "message": "forced", "counts_as_failure": True}]
        return real_ets(train, horizon)
    try:
        inf.fit_ets_primary = _ets_fail_once
        fx, frows, lrows = run_forecasts(months, pdp, "platelets", covid_missing=False)
    finally:
        inf.fit_ets_primary = real_ets
    lost = {(2023, 7), (2023, 8), (2023, 9)}
    check(all((2023, 6 + h) not in fx["ets"][h] for h in HORIZONS) and all((2023, 6 + h) in fx["naive"][h] for h in HORIZONS),
          "origin Jun 2023 failed -> ETS has no Jul/Aug/Sep 2023 forecast from it at h=1/2/3; naive still does")
    check(len(fx["ets"][1]) == 35 and len(fx["ets"][2]) == 34 and len(fx["ets"][3]) == 33, "ETS counts drop by one at each horizon")
    check(sum(1 for r in frows if r["method"] == "ets" and r["spec_used"] == "omitted") == 1 and
          any(r["message"] == "forced" for r in lrows), "the omitted origin is counted once and logged")
    _ = lost
    act = dict(zip(months, pdp))
    _, _, _, info = inf.mae_diff_ci_keyed(fx["ets"][2], fx["naive"][2], act, 2)
    check(info["n_paired"] == 34 and info["missing_a"] == [(2023, 8)], "h=2 comparison pairs 34 months and reports Aug 2023 dropped")

    print(f"\nSYNTHETIC TEST: {check.n_ok} passed, {len(check.failed)} failed. NHSBT file was not read.")
    if check.failed:
        print("Failed checks: " + "; ".join(check.failed))
        return 1
    return 0


# ---------------------------------------------------------------------------
# NHSBT structure check and confirmatory run
# ---------------------------------------------------------------------------

def _osf_url_ok(url) -> bool:
    return isinstance(url, str) and url.startswith("https://osf.io/") and len(url) > len("https://osf.io/")


def read_frozen_manifest(path: Path = FROZEN_MANIFEST) -> dict:
    """Parse 'sha256  filename' lines (sha256sum format). Returns {filename: sha}."""
    out = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sha, name = line.split(None, 1)
        out[name.strip().lstrip("*")] = sha.lower()
    return out


def read_plan_hashes(path: Path = PLAN_FILE) -> dict:
    """Find '`study2/prereg/<file>` (SHA-256 `<hex>`)' for each frozen file in the plan text."""
    import re
    text = Path(path).read_text()
    out = {}
    for name in FROZEN_FILES:
        m = re.search(r"`study2/prereg/" + re.escape(name) + r"`\s*\(SHA-256 `([0-9a-f]{64})`\)", text)
        if m:
            out[name] = m.group(1)
    return out


def verify_frozen_code(code_dir: Path = HERE, manifest: Path = FROZEN_MANIFEST, plan: Path = PLAN_FILE):
    """
    Stop (SystemExit) unless the actual SHA-256 of nhsbt_analysis.py and
    inference.py equal BOTH the manifest and the plan. The expected values
    are read from those two files, never written inside the scripts, so
    there is no self-hashing loop. Returns {filename: sha} on success.
    """
    want_m = read_frozen_manifest(manifest)
    want_p = read_plan_hashes(plan)
    got = {n: sha256_of(Path(code_dir) / n) for n in FROZEN_FILES}
    problems = []
    for n in FROZEN_FILES:
        if want_m.get(n) != got[n]:
            problems.append(f"{n}: actual {got[n]} != manifest {want_m.get(n)}")
        if want_p.get(n) != got[n]:
            problems.append(f"{n}: actual {got[n]} != plan {want_p.get(n)}")
    if problems:
        raise SystemExit("Refusing: code is not the pre-registered frozen code. " + " | ".join(problems))
    return got


def verify_snapshot(path: Path = NHSBT_SNAPSHOT, expected: str = NHSBT_SHA256) -> str:
    sha = sha256_of(path)
    if sha != expected:
        raise SystemExit(f"Snapshot hash {sha} does not match the pre-registered {expected}. Stopping.")
    return sha


def check_structure(log_path: Path = STRUCTURE_LOG) -> int:
    """Structure only: no values printed, no forecasts, no errors. Output also saved to log_path."""
    sha = sha256_of(NHSBT_SNAPSHOT)
    months, totals, header = read_sheet(NHSBT_SNAPSHOT)
    lines = [
        f"--check-structure run at {dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"script SHA-256 nhsbt_analysis.py {sha256_of(Path(__file__))}; inference.py {sha256_of(Path(inf.__file__))}",
        f"snapshot {NHSBT_SNAPSHOT.name} SHA-256 {sha} ({'matches' if sha == NHSBT_SHA256 else 'DOES NOT MATCH'} the plan)",
        f"sheet {SHEET!r}; columns {header}",
        f"{len(months)} months, first {fmt(months[0])}, last {fmt(months[-1])}, no gaps; "
        f"all {len(PRODUCTS)} product columns numeric and positive",
        "No data values were printed or saved. No forecasts, errors or tests were computed. "
        "(Values were read only to check that each cell is a positive number.)",
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"(saved to {log_path})")
    return 0 if sha == NHSBT_SHA256 else 1


def run_nhsbt(osf_url) -> int:
    if not _osf_url_ok(osf_url):
        raise SystemExit("Refusing: --nhsbt needs --osf-url https://osf.io/<id> of the POSTED pre-registration. "
                         f"The snapshot at {NHSBT_SNAPSHOT} was not opened.")
    code = verify_frozen_code()
    sha = verify_snapshot()
    res = run_pipeline(NHSBT_SNAPSHOT, NHSBT_OUT, "NHSBT", sha)
    man = res["out"] / "run_manifest.json"
    m = json.loads(man.read_text())
    m["osf_registration"] = osf_url
    m["frozen_code_verified"] = code
    man.write_text(json.dumps(m, indent=2))
    print(f"Done. Outputs in {NHSBT_OUT}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Study 2 NHSBT pre-registered analysis")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--synthetic-test", action="store_true", help="full pipeline + checks on made-up data only")
    g.add_argument("--check-structure", action="store_true", help="NHSBT sheet structure only; no values, no models")
    g.add_argument("--nhsbt", action="store_true", help="confirmatory run; locked until the plan is posted")
    p.add_argument("--osf-url", default=None, help="https://osf.io/... URL of the posted registration (required with --nhsbt)")
    a = p.parse_args()
    if a.synthetic_test:
        sys.exit(run_synthetic_test())
    if a.check_structure:
        sys.exit(check_structure())
    sys.exit(run_nhsbt(a.osf_url))


if __name__ == "__main__":
    main()
