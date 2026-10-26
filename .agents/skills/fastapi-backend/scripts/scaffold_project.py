#!/usr/bin/env python3
"""Create a clean FastAPI project skeleton.

Usage: python scaffold_project.py <project-name> [--path DIR]
"""
import argparse
from pathlib import Path

FILES = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/models/__init__.py": "",
    "app/schemas/__init__.py": "",
    "app/services/__init__.py": "",
    "app/routers/__init__.py": "",
    "tests/__init__.py": "",
    "app/core/config.py": '''from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "__NAME__"
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-me"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
''',
    "app/db.py": '''from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
    "app/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine

# 1) Import models here so their tables are registered
# from app.models import item as item_model  # noqa: F401

# 2) Import routers here
# from app.routers import item

Base.metadata.create_all(bind=engine)  # dev only; use Alembic in production

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# 3) Register routers here, e.g.:
# app.include_router(item.router, prefix="/api/v1")
''',
    "tests/test_health.py": '''from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
''',
    "requirements.txt": "fastapi[standard]\nsqlalchemy\npydantic-settings\nalembic\npytest\nhttpx\n",
    ".env.example": "DATABASE_URL=sqlite:///./app.db\nSECRET_KEY=change-me\n",
    ".gitignore": "venv/\n__pycache__/\n.env\n*.db\n",
    "Dockerfile": '''FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    "README.md": "# __NAME__\n\n```bash\npython -m venv venv && source venv/bin/activate\npip install -r requirements.txt\nfastapi dev app/main.py\n```\n\nDocs: http://127.0.0.1:8000/docs\n",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--path", default=".")
    args = ap.parse_args()

    root = Path(args.path) / args.name
    if root.exists():
        raise SystemExit(f"Error: {root} already exists")

    for rel, content in FILES.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content.replace("__NAME__", args.name))

    print(f"Created {root}")
    print(f"Next: cd {root} && python -m venv venv && source venv/bin/activate")
    print("      pip install -r requirements.txt && fastapi dev app/main.py")


if __name__ == "__main__":
    main()
