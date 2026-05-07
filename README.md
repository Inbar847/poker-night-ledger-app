# Poker Night Ledger

A full-stack mobile app for managing real-world poker nights.
Track buy-ins, shared expenses, final chip counts, and settlement — in real time.

---

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node 18+
- [Expo CLI](https://docs.expo.dev/get-started/installation/) (`npm install -g expo-cli`)

---

## Repository layout

```text
poker-night-ledger/
├─ mobile/          React Native + Expo + TypeScript
├─ backend/         FastAPI + SQLAlchemy + Alembic + PostgreSQL
├─ docs/            Product spec, architecture, plan
├─ docker-compose.yml
├─ CLAUDE.md
└─ README.md
```

---

## Quick start

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

Postgres will be available at `localhost:5432`, database `poker_ledger`.

### 2. Set up the backend

```bash
cd backend
cp .env.example .env          # edit SECRET_KEY before use
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`

Interactive docs: `http://localhost:8000/docs`

### 3. (Optional) Load demo data

```bash
cd backend
python scripts/seed_demo.py
```

Creates demo users (`alice@demo.com`, `bob@demo.com`, `carol@demo.com`, password `demo1234`)
and a fully-closed demo game with buy-ins, expenses, and settlement.

### 4. Set up the mobile app

```bash
cd mobile
cp .env.example .env.local    # set EXPO_PUBLIC_API_URL if needed
npm install
npx expo start
```

Then press `i` for iOS simulator, `a` for Android emulator, or scan the QR code with Expo Go.

---

## Running backend tests

```bash
cd backend
pytest
```

Tests use an in-memory SQLite database — no running Postgres required.

---

## Linting (backend)

```bash
cd backend
pip install ruff
ruff check app/ tests/
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | dev default | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | JWT signing secret — **change before any deployment** |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | |
| `DEBUG` | No | `false` | Enable debug mode |

### Mobile (`mobile/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `EXPO_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## Documentation

| File | Contents |
|---|---|
| `docs/PLAN.md` | Stage-by-stage build roadmap |
| `docs/PRODUCT_SPEC.md` | Full product specification |
| `docs/ARCHITECTURE.md` | System architecture and domain model |
| `docs/PRODUCTION.md` | Production hardening and DB backup notes |
| `docs/RELEASE_CHECKLIST.md` | Pre-release QA checklist |

---

## Current stage

**Stage 9 (MVP complete)** — All stages 0–9 implemented.

Stages completed:
- Stage 0: Monorepo bootstrap
- Stage 1: Backend auth and user profiles
- Stage 2: Game creation, participants, invite flows
- Stage 3: Live ledger — buy-ins, expenses, final stacks
- Stage 4: Settlement engine and audit breakdown
- Stage 5: Realtime WebSocket transport
- Stage 6: Mobile auth and profile flows
- Stage 7: Mobile game flows and realtime integration
- Stage 8: History, game details, personal statistics
- Stage 9: Hardening, QA, env examples, seed data, release docs

See `docs/PLAN.md` for the full roadmap and stage boundaries.
