---
name: fastapi-backend
description: Scaffold and build clean, production-ready FastAPI backends. Use whenever the user wants to create a FastAPI project or API, add routers/endpoints, set up a database (SQLAlchemy/Alembic), add JWT authentication, configure settings or CORS, write tests, or containerize with Docker, even if they only say "backend", "REST API" or "Python API" without naming FastAPI.
---

# FastAPI Backend

Build FastAPI backends with a consistent, layered structure.

## Workflow

1. **Clarify** what the API is for (entities, auth needed, database choice). Default to SQLite for development, PostgreSQL for production.
2. **Scaffold** the project:
   ```bash
   python scripts/scaffold_project.py <project-name> [--path <dir>]
   ```
3. **Add features** one at a time. For each new resource, generate files with:
   ```bash
   python scripts/add_resource.py <project-dir> <resource-name>
   ```
   This creates the model, schema, service and router, and prints the line to register the router in `app/main.py`.
4. **Customize** the generated code to the user's actual fields and rules.
5. **Verify**: install dependencies, run `pytest`, and start with `fastapi dev app/main.py`.

## Layering rules

Keep responsibilities separate:

- `routers/`: HTTP only (parse request, call service, return response). No business logic.
- `services/`: business logic and database operations.
- `models/`: SQLAlchemy tables.
- `schemas/`: Pydantic request/response shapes. Never return ORM models directly.
- `core/`: settings, security, shared dependencies.

## Conventions

- Use `async def` only with async-capable libraries; otherwise plain `def`.
- Read all config from environment via `pydantic-settings`. Never hardcode secrets.
- Separate schemas per purpose: `XCreate`, `XUpdate`, `XRead`.
- Use dependency injection (`Depends`) for the DB session and the current user.
- Return proper status codes (201 create, 204 delete, 404 missing, 409 conflict).
- Version routes under `/api/v1`.

## Reference files (read only when needed)

- `references/project-structure.md`: folder layout and what goes where
- `references/database.md`: SQLAlchemy session setup and Alembic migrations
- `references/auth-jwt.md`: password hashing, token creation, protected routes
- `references/deployment.md`: Dockerfile, production server, env checklist

## Output

Give the user the working project folder, the commands to run it, and a short list of what to customize next.
