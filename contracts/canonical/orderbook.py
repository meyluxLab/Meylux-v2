"""Canonical order-book snapshot contract for Meylux V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


SID = "CTR-V2-CANONICAL-ORDERBOOK"
VERSION = "1.0.0"


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _level(level: object, side: str, index: int) -> tuple[Decimal, Decimal]:
    if not isinstance(level, tuple) or len(level) != 2:
        raise TypeError(f"{side}[{index}] must be a (price, quantity) tuple")
    price, quantity = level
    if not isinstance(price, Decimal) or not isinstance(quantity, Decimal):
        raise TypeError(f"{side}[{index}] price and quantity must be Decimal")
    if not price.is_finite() or not quantity.is_finite():
        raise ValueError(f"{side}[{index}] price and quantity must be finite")
    if price <= 0 or quantity <= 0:
        raise ValueError(f"{side}[{index}] price and quantity must be positive")
    return price, quantity


def _validate_levels(levels: tuple[tuple[Decimal, Decimal], ...], side: str, descending: bool) -> None:
    if not isinstance(levels, tuple):
        raise TypeError(f"{side} must be a tuple")
    previous = None
    seen: set[Decimal] = set()
    for index, level in enumerate(levels):
        price, _ = _level(level, side, index)
        if price in seen:
            raise ValueError(f"{side} contains duplicate price levels")
        seen.add(price)
        if previous is not None and ((descending and price >= previous) or (not descending and price <= previous)):
            order = "strictly descending" if descending else "strictly ascending"
            raise ValueError(f"{side} prices must be {order}")
        previous = price


@dataclass(frozen=True, slots=True)
class CanonicalOrderBook:
    """Validated immutable canonical order-book snapshot.

    Levels are ``(price, quantity)`` pairs. Provider sequence numbers and wire
    event IDs are deliberately excluded from this provider-neutral contract.
    """

    instrument_id: str
    timestamp: datetime
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]
    provenance_id: str = ""

    def __post_init__(self) -> None:
        _text(self.instrument_id, "instrument_id")
        _text(self.provenance_id, "provenance_id")
        _utc(self.timestamp, "timestamp")
        _validate_levels(self.bids, "bids", descending=True)
        _validate_levels(self.asks, "asks", descending=False)
        if not self.bids and not self.asks:
            raise ValueError("order book must contain at least one level")
        if self.bids and self.asks and self.bids[0][0] >= self.asks[0][0]:
            raise ValueError("best bid must be lower than best ask")
