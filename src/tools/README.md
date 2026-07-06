# src/tools

LangChain `@tool` 기반 **4개 Tool** 정의 영역입니다.

## PoC 구현 위치

[`notebooks/AI_DigitalFactory.ipynb`](../../notebooks/AI_DigitalFactory.ipynb) **Step 2~4** 셀

| Tool | 함수 | 설명 |
|------|------|------|
| Tool 1 | `detect_anomaly` | ARMA(1,1) + 95% CI |
| Tool 2 | `classify_anomaly_cause` | SPIKE / DRIFT / LOSS |
| Tool 3 | `decide_action` | Level 1~3 대응 |
| Tool 4 | `generate_report` | Markdown 리포트 |

## 향후 분리 계획

```
tools/
  detector.py
  classifier.py
  action.py
  reporter.py
```
