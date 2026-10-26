from fastapi import FastAPI, HTTPException

from app.backend.llm_service import (
    GenerateRequest,
    LLMConfigurationError,
    LLMProviderError,
    generate_text,
)

app = FastAPI(
    title="SkillForge API",
    version="0.1.0",
    description="Initial backend for SkillForge",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "skillforge-api",
    }


@app.post("/api/v1/llm/generate")
def generate_llm_response(payload: GenerateRequest):
    try:
        result = generate_text(payload.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return result.model_dump()
