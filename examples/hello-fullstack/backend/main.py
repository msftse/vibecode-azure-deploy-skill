"""hello-fullstack backend.

GET /api/hello → increments a counter row in Postgres, returns {count, timestamp}.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI(title="hello-fullstack")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise HTTPException(500, "DATABASE_URL not set")
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with _pool.acquire() as conn:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS counter ("
                "  id INT PRIMARY KEY,"
                "  value BIGINT NOT NULL"
                ")"
            )
            await conn.execute(
                "INSERT INTO counter (id, value) VALUES (1, 0) "
                "ON CONFLICT (id) DO NOTHING"
            )
    return _pool


@app.get("/api/hello")
async def hello() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE counter SET value = value + 1 WHERE id = 1 RETURNING value"
        )
    return {
        "count": row["value"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
