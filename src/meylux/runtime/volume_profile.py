"""Explicit-interval P4 Volume Profile runtime boundary.

The caller supplies the complete profile interval. No calendar/session boundary
is discovered or inferred here. The runtime consumes persisted validated
CanonicalTrade evidence and writes only through the existing append-only P4
Volume Profile persistence surface.
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from meylux.persistence.quantitative import QuantitativePersistence
from meylux.quantitative.volume_orderflow_derivatives import (
    VolumeProfileConfig,
    VolumeProfileEngine,
)


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _utc(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field} must be UTC")
    return parsed.astimezone(timezone.utc)


def _finite_decimal(name: str) -> Decimal:
    value = Decimal(_required(name))
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


@dataclass(frozen=True, slots=True)
class VolumeProfileRequest:
    symbol: str
    timeframe: str
    interval_start: datetime
    interval_end: datetime
    price_bin_size: Decimal
    hvn_threshold: Decimal
    lvn_threshold: Decimal
    configuration_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.symbol or not self.timeframe:
            raise ValueError("symbol and timeframe are required")
        if self.interval_start.tzinfo is None or self.interval_start.utcoffset() != timezone.utc.utcoffset(self.interval_start):
            raise ValueError("interval_start must be UTC")
        if self.interval_end.tzinfo is None or self.interval_end.utcoffset() != timezone.utc.utcoffset(self.interval_end):
            raise ValueError("interval_end must be UTC")
        if self.interval_end <= self.interval_start:
            raise ValueError("interval_end must be after interval_start")
        if not self.price_bin_size.is_finite() or self.price_bin_size <= 0:
            raise ValueError("price_bin_size must be finite and positive")
        if not self.hvn_threshold.is_finite() or self.hvn_threshold < 0:
            raise ValueError("hvn_threshold must be finite and non-negative")
        if not self.lvn_threshold.is_finite() or self.lvn_threshold < 0:
            raise ValueError("lvn_threshold must be finite and non-negative")
        if not self.configuration_version:
            raise ValueError("configuration_version must be non-empty")


async def execute(connection: Any, request: VolumeProfileRequest) -> int:
    persistence = QuantitativePersistence(connection)
    trades, source_record_ids = await persistence.fetch_canonical_trade_lineage(
        request.symbol,
        request.interval_start,
        request.interval_end,
    )
    analysis = VolumeProfileEngine().analyze(
        trades,
        request.interval_start,
        request.interval_end,
        VolumeProfileConfig(
            request.price_bin_size,
            request.hvn_threshold,
            request.lvn_threshold,
        ),
    )
    return await persistence.persist_volume_profile(
        symbol=request.symbol,
        timeframe=request.timeframe,
        analysis=analysis,
        trades=trades,
        configuration_version=request.configuration_version,
        source_record_ids=source_record_ids,
    )


def request_from_environment() -> VolumeProfileRequest:
    return VolumeProfileRequest(
        symbol=_required("MEYLUX_VOLUME_PROFILE_SYMBOL"),
        timeframe=_required("MEYLUX_VOLUME_PROFILE_TIMEFRAME"),
        interval_start=_utc(
            _required("MEYLUX_VOLUME_PROFILE_INTERVAL_START"),
            "MEYLUX_VOLUME_PROFILE_INTERVAL_START",
        ),
        interval_end=_utc(
            _required("MEYLUX_VOLUME_PROFILE_INTERVAL_END"),
            "MEYLUX_VOLUME_PROFILE_INTERVAL_END",
        ),
        price_bin_size=_finite_decimal("MEYLUX_VOLUME_PROFILE_PRICE_BIN_SIZE"),
        hvn_threshold=_finite_decimal("MEYLUX_VOLUME_PROFILE_HVN_THRESHOLD"),
        lvn_threshold=_finite_decimal("MEYLUX_VOLUME_PROFILE_LVN_THRESHOLD"),
        configuration_version=os.environ.get("MEYLUX_VOLUME_PROFILE_CONFIG_VERSION", "1.0.0"),
    )


async def main() -> None:
    import asyncpg

    request = request_from_environment()
    connection = await asyncpg.connect(
        host=_required("MEYLUX_DB_HOST"),
        port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
        database=_required("MEYLUX_DB_NAME"),
        user=_required("MEYLUX_DB_USER"),
        password=_required("MEYLUX_DB_PASSWORD"),
        timeout=10,
        command_timeout=30,
    )
    try:
        inserted = await execute(connection, request)
        print(
            f"volume_profile_persisted symbol={request.symbol} timeframe={request.timeframe} "
            f"interval_start={request.interval_start.isoformat()} "
            f"interval_end={request.interval_end.isoformat()} inserted={inserted}",
            flush=True,
        )
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
