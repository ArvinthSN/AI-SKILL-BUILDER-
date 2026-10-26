from fastapi import FastAPI

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
