#!/usr/bin/env python3
"""Milestone 10, Stanford: Chronos-Bolt small (amazon/chronos-bolt-small, as published,
not fine-tuned), mean forecast, context = all available history up to 512 days,
origins 199..878, h = 1..3. Zero-shot, CPU, no data uploaded, no sign-in.
Run: .venv-chronos/bin/python study2/scripts/10b_m10_chronos.py
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from chronos import BaseChronosPipeline

for v in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
    os.environ.pop(v, None)
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
STUDY = Path(__file__).resolve().parent.parent
df = pd.read_csv(STUDY / "data/derived/stanford_day3_aligned.csv")
y = df["y"].values.astype(float)
N, FIRST, H, CTX = 880, 199, 3, 512
pipe = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map="cpu", torch_dtype=torch.float32)
rows = []
origins = list(range(FIRST, N - 1))
for b in range(0, len(origins), 64):
    batch = origins[b:b + 64]
    ctx = [torch.tensor(y[max(0, i + 1 - CTX):i + 1], dtype=torch.float32) for i in batch]
    with torch.no_grad():
        q, mean = pipe.predict_quantiles(ctx, prediction_length=H, quantile_levels=[0.5])
    m = mean.cpu().numpy()
    for bi, i in enumerate(batch):
        for h in range(1, H + 1):
            if i + h < N:
                rows.append(dict(origin=i, h=h, target=i + h, model="cb", fc=float(max(m[bi, h - 1], 0.0))))
out = pd.DataFrame(rows)
out.to_csv(STUDY / "results/s2m10/10b_forecasts_chronos.csv", index=False)
print(out.fc.describe())
