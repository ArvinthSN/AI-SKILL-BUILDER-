import pytest
from fastapi.testclient import TestClient

from app.backend.main import app, generate_llm_response
from app.backend.llm_service import (
    GenerateRequest,
    LLMConfigurationError,
    LLMProviderError,
    generate_text,
)

client = TestClient(app)


def test_generate_endpoint_returns_generated_text(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    def fake_post(self, url, json, headers=None, timeout=None):
        class MockResponse:
            status_code = 200

            def json(self):
                return {
                    "choices": [
                        {"message": {"content": "Generated skill instruction."}}
                    ]
                }

        return MockResponse()

    monkeypatch.setattr("app.backend.llm_service.httpx.Client.post", fake_post)

    result = generate_llm_response(GenerateRequest(prompt="Create a Python skill for fast code reviews."))

    assert result == {"response": "Generated skill instruction.", "model": "gpt-4o-mini"}


def test_generate_endpoint_rejects_blank_prompt():
    with pytest.raises(ValueError, match="Prompt must not be empty"):
        generate_text("   ")


def test_generate_text_raises_configuration_error_without_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError, match="LLM API key is not configured"):
        generate_text("Write a skill outline.")


def test_generate_text_raises_provider_error_on_timeout(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    def fake_post(self, url, json, headers=None, timeout=None):
        raise TimeoutError("Request timed out")

    monkeypatch.setattr("app.backend.llm_service.httpx.Client.post", fake_post)

    with pytest.raises(LLMProviderError, match="timed out"):
        generate_text("Write a skill outline.")
