"""Tool 3: 대응 액션 결정."""
from __future__ import annotations

import json
from typing import Any

from langchain.tools import tool
from pydantic import BaseModel, Field

from wafer_agent.llm import invoke_structured


class ActionResult(BaseModel):
    action_level: int = Field(ge=1, le=3)
    action_description: str
    reason: str


def _mock_action(classification: dict[str, Any]) -> dict[str, Any]:
    atype = classification.get("anomaly_type", "SPIKE")
    conf = classification.get("confidence", 0.5)

    if atype == "LOSS" and conf >= 0.7:
        return {
            "action_level": 3,
            "action_description": "장비 중단 + 웨이퍼 재배치 지시",
            "reason": "센서 데이터 손실은 공정 추적 불가로 심각 등급 대응이 필요합니다.",
        }
    if atype == "SPIKE" and conf >= 0.75:
        return {
            "action_level": 2,
            "action_description": "해당 로트 격리 + 엔지니어 통보",
            "reason": "급격한 스파이크는 장비 이상 가능성이 높아 로트 격리가 필요합니다.",
        }
    if atype == "DRIFT":
        return {
            "action_level": 2,
            "action_description": "해당 로트 격리 + 엔지니어 통보",
            "reason": "공정 파라미터 드리프트는 수율 영향 가능성이 있어 격리·점검이 필요합니다.",
        }
    return {
        "action_level": 1,
        "action_description": "알람 발생 + 모니터링 강화",
        "reason": "경미한 이상으로 판단되어 모니터링 강화 수준으로 대응합니다.",
    }


def run_action_decision(classification: dict[str, Any]) -> dict[str, Any]:
    """원인 분류 결과 기반 대응 수준 결정."""
    system = (
        "반도체 Fab 웨이퍼 이상 대응 Agent입니다. 분류 결과를 바탕으로 action_level을 결정하세요.\n"
        "- Level 1 (경미): 알람 + 모니터링 강화\n"
        "- Level 2 (중간): 로트 격리 + 엔지니어 통보\n"
        "- Level 3 (심각): 장비 중단 + 웨이퍼 재배치\n"
        "JSON: action_level(1~3), action_description, reason(한국어 근거)"
    )
    user = f"분류 결과:\n{json.dumps(classification, ensure_ascii=False)}"

    result = invoke_structured(system, user, ActionResult)
    if result is not None:
        return result
    return _mock_action(classification)


@tool
def decide_action(classification_json: str) -> str:
    """원인 분류 결과를 바탕으로 대응 수준(Level 1~3)을 결정한다.

    Args:
        classification_json: {anomaly_type, confidence, description} JSON
    """
    classification = json.loads(classification_json)
    result = run_action_decision(classification)
    return json.dumps(result, ensure_ascii=False)
