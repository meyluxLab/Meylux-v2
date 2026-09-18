"""One-shot P3-008 canonical-event outbox relay runtime."""
from __future__ import annotations
import asyncio
import os
import asyncpg
import redis.asyncio as redis
from meylux.persistence.canonical import CanonicalPersistence
from meylux.persistence.event_handoff import CanonicalEventRelay

def _required(name:str)->str:
    value=os.environ.get(name)
    if not value: raise RuntimeError(f"{name} is required")
    return value

async def main()->int:
    pool=await asyncpg.create_pool(
        host=_required("MEYLUX_DB_HOST"),
        port=int(os.environ.get("MEYLUX_DB_PORT","5432")),
        database=_required("MEYLUX_DB_NAME"),
        user=_required("MEYLUX_DB_USER"),
        password=_required("MEYLUX_DB_PASSWORD"),
        min_size=1,max_size=2,
    )
    client=redis.from_url(os.environ.get("MEYLUX_REDIS_URL","redis://redis:6379/0"),decode_responses=False)
    try:
        async with pool.acquire() as connection:
            persistence=CanonicalPersistence(connection)
            count=await CanonicalEventRelay(persistence,client,max_batch=100).publish_pending()
            print(f"canonical event relay: published={count}",flush=True)
            return 0
    finally:
        await client.aclose()
        await pool.close()

if __name__=="__main__":
    raise SystemExit(asyncio.run(main()))
