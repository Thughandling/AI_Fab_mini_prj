# src

PoC **모듈 설계 레이아웃**입니다.  
실행 가능한 구현은 [`notebooks/AI_DigitalFactory.ipynb`](../notebooks/AI_DigitalFactory.ipynb)에 있으며, 향후 production 분리 시 이 구조로 이전합니다.

```
src/
├── agents/     # LangGraph StateGraph
├── tools/      # detect, classify, action, report
└── prompts/    # LLM system prompts
```
