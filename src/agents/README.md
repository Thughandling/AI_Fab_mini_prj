# src/agents

LangGraph **StateGraph** Agent 정의 영역입니다.

## PoC 구현 위치

현재 Agent 로직은 [`notebooks/AI_DigitalFactory.ipynb`](../../notebooks/AI_DigitalFactory.ipynb) **Step 5** 셀에 구현되어 있습니다.

| 노드 | 역할 |
|------|------|
| `detect_node` | ARMA 기반 이상탐지 |
| `classify_node` | LLM 원인 분류 |
| `action_node` | 대응 Level 결정 |
| `report_gen` | Markdown 리포트 저장 |

## 향후 분리 계획

```
agents/
  graph.py       # StateGraph 정의
  state.py       # WaferState TypedDict
  nodes.py       # detect / classify / action / report 노드
```
