"""Tool 4: Markdown 리포트 자동 생성."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain.tools import tool

from wafer_agent.config import REPORT_DIR


def _build_markdown(
    anomaly: dict[str, Any],
    classification: dict[str, Any],
    action: dict[str, Any],
) -> str:
    ts = anomaly.get("timestamp", datetime.now().isoformat())
    return f"""# 웨이퍼 이상탐지 리포트

**발생 시각:** {ts}

## 1. 이상탐지 결과

| 항목 | 값 |
|------|-----|
| 센서값 | {anomaly.get('value')} |
| 예측값 | {anomaly.get('predicted')} |
| 상한 (95% CI) | {anomaly.get('upper_bound')} |
| 하한 (95% CI) | {anomaly.get('lower_bound')} |
| 이상 여부 | {'⚠️ 이상' if anomaly.get('is_anomaly') else '정상'} |

## 2. 원인 분류

- **유형:** {classification.get('anomaly_type')}
- **신뢰도:** {classification.get('confidence', 0):.0%}
- **설명:** {classification.get('description')}

## 3. 대응 조치

- **대응 수준:** Level {action.get('action_level')}
- **조치:** {action.get('action_description')}
- **근거:** {action.get('reason')}

---
*Digital Factory AI Agent — 자동 생성*
"""


def run_report(
    anomaly: dict[str, Any],
    classification: dict[str, Any],
    action: dict[str, Any],
    save: bool = True,
) -> dict[str, Any]:
    """Markdown 리포트 생성 및 저장."""
    md = _build_markdown(anomaly, classification, action)
    ts_raw = str(anomaly.get("timestamp", "")).replace(":", "-").replace(" ", "_")
    filename = f"anomaly_report_{ts_raw}.md"

    filepath = None
    if save:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        filepath = REPORT_DIR / filename
        filepath.write_text(md, encoding="utf-8")

    return {
        "filename": filename,
        "filepath": str(filepath) if filepath else None,
        "report": md,
    }


@tool
def generate_report(
    anomaly_json: str,
    classification_json: str,
    action_json: str,
) -> str:
    """이상탐지·분류·대응 결과를 Markdown 리포트로 생성한다.

    Args:
        anomaly_json: 이상탐지 결과 JSON
        classification_json: 원인 분류 JSON
        action_json: 대응 액션 JSON
    """
    result = run_report(
        json.loads(anomaly_json),
        json.loads(classification_json),
        json.loads(action_json),
    )
    return json.dumps(result, ensure_ascii=False)
