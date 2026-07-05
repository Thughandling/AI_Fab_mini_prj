"""Tool 2: LLM 기반 이상 원인 분류."""
from __future__ import annotations

import json
from typing import Any

from langchain.tools import tool
from pydantic import BaseModel, Field

from wafer_agent.llm import invoke_structured


class ClassificationResult(BaseModel):
    anomaly_type: str = Field(description="SPIKE | DRIFT | LOSS")
    confidence: float = Field(ge=0.0, le=1.0)
    description: str


def _mock_classify(recent_data: list[dict]) -> dict[str, Any]:
    values = [d.get("value") for d in recent_data]
    n_missing = sum(1 for v in values if v is None or (isinstance(v, float) and v != v))

    if values and (values[-1] is None or (isinstance(values[-1], float) and values[-1] != values[-1])):
        return {
            "anomaly_type": "LOSS",
            "confidence": 0.92,
            "description": "현재 시점 센서값 결측 — 센서 이슈 의심",
        }

    if n_missing >= 3:
        return {
            "anomaly_type": "LOSS",
            "confidence": 0.88,
            "description": "최근 구간에서 결측/센서 데이터 손실 패턴이 반복됩니다.",
        }

    clean = [v for v in values if v is not None and v == v]
    if len(clean) >= 5:
        diffs = [abs(clean[i] - clean[i - 1]) for i in range(1, len(clean))]
        if diffs and max(diffs) > 5:
            return {
                "anomaly_type": "SPIKE",
                "confidence": 0.85,
                "description": "급격한 수치 변화(Spike)가 관측되어 장비 이슈를 의심합니다.",
            }
        slope = (clean[-1] - clean[0]) / len(clean)
        if abs(slope) > 0.3:
            return {
                "anomaly_type": "DRIFT",
                "confidence": 0.82,
                "description": "점진적 드리프트 패턴으로 공정 파라미터 이상을 의심합니다.",
            }

    return {
        "anomaly_type": "SPIKE",
        "confidence": 0.6,
        "description": "패턴이 불명확하나 이상치로 분류됩니다.",
    }


def run_classification(recent_data: list[dict]) -> dict[str, Any]:
    """최근 20개 시점 데이터로 원인 분류."""
    system = (
        "반도체 웨이퍼 센서 이상 분류 Agent입니다. "
        "최근 시계열 데이터를 분석해 anomaly_type을 분류하세요.\n"
        "- SPIKE: 급격한 수치 변화 → 장비 이슈\n"
        "- DRIFT: 점진적 변화 → 공정 파라미터 이상\n"
        "- LOSS: 결측/NaN → 센서 이슈\n"
        "JSON만 출력: anomaly_type, confidence(0~1), description(한국어)"
    )
    user = f"최근 20개 시점 데이터:\n{json.dumps(recent_data, ensure_ascii=False, indent=2)}"

    result = invoke_structured(system, user, ClassificationResult)
    if result is not None:
        return result
    return _mock_classify(recent_data)


@tool
def classify_anomaly_cause(recent_data_json: str) -> str:
    """최근 20개 시점 센서 데이터를 LLM으로 분석해 이상 원인을 분류한다.

    Args:
        recent_data_json: [{timestamp, value}, ...] JSON 문자열
    """
    recent = json.loads(recent_data_json)
    result = run_classification(recent)
    return json.dumps(result, ensure_ascii=False)
