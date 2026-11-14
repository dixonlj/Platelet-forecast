#!/usr/bin/env python3
"""
Milestone 4, step 2b: a public pretrained time-series model (Amazon Chronos-Bolt).

Zero-shot, CPU only, using amazon/chronos-bolt-small through the
chronos-forecasting package. We do not fine-tune, do not upload any data,
and do not sign in to Hugging Face. If the install or download fails or
takes too long, this script records the skip and exits cleanly.

Compared on 2017 and 2018 against the original gradient boosting model and
the 4-week weekday average: average miss per day, plus the realistic
simulation with Chronos's own high/typical bands as the safety-stock unit.

Educational / advisory only. Never clinical. Public Aachen data only.

Run:  PYTHONPATH=scripts .venv/bin/python scripts/05b_pretrained_model.py
"""

from __future__ import annotations

import os
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import lib_m4 as L

RESULTS = L.RESULTS_DIR
CHARTS = L.CHART_DIR
MODEL_ID = "amazon/chronos-bolt-small"
# Hard cap: skip rather than hang. Covers download + all zero-shot forecasts.
TIME_BUDGET_SEC = 12 * 60
CONTEXT_LEN = 512  # daily history shown to the model (fast, and longer than a year)
BATCH = 64
PRED_LEN = 4
# Quantile levels Chronos-Bolt was trained on include 0.1, 0.5, 0.9.
Q_LEVELS = [0.5, 0.9]


