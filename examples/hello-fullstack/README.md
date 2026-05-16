# hello-fullstack

A minimal Next.js + FastAPI + Postgres app you can deploy to Azure in 60 seconds.

## Stack

- **frontend/** — Next.js 14 (app router). Fetches `/api/hello` from the backend.
- **backend/** — FastAPI + asyncpg. Increments a counter row in Postgres, returns `{count, timestamp}`.
- **Postgres Flexible Server** — provisioned by `deploy-azure db add postgres`.

## Deploy

Prereqs: `az login` (or service-principal env vars), Docker running, the
`deploy-azure` Hermes skill installed (it's on your PATH via `~/.hermes/skills/devops/deploy-azure/scripts/`).

```bash
cd hello-fullstack

# 1. provision Postgres (3-5 min)
deploy-azure db add postgres

# 2. build + push + deploy everything
deploy-azure up

# 3. open it
deploy-azure status
```

That's it. Re-running `deploy-azure up` is a no-op if nothing changed; if
you push a new commit, it rebuilds + ships a new ACA revision in ~20s.

## Local dev

```bash
# backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://localhost/hello uvicorn main:app --reload

# frontend (in another shell)
cd frontend
npm install
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev
```

## Teardown

```bash
deploy-azure destroy
```
