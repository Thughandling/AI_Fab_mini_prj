# Architecture — AI Digital Factory PoC

## 1. Overview

본 PoC는 반도체 Fab **웨이퍼 센서 데이터**를 입력으로 받아, 이상 탐지 → 원인 분류 → 대응 조치 → 리포트 생성까지를 **단일 LangGraph Agent**로 처리합니다.

실제 Fab 데이터 대신 **ARMA(1,1) 시뮬레이터**에 SPIKE / DRIFT / LOSS 패턴을 주입하여 End-to-End 파이프라인을 검증합니다.

---

## 2. Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     Monitoring Loop (500 steps)                  │
│                                                                  │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────────┐  │
│  │ Simulator  │───▶│  Detector   │───▶│  LangGraph Agent     │  │
│  │ ARMA(1,1)  │    │  Tool 1     │    │                      │  │
│  │ + Anomaly  │    │  statsmodels│    │  classify (Tool 2)   │  │
│  └────────────┘    └─────────────┘    │  action   (Tool 3)   │  │
│                                        │  report   (Tool 4)   │  │
│                                        └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    reports/anomaly_report_*.md
```

---

## 3. LangGraph State

| Field | Type | Description |
|-------|------|-------------|
| `sensor_data` | DataFrame | 전체 센서 시계열 |
| `current_idx` | int | 현재 모니터링 step |
| `anomaly_result` | dict | detect 결과 |
| `classification_result` | dict | SPIKE/DRIFT/LOSS |
| `action_result` | dict | Level 1~3 |
| `report` | str | Markdown 본문 |
| `events` | list | 탐지 이력 |

---

## 4. Conditional Edge

```python
detect_node → route_after_detect
                ├─ is_anomaly=True  → classify → action → report_gen
                └─ is_anomaly=False → END (모니터링 계속)
```

모니터링 루프에서는 **debounce + cooldown**으로 동일 구간 중복 리포트를 방지합니다.

---

## 5. LLM Provider

| Provider | 용도 |
|----------|------|
| `mock` | 파이프라인 구조 검증 (휴리스틱) |
| `qwen` | HuggingFace Qwen3-0.6B — Colab GPU |
| `anthropic` | Claude API (선택) |

---

## 6. Digital Factory 확장 로드맵

```
[PoC — 현재]          [Phase 2]              [Phase 3]
Simulator        →    FDC/MES API       →    Digital Twin
Notebook              src/ package           FastAPI Service
Qwen local            RAG knowledge base     Multi-Agent Fab
```

---

## 7. Reference

- 구현: [`notebooks/AI_DigitalFactory.ipynb`](../notebooks/AI_DigitalFactory.ipynb)
- 프롬프트: [`src/prompts/`](../src/prompts/)
- 개발 정의: [`AI_DigitalFactory_개발정의.xlsx`](./AI_DigitalFactory_개발정의.xlsx)
