from __future__ import annotations

import httpx
from pydantic import BaseModel, Field, field_validator

from app.backend.config import get_llm_settings


class LLMConfigurationError(RuntimeError):
    """Raised when LLM credentials or settings are missing or invalid."""


class LLMProviderError(RuntimeError):
    """Raised when the upstream provider responds with an error."""


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Prompt must not be empty.")

        settings = get_llm_settings()
        if len(normalized) > settings.max_prompt_length:
            raise ValueError(
                f"Prompt must be {settings.max_prompt_length} characters or fewer."
            )

        return normalized


class GenerateResponse(BaseModel):
    response: str
    model: str


def generate_text(prompt: str, *, model: str | None = None, timeout: float | None = None) -> GenerateResponse:
    settings = get_llm_settings()
    normalized_prompt = prompt.strip()

    if not normalized_prompt:
        raise ValueError("Prompt must not be empty.")

    if len(normalized_prompt) > settings.max_prompt_length:
        raise ValueError(
            f"Prompt must be {settings.max_prompt_length} characters or fewer."
        )

    if not settings.api_key:
        raise LLMConfigurationError("LLM API key is not configured.")

    request_model = model or settings.model
    payload = {
        "model": request_model,
        "messages": [{"role": "user", "content": normalized_prompt}],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }

    timeout_value = timeout if timeout is not None else settings.timeout

    try:
        with httpx.Client(base_url=settings.base_url, timeout=timeout_value) as client:
            response = client.post("/chat/completions", json=payload, headers=headers)
    except TimeoutError as exc:
        raise LLMProviderError("The LLM provider timed out while processing the request.") from exc
    except httpx.HTTPError as exc:
        raise LLMProviderError("The LLM provider request failed.") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise LLMProviderError("The LLM provider returned an invalid response.") from exc

    if response.status_code >= 400:
        error_detail = body.get("error", {}).get("message", "The LLM provider rejected the request.")
        raise LLMProviderError(error_detail)

    choices = body.get("choices") or []
    if not choices:
        raise LLMProviderError("The LLM provider returned no completion choices.")

    content = choices[0].get("message", {}).get("content", "")
    if not content or not str(content).strip():
        raise LLMProviderError("The LLM provider returned an empty response.")

    return GenerateResponse(response=str(content).strip(), model=request_model)
