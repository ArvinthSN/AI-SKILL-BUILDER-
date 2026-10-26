# Database

The scaffold already provides `app/db.py` (engine, `SessionLocal`, `Base`, `get_db`).
Use `Depends(get_db)` in routers.

## Migrations (Alembic)
```bash
alembic init migrations
# in migrations/env.py: from app.db import Base; target_metadata = Base.metadata
# set sqlalchemy.url from settings.database_url
alembic revision --autogenerate -m "create tables"
alembic upgrade head
```
Once Alembic is used, remove `Base.metadata.create_all(...)` from `main.py`.

## URLs
- SQLite: `sqlite:///./app.db`
- PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/dbname` (add `psycopg2-binary` to requirements)
