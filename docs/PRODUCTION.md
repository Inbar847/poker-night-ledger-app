# Production Readiness Notes

This document covers what to do before deploying Poker Night Ledger beyond a local dev machine.

---

## Backend checklist

### SECRET_KEY
The default `SECRET_KEY` in `core/config.py` is a placeholder for local development only.
It **must** be replaced with a strong random value before any deployment:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it as an environment variable or via `.env`. Never commit a real secret to the repo.

---

### CORS origins
`app/main.py` currently sets `allow_origins=["*"]`.
For production, restrict this to the actual client origin(s):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### DEBUG mode
Set `DEBUG=false` in production. This suppresses FastAPI's internal tracebacks
from being returned to the client in 500 responses.

---

### HTTPS
Run behind a reverse proxy (nginx, Caddy, etc.) that terminates TLS.
The FastAPI app should never be exposed directly on port 80/443 in production.

---

### Database connection pooling
The default SQLAlchemy engine uses a simple connection pool.
For production traffic, consider tuning:
- `pool_size` (default: 5)
- `max_overflow` (default: 10)
- `pool_pre_ping=True` to recover from stale connections

---

### Access token expiry
The default `ACCESS_TOKEN_EXPIRE_MINUTES=30` and `REFRESH_TOKEN_EXPIRE_DAYS=7`
are reasonable starting points. Adjust in `.env` based on your security requirements.

---

### Refresh token storage (future hardening)
Currently refresh tokens are stateless JWTs — there is no server-side revocation.
For MVP this is acceptable. For production with stricter logout requirements,
add a `refresh_tokens` table and revoke on logout.

---

### Logging
The app has no structured logging configured beyond FastAPI's default uvicorn logs.
For production, add a logging config that writes JSON-formatted logs and integrates
with your log aggregation stack (Datadog, Loki, CloudWatch, etc.).

---

## Database backup and recovery

### Docker Compose (local / single-host dev)

The Postgres volume is named `postgres_data` in `docker-compose.yml`.

**Manual backup:**
```bash
docker exec poker_ledger_db pg_dump -U poker_user poker_ledger > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore from backup:**
```bash
docker exec -i poker_ledger_db psql -U poker_user -d poker_ledger < backup_20240101_120000.sql
```

### Managed Postgres (recommended for production)

Use a managed provider (AWS RDS, Supabase, Render, Railway, Neon, etc.) which
provides:
- automatic daily backups with point-in-time recovery
- read replicas (if traffic grows)
- automated failover

### Migration safety

Always run `alembic upgrade head` during deployment **before** the new app version
starts serving traffic (run migrations as a pre-start step in your deploy pipeline).

Never roll back a migration that removes a column while the old app version still reads
that column — keep the old column nullable until the old code is fully retired.

---

## Scaling notes (post-MVP)

The current WebSocket implementation uses an in-memory `ConnectionManager`.
This works for a single-process deployment.

If you scale to multiple processes/replicas, you will need a shared pub/sub backend
(Redis Pub/Sub, etc.) so that a broadcast from process A reaches clients connected
to process B.

Do **not** add Redis until scaling requirements actually appear.

---

## Environment variable summary

| Variable | Required | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | Yes | dev default | PostgreSQL DSN |
| `SECRET_KEY` | Yes | — | Must be changed; 32+ random bytes |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | |
| `DEBUG` | No | `false` | Set `false` in production |
