#!/usr/bin/env python3
"""Generate architecture.png and demo.gif for README."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]


def draw_architecture(path: Path):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title(
        "AI Digital Factory PoC — Agent Workflow",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )

    boxes = [
        (0.3, 2.0, 1.8, 1.2, "Sensor\nSimulator", "#DBEAFE"),
        (2.5, 2.0, 1.8, 1.2, "Detect\n(ARMA)", "#FEF3C7"),
        (4.7, 2.0, 1.8, 1.2, "Classify\n(Qwen LLM)", "#E9D5FF"),
        (6.9, 2.0, 1.8, 1.2, "Action\n(Qwen LLM)", "#FED7AA"),
        (9.1, 2.0, 1.8, 1.2, "Report\n(Markdown)", "#D1FAE5"),
    ]
    for x, y, w, h, label, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                facecolor=color, edgecolor="#374151", linewidth=1.5,
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)

    for x1, x2 in [(2.1, 2.5), (4.3, 4.7), (6.5, 6.9), (8.7, 9.1)]:
        ax.add_patch(
            FancyArrowPatch(
                (x1, 2.6), (x2, 2.6),
                arrowstyle="-|>", mutation_scale=14, color="#374151", lw=1.8,
            )
        )

    ax.text(3.4, 1.2, "Normal → Keep monitoring", ha="center", fontsize=9, color="#6B7280")
    ax.annotate("", xy=(2.5, 1.5), xytext=(3.4, 1.35),
                arrowprops=dict(arrowstyle="-|>", color="#9CA3AF"))

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_demo_gif(path: Path, frames: int = 60):
    rng = np.random.default_rng(42)
    t = np.arange(120)
    base = 100 + np.cumsum(rng.normal(0, 0.3, 120))
    base[70:75] += np.linspace(0, 12, 5)
    base[75:80] = np.nan

    fig, ax = plt.subplots(figsize=(8, 3.5))
    line, = ax.plot([], [], color="#2563EB", lw=1.2)
    anomaly_line = ax.axvline(70, color="#EF4444", ls="--", alpha=0.7, visible=False)
    ax.set_xlim(0, 119)
    ax.set_ylim(base[~np.isnan(base)].min() - 3, base[~np.isnan(base)].max() + 5)
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Sensor Value")
    ax.set_title("Wafer Sensor Monitoring — PoC Demo")
    ax.grid(True, alpha=0.25)

    status = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=10,
                     va="top", bbox=dict(boxstyle="round", facecolor="#FEF3C7", alpha=0.9))

    def update(frame):
        end = min(120, 20 + frame * 2)
        line.set_data(t[:end], base[:end])
        if end > 70:
            anomaly_line.set_visible(True)
            status.set_text("⚠ Anomaly → Classify → Action → Report")
        else:
            anomaly_line.set_visible(False)
            status.set_text("Monitoring...")
        return line, anomaly_line, status

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=80, blit=False)
    ani.save(path, writer="pillow", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    draw_architecture(ROOT / "architecture.png")
    draw_demo_gif(ROOT / "demo.gif")
    print("Generated:", ROOT / "architecture.png", ROOT / "demo.gif")
