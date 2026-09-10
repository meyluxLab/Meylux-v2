"""Canonical candle contract for Meylux V2.

This module contains only domain contract semantics. It performs no I/O,
network access, provider interaction, database access, or wall-clock reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


SID = "CTR-V2-CANONICAL-CANDLE"
VERSION = "1.0.0"


def _decimal(value: Decimal, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    return value


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


@dataclass(frozen=True, slots=True)
class CanonicalCandle:
    """Validated, immutable canonical OHLCV candle.

    Numeric values are exact ``Decimal`` values. This contract deliberately
    does not quantize or round values: source precision is preserved and any
    provider/instrument-specific tick-size normalization belongs to the
    validation/normalization boundary.
    """

    instrument_id: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Optional[Decimal] = None
    trade_count: Optional[int] = None
    is_closed: bool = True
    provenance_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, str) or not self.instrument_id:
            raise ValueError("instrument_id must be a non-empty string")
        if not isinstance(self.timeframe, str) or not self.timeframe:
            raise ValueError("timeframe must be a non-empty string")
        if not isinstance(self.provenance_id, str) or not self.provenance_id:
            raise ValueError("provenance_id must be a non-empty string")

        open_time = _utc(self.open_time, "open_time")
        close_time = _utc(self.close_time, "close_time")
        if close_time <= open_time:
            raise ValueError("close_time must be later than open_time")

        prices = {
            "open": _decimal(self.open, "open"),
            "high": _decimal(self.high, "high"),
            "low": _decimal(self.low, "low"),
            "close": _decimal(self.close, "close"),
            "volume": _decimal(self.volume, "volume"),
        }
        if prices["open"] <= 0 or prices["high"] <= 0 or prices["low"] <= 0 or prices["close"] <= 0:
            raise ValueError("OHLC prices must be positive")
        if prices["volume"] < 0:
            raise ValueError("volume must be non-negative")
        if prices["high"] < max(prices["open"], prices["close"], prices["low"]):
            raise ValueError("high must be >= open, close, and low")
        if prices["low"] > min(prices["open"], prices["close"], prices["high"]):
            raise ValueError("low must be <= open, close, and high")

        if self.quote_volume is not None and _decimal(self.quote_volume, "quote_volume") < 0:
            raise ValueError("quote_volume must be non-negative")
        if self.trade_count is not None and (
            not isinstance(self.trade_count, int) or isinstance(self.trade_count, bool)
        ):
            raise TypeError("trade_count must be an integer")
        if self.trade_count is not None and self.trade_count < 0:
            raise ValueError("trade_count must be non-negative")
        if not isinstance(self.is_closed, bool):
            raise TypeError("is_closed must be bool")
