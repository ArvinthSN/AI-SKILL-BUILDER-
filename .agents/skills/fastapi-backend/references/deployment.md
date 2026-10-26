# Deployment

The scaffold includes a working `Dockerfile`.

```bash
docker build -t myapp .
docker run -p 8000:8000 --env-file .env myapp
```

## Production checklist
- [ ] `SECRET_KEY` and DB URL set via environment variables
- [ ] CORS limited to real frontend origins (no `*`)
- [ ] PostgreSQL instead of SQLite
- [ ] Migrations run before app start (`alembic upgrade head`)
- [ ] HTTPS via reverse proxy (Nginx) or the host platform
- [ ] `/health` endpoint monitored (included in scaffold)
- [ ] Debug off, logging on
