"""Canonical trade-event contract for Meylux V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


SID = "CTR-V2-CANONICAL-TRADE"
VERSION = "1.0.0"


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def _decimal(value: Decimal, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    return value


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class CanonicalTrade:
    """Validated immutable semantic trade event, independent of provider wire IDs."""

    trade_id: str
    instrument_id: str
    timestamp: datetime
    price: Decimal
    quantity: Decimal
    aggressor_side: Optional[str] = None
    quote_quantity: Optional[Decimal] = None
    provenance_id: str = ""

    def __post_init__(self) -> None:
        _text(self.trade_id, "trade_id")
        _text(self.instrument_id, "instrument_id")
        _text(self.provenance_id, "provenance_id")
        _utc(self.timestamp, "timestamp")

        price = _decimal(self.price, "price")
        quantity = _decimal(self.quantity, "quantity")
        if price <= 0:
            raise ValueError("price must be positive")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        if self.quote_quantity is not None:
            quote_quantity = _decimal(self.quote_quantity, "quote_quantity")
            if quote_quantity <= 0:
                raise ValueError("quote_quantity must be positive")

        if self.aggressor_side is not None:
            _text(self.aggressor_side, "aggressor_side")
            if self.aggressor_side not in {"BUY", "SELL"}:
                raise ValueError("aggressor_side must be BUY or SELL")