def _skip(reason: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    text = (
        "Chronos-Bolt comparison was skipped.\n\n"
        f"Reason: {reason}\n\n"
        "The rest of milestone 4 still uses scikit-learn gradient boosting "
        "and the four simple baselines. No Aachen data was uploaded anywhere.\n"
    )
    (RESULTS / "05b_skipped.txt").write_text(text)
    print(text)
    L.log_trackio("05b_pretrained_model", {"skipped": 1}, {"reason": reason[:200]})


def _forecast_chronos(y: pd.Series, origins: pd.DatetimeIndex, started: float):
    """Zero-shot 1- to 4-day forecasts and 50/90 bands at each origin."""
    import torch
    from chronos import BaseChronosPipeline

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.pop("HF_TOKEN", None)
    os.environ.pop("HUGGING_FACE_HUB_TOKEN", None)
    os.environ.pop("HUGGINGFACE_HUB_TOKEN", None)

    remaining = TIME_BUDGET_SEC - (time.time() - started)
    if remaining < 30:
        raise TimeoutError("time budget already used before model load")

    pipeline = BaseChronosPipeline.from_pretrained(
        MODEL_ID,
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    values = y.astype(float).values
    idx = {d: i for i, d in enumerate(y.index)}
    mean_fc = pd.DataFrame(index=origins, columns=list(range(1, PRED_LEN + 1)), dtype=float)
    q50_fc = mean_fc.copy()
    q90_fc = mean_fc.copy()

    # Only origins with enough history.
    use = [d for d in origins if idx[d] >= 28]
    for start in range(0, len(use), BATCH):
        if time.time() - started > TIME_BUDGET_SEC:
            raise TimeoutError(f"time budget exceeded after {start} of {len(use)} origins")
        batch_days = use[start:start + BATCH]
        contexts = []
        for d in batch_days:
            i = idx[d]
            lo = max(0, i + 1 - CONTEXT_LEN)  # include the origin day
            contexts.append(torch.tensor(values[lo:i + 1], dtype=torch.float32))
        with torch.no_grad():
            quantiles, mean = pipeline.predict_quantiles(
                contexts,
                prediction_length=PRED_LEN,
                quantile_levels=Q_LEVELS,
            )
        # quantiles: (batch, pred_len, n_q); mean: (batch, pred_len)
        q = quantiles.cpu().numpy()
        m = mean.cpu().numpy()
        for bi, d in enumerate(batch_days):
            mean_fc.loc[d, :] = m[bi]
            q50_fc.loc[d, :] = q[bi, :, 0]
            q90_fc.loc[d, :] = q[bi, :, 1]
        if start == 0 or (start // BATCH) % 5 == 0:
            print(f"  Chronos origins {start + len(batch_days)}/{len(use)}",
                  f"elapsed {time.time()-started:.0f}s")
    return mean_fc, q50_fc, q90_fc


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    skip_path = RESULTS / "05b_skipped.txt"
    if skip_path.exists():
        skip_path.unlink()

    started = time.time()
    try:
        import torch  # noqa: F401
        from chronos import BaseChronosPipeline  # noqa: F401
    except Exception as exc:
        _skip(f"could not import torch or chronos-forecasting ({type(exc).__name__}: {exc})")
        return

    df, y, authors = L.load_series()
    # Origins we need: 2016 (for 2017 safety unit) through the 2018 scoring window.
    origins = y.loc["2015-12-31":"2018-12-30"].index
    try:
        mean_fc, q50_fc, q90_fc = _forecast_chronos(y, origins, started)
    except Exception as exc:
        _skip(f"Chronos-Bolt failed or timed out ({type(exc).__name__}: {exc})\n\n"
              + traceback.format_exc())
        return

    # Persist forecasts so a rerun can skip the model if needed.
    out_fc = RESULTS / "05b_chronos_forecasts.csv"
    tmp = mean_fc.add_prefix("mean_h").join(q50_fc.add_prefix("q50_h")).join(q90_fc.add_prefix("q90_h"))
    tmp.to_csv(out_fc)

    feat_old = L.m2.hgbr_feature_table(y)
    base = L.m2.baseline_forecasts(y)

    score_rows = []
    inv_rows = []
    year_matched = {}
    hospitals = {}

    for year in (2017, 2018):
        _, eval_start, eval_end = L.year_window(year)
        hospital = L.hospital_actual(df, eval_start, eval_end)
        hospitals[year] = hospital
        target_sd = hospital["shortage_days"]

        hgbr = L.m2.hgbr_forecasts(feat_old, pd.Timestamp(f"{year - 1}-12-31"))
        hgbr_sigma = L.m2.hgbr_forecasts(feat_old, pd.Timestamp(f"{year - 2}-12-31"))
        point = {"dow4": base["dow4"], "hgbr": hgbr, "chronos": mean_fc}
        scores = L.m2.score_period(y, point, authors,
                                   pd.Timestamp(f"{year}-01-01"),
                                   pd.Timestamp(f"{year + 1}-01-01"))
        for r in scores:
            r["year"] = year
            score_rows.append(r)

        fcs_sigma = {"dow4": base["dow4"], "hgbr": hgbr_sigma, "chronos": mean_fc}
        sigma = L.sigma_for_year(y, fcs_sigma, year)
        sigma["chronos_q"] = sigma["chronos"]

        win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4))
               for k, fc in point.items()}
        win["chronos_q"] = win["chronos"]
        safety_daily = {
            "chronos_q": {
                2: (q90_fc[[1, 2]].sum(axis=1) - q50_fc[[1, 2]].sum(axis=1)).clip(lower=0),
                4: (q90_fc[[1, 2, 3, 4]].sum(axis=1) - q50_fc[[1, 2, 3, 4]].sum(axis=1)).clip(lower=0),
            }
        }
        models = ["dow4", "hgbr", "chronos", "chronos_q"]
        res = L.run_config(L.m3.BASE, y, win, sigma, models,
                           year=year, safety_daily=safety_daily)
        summ, matched, _ = L.matched_table(res, target_sd, models)
        summ["year"] = year
        inv_rows.append(summ)
        year_matched[year] = matched
        print(f"=== {year} ===")
        print(summ.to_string(index=False))

    score_df = pd.DataFrame(score_rows)
    inv_df = pd.concat(inv_rows, ignore_index=True)
    score_df.to_csv(RESULTS / "05b_mae.csv", index=False)
    inv_df.to_csv(RESULTS / "05b_inventory.csv", index=False)
    seed_cols = {f"{yr}_{k}": year_matched[yr][k] for yr in year_matched for k in year_matched[yr]}
    pd.DataFrame(seed_cols).to_csv(RESULTS / "05b_per_seed_waste.csv", index_label="seed")

    # Chart: average miss per day on the two years, Chronos vs the two locals.
    # One idea: did the pretrained model beat our simple average / our GB?
    mae = score_df[score_df["model"].isin(["dow4", "hgbr", "chronos"])]
    # Four bars would be crowded with two years x three models. Show 2018
    # average miss (the year we already studied) plus 2017 Chronos vs 4-week
    # in the footnote, OR show 2017 and 2018 for Chronos vs 4-week only.
    # The brief asks for average miss per day AND the sim. The distinctive
    # question is whether Chronos beats the 4-week average and GB.
    # Use 4 bars of 2018 waste at 31 short days: 4-week, GB, Chronos point+fixed,
    # Chronos + its own bands. Mention 2017 and average-miss in the footnote
    # and the log; put average-miss numbers in the log clearly.
    m = year_matched[2018]
    items = [
        ("Average of the\nlast 4 same weekdays", m["dow4"], L.m2.COLORS["dow4"]),
        ("Our machine learning\n(gradient boosting)", m["hgbr"], L.m2.COLORS["hgbr"]),
        ("Pretrained Chronos-Bolt\n(fixed cushion)", m["chronos"], "#6a3d9a"),
        ("Pretrained Chronos-Bolt\n(its own uncertainty)", m["chronos_q"], "#b15928"),
    ]
    w = {k: float(np.nanmean(m[k])) for k in m}
    best = min(w, key=w.get)
    if best == "hgbr":
        title = ("In 2018, our gradient boosting model still threw away fewer platelets\n"
                 "than a public pretrained Chronos-Bolt model used zero-shot")
    elif best.startswith("chronos"):
        title = ("In 2018, the public pretrained Chronos-Bolt model threw away fewer\n"
                 "platelets than our gradient boosting model, used zero-shot")
    else:
        title = ("In 2018, the 4-week weekday average threw away fewer platelets\n"
                 "than both machine-learning forecasts, including Chronos-Bolt")
    chart = L.simple_bar_chart(
        CHARTS / "m4_pretrained_chronos.png",
        title=title,
        ylabel="Platelets thrown away\n(% of units transfused)",
        items=items,
        footnote=(
            "Aachen hospital, 2018, set to the hospital's 31 short days. "
            "Chronos-Bolt small, used as-is on a CPU, no extra training. "
            "Black lines = 5th to 95th percentile of 30 simulated runs. "
            "Average miss per day is in results/m4/05b_mae.csv. "
            "A learning exercise, not a real result. No data was uploaded."
        ),
        ylim=(0, 20),
        value_fmt="{:.1f}% wasted",
    )

    metrics = {"elapsed_sec": time.time() - started, "skipped": 0}
    for year in (2017, 2018):
        for model in ("dow4", "hgbr", "chronos"):
            row = score_df[(score_df["year"] == year) & (score_df["model"] == model)]
            if len(row):
                metrics[f"{year}_{model}_mae"] = float(row["mae_1d"].iloc[0])
        sub = inv_df[inv_df["year"] == year].set_index("model")
        for model in ("dow4", "hgbr", "chronos", "chronos_q"):
            metrics[f"{year}_{model}_waste"] = float(sub.loc[model, "waste_mean"])
    trackio_msg = L.log_trackio("05b_pretrained_model", metrics, {"model_id": MODEL_ID, "zero_shot": True})

    lines = [
        "=== Step 2b: Chronos-Bolt small, zero-shot, CPU only ===",
        f"Model: {MODEL_ID}. Context {CONTEXT_LEN} days, no fine-tuning, no upload.",
        f"Elapsed: {time.time()-started:.0f}s",
        score_df.to_string(index=False),
        inv_df.to_string(index=False),
        f"Chart: {chart}",
        f"Trackio: {trackio_msg}",
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    (RESULTS / "05b_run_log.txt").write_text(text)


if __name__ == "__main__":
    main()
