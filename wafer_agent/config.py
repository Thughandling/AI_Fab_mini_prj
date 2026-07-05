"""API 키 및 파라미터 설정."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "Qwen/Qwen3-0.6B")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # mock | anthropic | qwen

N_STEPS: int = 500
Z_SCORE: float = 1.96
WINDOW_SIZE: int = 20
MIN_ANOMALY_SEGMENTS: int = 3
MAX_ANOMALY_SEGMENTS: int = 5
REPORT_DIR: Path = Path(__file__).resolve().parents[1] / "reports"
COOLDOWN_STEPS: int = 25
