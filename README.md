# AI Digital Factory — 웨이퍼 이상탐지 & 자동대응 Agent

반도체 Diffusion 공정 **웨이퍼 센서 데이터**를 모니터링하고, 이상 발생 시 **LangGraph Agent**가 원인 분류 → 대응 조치 → 리포트 생성까지 자동 수행합니다.

> **Colab 단일 노트북**으로 실행합니다. 별도 `.py` 모듈 없이 `AI_DigitalFactory.ipynb` 셀만 순서대로 실행하면 됩니다.

```
센서 시뮬레이터 → detect (ARMA) → [이상?] → classify (LLM) → action (LLM) → report
                                      ↓ 정상
                                   모니터링 계속
```

## 프로젝트 구조

```
AI-DigitalFactory/
├── AI_DigitalFactory.ipynb          # ★ Colab 메인 (전체 코드)
├── AI_DigitalFactory_개발정의.xlsx   # 셀별 함수·목적 정리
├── requirements.txt                 # pip 참고용
└── README.md
```

## Colab 실행

1. GitHub에서 `AI_DigitalFactory.ipynb` 열기 (또는 업로드)
2. **Runtime → Change runtime type → T4 GPU**
3. 셀 순서대로 실행:

| 순서 | 셀 | 내용 |
|------|-----|------|
| 1 | pip | transformers, torch, langgraph 등 설치 |
| 2 | GPU 확인 | `torch.cuda.is_available()` |
| 3 | Drive | (선택) Drive 마운트 |
| 4 | 환경설정 | `LLM_PROVIDER`, `HF_MODEL_ID` |
| 5 | Qwen 로드 | `Qwen/Qwen3-0.6B` HuggingFace 로드 |
| 6~ | Agent | 시뮬레이터 → Tools → LangGraph → 실행 |

4. 빠른 테스트: `LLM_PROVIDER = "mock"`
5. Qwen 사용: `LLM_PROVIDER = "qwen"`

## LLM 선택 (노트북 Cell 4)

| Provider | 설명 |
|----------|------|
| `mock` | API/모델 없이 휴리스틱 — 구조 검증용 |
| `qwen` | HuggingFace Qwen3-0.6B (Colab GPU 권장) |
| `anthropic` | Claude API (Colab Secrets: `ANTHROPIC_API_KEY`) |

## 노트북 셀 구성

| Step | 내용 |
|------|------|
| 1 | ARMA(1,1) 센서 시뮬레이터 + SPIKE/DRIFT/LOSS 주입 |
| 2~4 | Tool 1~4 (`@tool`: detect, classify, action, report) |
| 5 | LangGraph `StateGraph` (detect → classify → action → report_gen) |
| 6 | 500 step 모니터링 + 시각화 |

## 이상 유형 & 대응

| 분류 | 패턴 | 대응 예시 |
|------|------|-----------|
| **SPIKE** | 급격한 변화 | Level 2: 로트 격리 |
| **DRIFT** | 점진적 변화 | Level 2: 엔지니어 통보 |
| **LOSS** | 결측/NaN | Level 3: 장비 중단 |

## 왜 .py 파일이 없나?

초기 설계에는 `wafer_agent/` 로컬 CLI 패키지가 있었으나, **Colab 전용**으로 정리하면서 노트북에 코드를 모두 포함했습니다. Git에는 노트북 + 개발정의 Excel만 유지합니다.

## 라이선스

MIT — see [LICENSE](LICENSE)
