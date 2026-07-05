"""진입점 — 센서 데이터 생성 후 Agent 순차 모니터링."""
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd

from wafer_agent.agent.graph import build_agent
from wafer_agent.config import N_STEPS, REPORT_DIR, COOLDOWN_STEPS
from wafer_agent.simulator import generate_sensor_data


def run_monitoring(
    sensor_data: pd.DataFrame | None = None,
    seed: int = 42,
    warmup: int = 30,
    verbose: bool = True,
) -> tuple[pd.DataFrame, list[dict]]:
    """500 step 센서 데이터를 순차 모니터링 (이상 구간 진입 시 1회 파이프라인 실행)."""
    from wafer_agent.tools.detector import run_detection

    df = sensor_data if sensor_data is not None else generate_sensor_data(N_STEPS, seed=seed)
    app = build_agent()
    events: list[dict] = []
    prev_anomaly = False
    cooldown_until = -1

    if verbose:
        print(f"=== 웨이퍼 센서 모니터링 시작 ({len(df)} steps) ===")

    for idx in range(warmup, len(df)):
        detection = run_detection(df.iloc[:idx], df.iloc[idx])
        is_anomaly = detection["is_anomaly"]

        if is_anomaly and not prev_anomaly and idx >= cooldown_until:
            if verbose:
                print(f"\n⚠️  이상 구간 진입 @ step {idx}")
            state = app.invoke(
                {"sensor_data": df, "current_idx": idx, "events": events}
            )
            events = state.get("events", events)
            cooldown_until = idx + COOLDOWN_STEPS
            if verbose:
                cls = state.get("classification_result", {})
                act = state.get("action_result", {})
                print(f"   분류: {cls.get('anomaly_type')} | 대응: Level {act.get('action_level')}")

        prev_anomaly = is_anomaly

    if verbose:
        print(f"\n=== 완료: {len(events)}건 이상 처리, 리포트 → {REPORT_DIR} ===")

    return df, events


def visualize(
    df: pd.DataFrame,
    events: list[dict],
    save_path: str | None = "wafer_monitoring.png",
) -> None:
    """센서 데이터 + 이상 구간 + 대응 결과 시각화."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df.index, df["value"], color="#2563eb", linewidth=0.8, label="센서값")

    colors = {1: "#fbbf24", 2: "#f97316", 3: "#ef4444"}
    for ev in events:
        idx = ev["idx"]
        level = ev["action"].get("action_level", 1)
        ax.axvline(idx, color=colors.get(level, "#ef4444"), alpha=0.6, linestyle="--")
        ax.scatter(idx, df.iloc[idx]["value"], color=colors.get(level, "#ef4444"), s=40, zorder=5)

    gt_spike = df.index[df["ground_truth"] == "SPIKE"]
    gt_drift = df.index[df["ground_truth"] == "DRIFT"]
    gt_loss = df.index[df["ground_truth"] == "LOSS"]
    ax.scatter(gt_spike, df.loc[gt_spike, "value"], marker="^", s=15, alpha=0.3, label="GT SPIKE")
    ax.scatter(gt_drift, df.loc[gt_drift, "value"], marker="s", s=15, alpha=0.3, label="GT DRIFT")
    ax.scatter(gt_loss, df.loc[gt_loss, "value"], marker="x", s=15, alpha=0.3, label="GT LOSS")

    ax.set_xlabel("Time Step")
    ax.set_ylabel("Sensor Value")
    ax.set_title("Wafer Sensor Monitoring — Anomaly Detection & Response")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=120)
        print(f"시각화 저장: {save_path}")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Wafer Anomaly Detection Agent")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    df, events = run_monitoring(seed=args.seed)
    if not args.no_plot:
        visualize(df, events)


if __name__ == "__main__":
    main()
