"""Tool 1: ARMA 기반 이상탐지."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from langchain.tools import tool
from statsmodels.tsa.arima.model import ARIMA

from wafer_agent.config import Z_SCORE


def _fit_predict(history: pd.Series) -> tuple[float, float, float]:
    """ARMA(1,1) 적합 후 1-step 예측 및 95% CI."""
    clean = history.dropna()
    if len(clean) < 10:
        mean = float(clean.mean()) if len(clean) else 0.0
        std = float(clean.std()) if len(clean) > 1 else 1.0
        return mean, mean + Z_SCORE * std, mean - Z_SCORE * std

    try:
        model = ARIMA(clean, order=(1, 0, 1))
        fitted = model.fit()
        fc = fitted.get_forecast(steps=1)
        pred = float(fc.predicted_mean.iloc[0])
        ci = fc.conf_int(alpha=0.05)
        lower = float(ci.iloc[0, 0])
        upper = float(ci.iloc[0, 1])
        return pred, upper, lower
    except Exception:
        mean = float(clean.mean())
        std = float(clean.std()) if clean.std() > 0 else 1.0
        return mean, mean + Z_SCORE * std, mean - Z_SCORE * std


def run_detection(
    history: pd.DataFrame,
    current_row: pd.Series,
) -> dict[str, Any]:
    """현재 시점 이상탐지 (내부 호출용)."""
    hist_values = history["value"].copy()
    ts = current_row["timestamp"]
    actual = current_row["value"]

    predicted, upper, lower = _fit_predict(hist_values)

    is_anomaly = False
    if pd.isna(actual):
        is_anomaly = True
    elif actual > upper or actual < lower:
        is_anomaly = True

    return {
        "timestamp": str(ts),
        "value": None if pd.isna(actual) else float(actual),
        "predicted": round(predicted, 4),
        "upper_bound": round(upper, 4),
        "lower_bound": round(lower, 4),
        "is_anomaly": is_anomaly,
    }


@tool
def detect_anomaly(sensor_history_json: str, current_point_json: str) -> str:
    """ARMA(1,1) 모델로 현재 센서값의 이상 여부를 판정한다.

    Args:
        sensor_history_json: 과거 센서 데이터 JSON (timestamp, value)
        current_point_json: 현재 시점 JSON (timestamp, value)
    """
    history = pd.DataFrame(json.loads(sensor_history_json))
    current = pd.Series(json.loads(current_point_json))
    result = run_detection(history, current)
    return json.dumps(result, ensure_ascii=False)
