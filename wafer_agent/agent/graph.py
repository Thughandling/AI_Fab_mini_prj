"""LangGraph StateGraph — detect → classify → action → report."""
from __future__ import annotations

from typing import Any, Literal, TypedDict

import pandas as pd
from langgraph.graph import END, START, StateGraph

from wafer_agent.tools.action import run_action_decision
from wafer_agent.tools.classifier import run_classification
from wafer_agent.tools.detector import run_detection
from wafer_agent.tools.reporter import run_report


class WaferState(TypedDict, total=False):
    sensor_data: pd.DataFrame
    current_idx: int
    anomaly_result: dict[str, Any]
    classification_result: dict[str, Any]
    action_result: dict[str, Any]
    report: str
    report_meta: dict[str, Any]
    events: list[dict[str, Any]]


def detect_node(state: WaferState) -> dict[str, Any]:
    idx = state["current_idx"]
    df = state["sensor_data"]
    history = df.iloc[:idx]
    current = df.iloc[idx]
    result = run_detection(history, current)
    print(f"  [detect] t={idx} anomaly={result['is_anomaly']}")
    return {"anomaly_result": result}


def classify_node(state: WaferState) -> dict[str, Any]:
    idx = state["current_idx"]
    df = state["sensor_data"]
    start = max(0, idx - 19)
    recent = df.iloc[start : idx + 1][["timestamp", "value"]].copy()
    recent["timestamp"] = recent["timestamp"].astype(str)
    recent_list = recent.where(recent.notna(), None).to_dict(orient="records")
    result = run_classification(recent_list)
    print(f"  [classify] type={result['anomaly_type']} conf={result['confidence']:.0%}")
    return {"classification_result": result}


def action_node(state: WaferState) -> dict[str, Any]:
    result = run_action_decision(state["classification_result"])
    print(f"  [action] level={result['action_level']} — {result['action_description']}")
    return {"action_result": result}


def report_node(state: WaferState) -> dict[str, Any]:
    meta = run_report(
        state["anomaly_result"],
        state["classification_result"],
        state["action_result"],
    )
    print(f"  [report] saved → {meta['filename']}")
    event = {
        "idx": state["current_idx"],
        "anomaly": state["anomaly_result"],
        "classification": state["classification_result"],
        "action": state["action_result"],
        "report_file": meta["filename"],
    }
    events = list(state.get("events", []))
    events.append(event)
    return {"report": meta["report"], "report_meta": meta, "events": events}


def route_after_detect(state: WaferState) -> Literal["classify", "end"]:
    if state.get("anomaly_result", {}).get("is_anomaly"):
        return "classify"
    return "end"


def build_agent():
    workflow = StateGraph(WaferState)
    workflow.add_node("detect", detect_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("action", action_node)
    workflow.add_node("report_gen", report_node)

    workflow.add_edge(START, "detect")
    workflow.add_conditional_edges(
        "detect",
        route_after_detect,
        {"classify": "classify", "end": END},
    )
    workflow.add_edge("classify", "action")
    workflow.add_edge("action", "report_gen")
    workflow.add_edge("report_gen", END)
    return workflow.compile()


def run_anomaly_pipeline(
    sensor_data: pd.DataFrame,
    current_idx: int,
    events: list[dict[str, Any]] | None = None,
) -> WaferState:
    """단일 시점에 대해 Agent 파이프라인 실행."""
    app = build_agent()
    return app.invoke(
        {
            "sensor_data": sensor_data,
            "current_idx": current_idx,
            "events": events or [],
        }
    )
