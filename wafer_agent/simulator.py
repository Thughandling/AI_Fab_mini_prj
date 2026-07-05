"""웨이퍼 센서 데이터 시뮬레이터 — ARMA(1,1) + 이상 패턴 주입."""
from __future__ import annotations

import random
from typing import Literal

import numpy as np
import pandas as pd
from statsmodels.tsa.arima_process import ArmaProcess

AnomalyType = Literal["SPIKE", "DRIFT", "LOSS", "NORMAL"]

ARMA_AR = np.array([1.0, -0.6])
ARMA_MA = np.array([1.0, 0.4])
BASE_SCALE = 100.0


def _generate_normal_series(n_steps: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    process = ArmaProcess(ar=ARMA_AR, ma=ARMA_MA)
    raw = process.generate_sample(nsample=n_steps, scale=1.0, burnin=100)
    return BASE_SCALE + raw + rng.normal(0, 0.5, n_steps)


def _inject_spike(values: np.ndarray, start: int, rng: np.random.Generator) -> None:
    length = rng.integers(1, 4)
    magnitude = rng.uniform(8, 15)
    for i in range(start, min(start + length, len(values))):
        values[i] += magnitude * (1 if rng.random() > 0.3 else -1)


def _inject_drift(values: np.ndarray, start: int, rng: np.random.Generator) -> None:
    length = rng.integers(20, 41)
    step = rng.uniform(0.15, 0.35) * (1 if rng.random() > 0.5 else -1)
    for i in range(start, min(start + length, len(values))):
        values[i] += step * (i - start + 1)


def _inject_loss(values: np.ndarray, start: int, rng: np.random.Generator) -> None:
    length = rng.integers(5, 16)
    for i in range(start, min(start + length, len(values))):
        values[i] = np.nan


def generate_sensor_data(
    n_steps: int = 500,
    seed: int = 42,
    n_anomalies: int | None = None,
) -> pd.DataFrame:
    """정상 ARMA(1,1) 시계열에 3~5개 이상 구간을 주입한다."""
    rng = np.random.default_rng(seed)
    random.seed(seed)

    values = _generate_normal_series(n_steps, seed)
    labels: list[AnomalyType] = ["NORMAL"] * n_steps

    if n_anomalies is None:
        n_anomalies = rng.integers(3, 6)

    injectors = [
        ("SPIKE", _inject_spike, 3),
        ("DRIFT", _inject_drift, 30),
        ("LOSS", _inject_loss, 10),
    ]

    used_ranges: list[tuple[int, int]] = []
    attempts = 0
    placed = 0

    while placed < n_anomalies and attempts < 200:
        attempts += 1
        atype, fn, min_span = rng.choice(injectors)
        start = rng.integers(60, max(61, n_steps - min_span - 10))
        end = start + min_span

        overlap = any(not (end < s or start > e) for s, e in used_ranges)
        if overlap:
            continue

        fn(values, start, rng)
        end_actual = start + min_span
        for i in range(start, min(end_actual, n_steps)):
            labels[i] = atype
        used_ranges.append((start, end_actual))
        placed += 1

    timestamps = pd.date_range("2026-01-01", periods=n_steps, freq="1min")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "value": values,
            "ground_truth": labels,
        }
    )
