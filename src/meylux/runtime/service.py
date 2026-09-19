"""Phase-4 runtime entrypoint for API and quantitative worker services."""
from __future__ import annotations
import asyncio,os
import asyncpg
import redis.asyncio as redis
from decimal import Decimal
from meylux.api import QuantitativeAPI
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.runtime.http import serve_api
from meylux.runtime.quant_worker import QuantWorkerHandler
from meylux.queue import AsyncWorker,QueuePolicy,RedisQueue
from meylux.orchestration import QuantOrchestrationConfig
from meylux.quantitative.regime_venue import RegimeConfig

def _required(n:str)->str:
    v=os.environ.get(n)
    if not v: raise RuntimeError(f"{n} is required")
    return v

def _config()->QuantOrchestrationConfig:
    regime=RegimeConfig(
        int(os.environ.get("MEYLUX_TREND_LOOKBACK","2")),
        int(os.environ.get("MEYLUX_MOMENTUM_LOOKBACK","2")),
        Decimal(os.environ.get("MEYLUX_TREND_ENTRY_THRESHOLD","0.10")),
        Decimal(os.environ.get("MEYLUX_TREND_EXIT_THRESHOLD","0.05")),
        Decimal(os.environ.get("MEYLUX_MOMENTUM_ENTRY_THRESHOLD","0.10")),
        Decimal(os.environ.get("MEYLUX_MOMENTUM_EXIT_THRESHOLD","0.05")),
        os.environ.get("MEYLUX_REGIME_VERSION","1.0.0"),
    )
    return QuantOrchestrationConfig(
        regime,
        int(os.environ.get("MEYLUX_EMA_PERIOD","20")),
        int(os.environ.get("MEYLUX_RSI_PERIOD","14")),
        int(os.environ.get("MEYLUX_ATR_PERIOD","14")),
        os.environ.get("MEYLUX_QUANT_CONFIG_VERSION","1.0.0"),
    )

async def main():
    service=os.environ.get("MEYLUX_SERVICE","")
    if service in {"collector","worker-ai"}:
        print(f"meylux-v2 foundation service started: {service}", flush=True)
        while True:
            await asyncio.sleep(3600)
    if service not in {"api","worker-quant"}:
        raise SystemExit(f"unsupported Phase-4 service: {service!r}")
    pool=await asyncpg.create_pool(
        host=_required("MEYLUX_DB_HOST"),port=int(os.environ.get("MEYLUX_DB_PORT","5432")),
        database=_required("MEYLUX_DB_NAME"),user=_required("MEYLUX_DB_USER"),
        password=_required("MEYLUX_DB_PASSWORD"),min_size=1,max_size=2)
    client=redis.from_url(os.environ.get("MEYLUX_REDIS_URL","redis://redis:6379/0"),decode_responses=False)
    try:
        if service=="api":
            async with pool.acquire() as conn:
                await serve_api(os.environ.get("MEYLUX_API_HOST","0.0.0.0"),
                                int(os.environ.get("MEYLUX_API_PORT","8080")),
                                QuantitativeAPI(QuantitativePersistence(conn)))
        else:
            async with pool.acquire() as conn:
                policy=QueuePolicy(
                    "quantitative-candle-close","ROL-V2-002","canonical-event-worker",
                    "worker-quant","execute deterministic quantitative orchestration from closed canonical candles",
                    "CTR-P4-QUANT-CANDLE-CLOSE-1.0","quantitative-candle-close",
                    10000,1,3,30.0,0.1,86400)
                queue=RedisQueue(client,policy,"quantitative-workers")
                await AsyncWorker(
                    queue,QuantWorkerHandler(QuantitativePersistence(conn),_config()),
                    consumer="worker-quant").run()
    finally:
        await client.aclose()
        await pool.close()

if __name__=="__main__":
    asyncio.run(main())
