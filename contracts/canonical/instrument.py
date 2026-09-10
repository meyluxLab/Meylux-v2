"""Canonical instrument metadata contract for Meylux V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


SID = "CTR-V2-CANONICAL-INSTRUMENT"
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
class CanonicalInstrument:
    """Validated immutable semantic identity and metadata for an instrument."""

    instrument_id: str
    base_asset: str
    quote_asset: str
    market_type: str
    contract_type: str
    unit: str
    as_of: datetime
    price_precision: Optional[int] = None
    quantity_precision: Optional[int] = None
    contract_multiplier: Optional[Decimal] = None
    active: bool = True
    provenance_id: str = ""

    def __post_init__(self) -> None:
        for value, field in (
            (self.instrument_id, "instrument_id"),
            (self.base_asset, "base_asset"),
            (self.quote_asset, "quote_asset"),
            (self.market_type, "market_type"),
            (self.contract_type, "contract_type"),
            (self.unit, "unit"),
            (self.provenance_id, "provenance_id"),
        ):
            _text(value, field)
        _utc(self.as_of, "as_of")

        for value, field in (
            (self.price_precision, "price_precision"),
            (self.quantity_precision, "quantity_precision"),
        ):
            if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                raise TypeError(f"{field} must be an integer")
            if value is not None and value < 0:
                raise ValueError(f"{field} must be non-negative")

        if self.contract_multiplier is not None:
            multiplier = _decimal(self.contract_multiplier, "contract_multiplier")
            if multiplier <= 0:
                raise ValueError("contract_multiplier must be positive")

        if not isinstance(self.active, bool):
            raise TypeError("active must be bool")
