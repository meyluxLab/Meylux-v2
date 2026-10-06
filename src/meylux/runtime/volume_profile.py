"""Explicit-interval P4 Volume Profile runtime path over persisted CanonicalTrade evidence."""
from __future__ import annotations
import asyncio, json, os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping
from contracts.canonical.trade import CanonicalTrade
from contracts.quantitative.volume_profile import VolumeProfileConfig
from meylux.persistence.quantitative import QuantitativePersistence

def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value: raise RuntimeError(f"{name} is required")
    return value

def _utc(value: str, field: str) -> datetime:
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc: raise ValueError(f"{field} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field} must be UTC")
    return parsed.astimezone(timezone.utc)

def _trade(row: Mapping[str, Any]) -> CanonicalTrade:
    payload = row["payload_json"]
    if isinstance(payload, str): payload = json.loads(payload)
    if not isinstance(payload, Mapping): raise TypeError("canonical trade payload_json must be an object")
    return CanonicalTrade(
        str(payload["trade_id"]), str(payload["instrument_id"]), _utc(str(payload["timestamp"]), "trade.timestamp"),
        Decimal(str(payload["price"])), Decimal(str(payload["quantity"])),
        payload.get("aggressor_side"),
        None if payload.get("quote_quantity") is None else Decimal(str(payload["quote_quantity"])),
        str(payload["provenance_id"]),
    )

async def run_volume_profile(conn: Any, *, symbol: str, timeframe: str, interval_start: datetime, interval_end: datetime, config: VolumeProfileConfig) -> int:
    rows = await conn.fetch(
        "SELECT payload_json FROM meylux.canonical_trades WHERE instrument_id=$1 AND event_time >= $2 AND event_time < $3 ORDER BY event_time,record_id",
        symbol, interval_start, interval_end,
    )
    trades = tuple(_trade(row) for row in rows)
    return await QuantitativePersistence(conn).persist_volume_profile(
        symbol=symbol, timeframe=timeframe, trades=trades, interval_start=interval_start, interval_end=interval_end, config=config,
    )

async def main() -> int:
    import asyncpg
    symbol, timeframe = _required("MEYLUX_VOLUME_PROFILE_SYMBOL"), _required("MEYLUX_VOLUME_PROFILE_TIMEFRAME")
    start, end = _utc(_required("MEYLUX_VOLUME_PROFILE_INTERVAL_START"), "MEYLUX_VOLUME_PROFILE_INTERVAL_START"), _utc(_required("MEYLUX_VOLUME_PROFILE_INTERVAL_END"), "MEYLUX_VOLUME_PROFILE_INTERVAL_END")
    config = VolumeProfileConfig(
        Decimal(_required("MEYLUX_VOLUME_PROFILE_PRICE_BIN_SIZE")),
        None if os.environ.get("MEYLUX_VOLUME_PROFILE_HVN_THRESHOLD") is None else Decimal(os.environ["MEYLUX_VOLUME_PROFILE_HVN_THRESHOLD"]),
        None if os.environ.get("MEYLUX_VOLUME_PROFILE_LVN_THRESHOLD") is None else Decimal(os.environ["MEYLUX_VOLUME_PROFILE_LVN_THRESHOLD"]),
    )
    conn = await asyncpg.connect(host=_required("MEYLUX_DB_HOST"), port=int(os.environ.get("MEYLUX_DB_PORT", "5432")), database=_required("MEYLUX_DB_NAME"), user=_required("MEYLUX_DB_USER"), password=_required("MEYLUX_DB_PASSWORD"))
    try:
        inserted = await run_volume_profile(conn, symbol=symbol, timeframe=timeframe, interval_start=start, interval_end=end, config=config)
        rows = await conn.fetch("SELECT record_id,status,reason,session_start,session_end,source_ref,venue_context,knowledge_time,payload_json FROM meylux.volume_profile_sessions WHERE symbol=$1 AND timeframe=$2 AND session_start=$3 AND session_end=$4 ORDER BY record_id", symbol, timeframe, start, end)
        print(f"volume-profile: inserted={inserted} rows={len(rows)} interval={start.isoformat()}..{end.isoformat()}")
        for row in rows: print(json.dumps({k: row[k] for k in ("record_id","status","reason","session_start","session_end","source_ref","venue_context","knowledge_time")}, default=str, sort_keys=True))
        return 0
    finally:
        await conn.close()

if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
