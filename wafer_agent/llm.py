"""LLM provider — mock | anthropic | qwen (HuggingFace Qwen3-0.6B)."""
from __future__ import annotations

import json
import os
import re
from types import SimpleNamespace
from typing import Any, Type

from pydantic import BaseModel

from wafer_agent.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, HF_MODEL_ID, LLM_PROVIDER

_qwen_model = None
_qwen_tokenizer = None
_qwen_device = "cpu"


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", LLM_PROVIDER)


def is_llm_enabled() -> bool:
    return _provider() not in ("mock", "")


def load_qwen_model(model_id: str | None = None, force: bool = False) -> tuple[Any, Any]:
    """HuggingFace Qwen3-0.6B 로드 (Colab GPU/CPU 자동 선택)."""
    global _qwen_model, _qwen_tokenizer, _qwen_device

    if _qwen_model is not None and not force:
        return _qwen_model, _qwen_tokenizer

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_id = model_id or os.getenv("HF_MODEL_ID", HF_MODEL_ID)
    _qwen_device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if _qwen_device == "cuda" else torch.float32

    print(f"[Qwen] loading {model_id} on {_qwen_device} ...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if _qwen_device == "cuda":
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            trust_remote_code=True,
        ).to(_qwen_device)

    model.eval()
    _qwen_model, _qwen_tokenizer = model, tokenizer
    print(f"[Qwen] ready ({sum(p.numel() for p in model.parameters()) / 1e6:.1f}M params)")
    return model, tokenizer


def _generate_qwen(system: str, user: str, max_new_tokens: int = 384) -> str:
    import torch

    model, tokenizer = load_qwen_model()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"No JSON object in LLM output: {text[:200]}")


def _get_anthropic():
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.getenv("CLAUDE_MODEL", CLAUDE_MODEL),
        temperature=0.2,
        api_key=ANTHROPIC_API_KEY,
    )


class QwenLLMWrapper:
    """LangChain-style wrapper for Qwen local model."""

    def invoke(self, prompt: str) -> SimpleNamespace:
        if "\n\n" in prompt:
            system, user = prompt.split("\n\n", 1)
        else:
            system, user = "You are a helpful assistant.", prompt
        return SimpleNamespace(content=_generate_qwen(system, user))

    def with_structured_output(self, schema: Type[BaseModel]):
        return _QwenStructured(self, schema)


class _QwenStructured:
    def __init__(self, llm: QwenLLMWrapper, schema: Type[BaseModel]):
        self.llm = llm
        self.schema = schema

    def invoke(self, prompt: str) -> BaseModel:
        fields = ", ".join(self.schema.model_fields.keys())
        extra = f"\n\n반드시 유효한 JSON만 출력하세요. 필드: {fields}. 마크다운 코드블록 없이."
        resp = self.llm.invoke(prompt + extra)
        data = _extract_json(resp.content)
        return self.schema.model_validate(data)


def get_llm() -> Any | None:
    """Provider에 맞는 LLM 반환. mock이면 None."""
    provider = _provider()
    if provider == "mock":
        return None
    if provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            return None
        return _get_anthropic()
    if provider == "qwen":
        load_qwen_model()
        return QwenLLMWrapper()
    return None


def invoke_structured(
    system: str,
    user: str,
    schema: Type[BaseModel],
) -> dict[str, Any] | None:
    """LLM structured JSON 호출. mock/실패 시 None."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        out = llm.with_structured_output(schema).invoke(f"{system}\n\n{user}")
        if isinstance(out, BaseModel):
            return out.model_dump()
        if isinstance(out, dict):
            return schema.model_validate(out).model_dump()
    except Exception:
        if _provider() == "qwen":
            try:
                raw = _generate_qwen(
                    system,
                    user + "\n\nJSON만 출력 (필드: "
                    + ", ".join(schema.model_fields.keys())
                    + ")",
                )
                return schema.model_validate(_extract_json(raw)).model_dump()
            except Exception:
                pass
        elif _provider() == "anthropic":
            try:
                resp = llm.invoke(f"{system}\n\n{user}")
                text = resp.content if hasattr(resp, "content") else str(resp)
                return schema.model_validate(_extract_json(text)).model_dump()
            except Exception:
                pass
    return None
