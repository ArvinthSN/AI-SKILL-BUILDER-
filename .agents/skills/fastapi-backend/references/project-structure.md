# Project Structure

```
myapp/
├── app/
│   ├── main.py            # creates app, registers routers, middleware
│   ├── core/
│   │   └── config.py      # Settings (pydantic-settings)
│   ├── db.py              # engine, SessionLocal, Base, get_db
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic models
│   ├── services/          # business logic
│   └── routers/           # endpoint groups
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
└── requirements.txt
```

## Where does new code go?

| Task | Location |
|---|---|
| New table | `models/` |
| New request/response shape | `schemas/` |
| Query or rule | `services/` |
| New endpoint | `routers/` |
| New setting | `core/config.py` + `.env.example` |
| Password hashing / JWT | `core/security.py` (see `auth-jwt.md`) |
