"""Deterministic Volume Profile, Order Flow and Derivatives engines for Phase 4 Step P4-004.

The module is deliberately pure: it consumes validated canonical contracts plus
explicit configuration/temporal boundaries and returns immutable quantitative
facts. It never infers missing market evidence and never reaches provider,
network, filesystem, clock, database, or runtime state.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from typing import Iterable, Mapping, Sequence

from contracts.canonical.derivatives import CanonicalDerivatives
from contracts.canonical.orderbook import CanonicalOrderBook
from contracts.canonical.trade import CanonicalTrade
from contracts.quantitative.base import CalculationResult, CalculationStatus, QuantitativeContext
from contracts.quantitative.order_flow import OrderFlowResult
from contracts.quantitative.volume_profile import VolumeProfileResult

SEMANTIC_VERSION = "1.0.0"
VALUE_AREA_TARGET = Decimal("0.70")


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def _finite_decimal(value: object, field: str, *, positive: bool = False, non_negative: bool = False) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field} must not be bool or float")
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{field} must be positive")
    if non_negative and value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _ctx(context: QuantitativeContext | None) -> QuantitativeContext | None:
    if context is not None and not isinstance(context, QuantitativeContext):
        raise TypeError("context must be QuantitativeContext or None")
    return context


def _result(
    value: Decimal | None,
    status: CalculationStatus,
    reason: str,
    context: QuantitativeContext | None,
) -> CalculationResult:
    return CalculationResult(value, status, reason, context)


def _vp(metric: str, result: CalculationResult) -> VolumeProfileResult:
    return VolumeProfileResult(metric, result, SEMANTIC_VERSION)


def _of(metric: str, result: CalculationResult) -> OrderFlowResult:
    return OrderFlowResult(metric, result, SEMANTIC_VERSION)


@dataclass(frozen=True, slots=True)
class VolumeProfileConfig:
    price_bin_size: Decimal
    hvn_threshold: Decimal | None = None
    lvn_threshold: Decimal | None = None

    def __post_init__(self) -> None:
        _finite_decimal(self.price_bin_size, "price_bin_size", positive=True)
        if self.hvn_threshold is not None:
            _finite_decimal(self.hvn_threshold, "hvn_threshold", non_negative=True)
        if self.lvn_threshold is not None:
            _finite_decimal(self.lvn_threshold, "lvn_threshold", non_negative=True)


@dataclass(frozen=True, slots=True)
class VolumeProfileAnalysis:
    interval_start: datetime
    interval_end: datetime
    price_bin_size: Decimal
    bins: tuple[tuple[Decimal, Decimal], ...]
    poc: VolumeProfileResult
    value_area_low: VolumeProfileResult
    value_area_high: VolumeProfileResult
    hvn_bins: tuple[Decimal, ...]
    lvn_bins: tuple[Decimal, ...]
    hvn: VolumeProfileResult
    lvn: VolumeProfileResult
    selected_value_area_bins: tuple[Decimal, ...]
    context: QuantitativeContext | None = None


class VolumeProfileEngine:
    calculation_version = SEMANTIC_VERSION

    def analyze(
        self,
        trades: Iterable[CanonicalTrade],
        interval_start: datetime,
        interval_end: datetime,
        config: VolumeProfileConfig,
        context: QuantitativeContext | None = None,
    ) -> VolumeProfileAnalysis:
        start = _utc(interval_start, "interval_start")
        end = _utc(interval_end, "interval_end")
        if end <= start:
            raise ValueError("interval_end must be after interval_start")
        if not isinstance(config, VolumeProfileConfig):
            raise TypeError("config must be VolumeProfileConfig")
        context = _ctx(context)
        xs = tuple(trades)
        if any(not isinstance(t, CanonicalTrade) for t in xs):
            raise TypeError("trades must contain CanonicalTrade instances")
        if any(t.instrument_id != xs[0].instrument_id for t in xs[1:]) if xs else False:
            raise ValueError("profile trades must belong to one instrument")
        selected = tuple(t for t in xs if start <= t.timestamp < end)
        if not selected:
            unavailable = _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "empty_profile_interval", context)
            return VolumeProfileAnalysis(
                start, end, config.price_bin_size, (), _vp("POC", unavailable),
                _vp("VAL", unavailable), _vp("VAH", unavailable), (), (),
                _vp("HVN", _result(None, CalculationStatus.UNAVAILABLE, "missing_hvn_threshold", context)),
                _vp("LVN", _result(None, CalculationStatus.UNAVAILABLE, "missing_lvn_threshold", context)),
                (), context,
            )

        bins_map: dict[Decimal, Decimal] = {}
        for trade in selected:
            lower = (trade.price / config.price_bin_size).to_integral_value(rounding=ROUND_FLOOR) * config.price_bin_size
            bins_map[lower] = bins_map.get(lower, Decimal("0")) + trade.quantity
        lowest = min(bins_map)
        highest = max(bins_map)
        contiguous: list[tuple[Decimal, Decimal]] = []
        cursor = lowest
        while cursor <= highest:
            contiguous.append((cursor, bins_map.get(cursor, Decimal("0"))))
            cursor += config.price_bin_size
        bins = tuple(contiguous)
        max_volume = max(v for _, v in bins)
        poc_price = min(p for p, v in bins if v == max_volume)
        poc = _vp("POC", _result(poc_price, CalculationStatus.VALID, "maximum_volume_lowest_price_tie_break", context))

        index = next(i for i, (p, _) in enumerate(bins) if p == poc_price)
        total = sum((v for _, v in bins), Decimal("0"))
        target = total * VALUE_AREA_TARGET
        accumulated = max_volume
        selected_indices = [index]
        left = index - 1
        right = index + 1
        while accumulated < target:
            if left < 0 and right >= len(bins):
                break
            if left < 0:
                chosen = right
            elif right >= len(bins):
                chosen = left
            else:
                left_volume = bins[left][1]
                right_volume = bins[right][1]
                chosen = left if left_volume >= right_volume else right
            selected_indices.append(chosen)
            accumulated += bins[chosen][1]
            if chosen == left:
                left -= 1
            else:
                right += 1
        selected_indices.sort()
        selected_prices = tuple(bins[i][0] for i in selected_indices)
        val = bins[selected_indices[0]][0]
        vah = bins[selected_indices[-1]][0] + config.price_bin_size
        val_result = _vp("VAL", _result(val, CalculationStatus.VALID, "lowest_selected_bin_lower_bound", context))
        vah_result = _vp("VAH", _result(vah, CalculationStatus.VALID, "highest_selected_bin_upper_boundary", context))

        hvn_bins: tuple[Decimal, ...] = ()
        lvn_bins: tuple[Decimal, ...] = ()
        if config.hvn_threshold is not None:
            hvn_bins = tuple(p for p, v in bins if v > 0 and v / max_volume >= config.hvn_threshold)
        if config.lvn_threshold is not None:
            lvn_bins = tuple(p for p, v in bins if v > 0 and v / max_volume <= config.lvn_threshold)
        hvn_result = _vp(
            "HVN",
            _result(
                Decimal(len(hvn_bins)),
                CalculationStatus.VALID,
                "count_of_bins_meeting_hvn_ratio" if config.hvn_threshold is not None else "unreachable",
                context,
            ) if config.hvn_threshold is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_hvn_threshold", context),
        )
        lvn_result = _vp(
            "LVN",
            _result(
                Decimal(len(lvn_bins)),
                CalculationStatus.VALID,
                "count_of_bins_meeting_lvn_ratio" if config.lvn_threshold is not None else "unreachable",
                context,
            ) if config.lvn_threshold is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_lvn_threshold", context),
        )
        return VolumeProfileAnalysis(
            start, end, config.price_bin_size, bins, poc, val_result, vah_result,
            hvn_bins, lvn_bins, hvn_result, lvn_result, selected_prices, context,
        )


@dataclass(frozen=True, slots=True)
class ClosedBar:
    start_time: datetime
    end_time: datetime
    trades: tuple[CanonicalTrade, ...]
    is_closed: bool = True

    def __post_init__(self) -> None:
        _utc(self.start_time, "start_time")
        _utc(self.end_time, "end_time")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if not self.is_closed:
            raise ValueError("ClosedBar requires is_closed=True")
        if any(not isinstance(t, CanonicalTrade) for t in self.trades):
            raise TypeError("trades must contain CanonicalTrade instances")


@dataclass(frozen=True, slots=True)
class OrderFlowConfig:
    imbalance_ratio_threshold: Decimal
    absorption_volume_threshold: Decimal
    max_price_displacement: Decimal

    def __post_init__(self) -> None:
        _finite_decimal(self.imbalance_ratio_threshold, "imbalance_ratio_threshold", positive=True)
        if self.imbalance_ratio_threshold <= Decimal("1"):
            raise ValueError("imbalance_ratio_threshold must be > 1")
        _finite_decimal(self.absorption_volume_threshold, "absorption_volume_threshold", positive=True)
        _finite_decimal(self.max_price_displacement, "max_price_displacement", non_negative=True)


class OrderFlowEngine:
    calculation_version = SEMANTIC_VERSION

    def bar_delta(
        self,
        trades: Sequence[CanonicalTrade],
        context: QuantitativeContext | None = None,
    ) -> OrderFlowResult:
        context = _ctx(context)
        xs = tuple(trades)
        if any(not isinstance(t, CanonicalTrade) for t in xs):
            raise TypeError("trades must contain CanonicalTrade instances")
        if not xs:
            return _of("BAR_DELTA", _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "empty_trade_set", context))
        if any(t.aggressor_side is None for t in xs):
            return _of("BAR_DELTA", _result(None, CalculationStatus.UNAVAILABLE, "missing_aggressor_evidence", context))
        buy = sum((t.quantity for t in xs if t.aggressor_side == "BUY"), Decimal("0"))
        sell = sum((t.quantity for t in xs if t.aggressor_side == "SELL"), Decimal("0"))
        return _of("BAR_DELTA", _result(buy - sell, CalculationStatus.VALID, "buy_positive_sell_negative", context))

    def cvd(
        self,
        bars: Sequence[ClosedBar],
        context: QuantitativeContext | None = None,
    ) -> tuple[OrderFlowResult, ...]:
        context = _ctx(context)
        xs = tuple(bars)
        previous_end: datetime | None = None
        running: Decimal | None = None
        out: list[OrderFlowResult] = []
        for bar in xs:
            if previous_end is not None and bar.start_time < previous_end:
                raise ValueError("closed bars must be explicitly ordered without temporal overlap")
            previous_end = bar.end_time
            delta = self.bar_delta(bar.trades, context).result
            if delta.status is not CalculationStatus.VALID:
                out.append(_of("CVD", _result(None, delta.status, "bar_delta_unavailable; cumulative_state_not_advanced", context)))
                continue
            running = delta.value if running is None else running + delta.value
            out.append(_of("CVD", _result(running, CalculationStatus.VALID, "cumulative_valid_closed_bar_delta", context)))
        return tuple(out)

    def imbalance(
        self,
        dominant_volume: Decimal,
        opposing_volume: Decimal,
        config: OrderFlowConfig,
        context: QuantitativeContext | None = None,
    ) -> OrderFlowResult:
        context = _ctx(context)
        dominant = _finite_decimal(dominant_volume, "dominant_volume", non_negative=True)
        opposing = _finite_decimal(opposing_volume, "opposing_volume", non_negative=True)
        if opposing == 0:
            return _of("IMBALANCE", _result(None, CalculationStatus.UNAVAILABLE, "zero_opposing_volume", context))
        ratio = dominant / opposing
        qualified = ratio >= config.imbalance_ratio_threshold
        return _of(
            "IMBALANCE_RATIO",
            _result(ratio, CalculationStatus.VALID, "threshold_qualified" if qualified else "threshold_not_qualified", context),
        )

    def absorption(
        self,
        trades: Sequence[CanonicalTrade],
        order_books: Sequence[CanonicalOrderBook],
        observation_start: datetime,
        observation_end: datetime,
        observed_price: Decimal,
        aggressor_side: str,
        config: OrderFlowConfig,
        context: QuantitativeContext | None = None,
    ) -> OrderFlowResult:
        context = _ctx(context)
        start = _utc(observation_start, "observation_start")
        end = _utc(observation_end, "observation_end")
        if end <= start:
            return _of("ABSORPTION", _result(None, CalculationStatus.INVALID_INPUT, "invalid_observation_window", context))
        price = _finite_decimal(observed_price, "observed_price", positive=True)
        if aggressor_side not in {"BUY", "SELL"}:
            raise ValueError("aggressor_side must be BUY or SELL")
        xs = tuple(trades)
        books = tuple(order_books)
        if any(not isinstance(t, CanonicalTrade) for t in xs):
            raise TypeError("trades must contain CanonicalTrade instances")
        if any(not isinstance(b, CanonicalOrderBook) for b in books):
            raise TypeError("order_books must contain CanonicalOrderBook instances")
        aggressive = tuple(t for t in xs if start <= t.timestamp <= end and t.aggressor_side == aggressor_side and t.price == price)
        if not aggressive or not books:
            return _of("ABSORPTION", _result(None, CalculationStatus.UNAVAILABLE, "missing_trade_or_order_book_evidence", context))
        aggressive_volume = sum((t.quantity for t in aggressive), Decimal("0"))
        if aggressive_volume < config.absorption_volume_threshold:
            return _of("ABSORPTION", _result(Decimal("0"), CalculationStatus.VALID, "aggressive_volume_below_threshold", context))
        contemporaneous = tuple(b for b in books if start <= b.timestamp <= end)
        if not contemporaneous:
            return _of("ABSORPTION", _result(None, CalculationStatus.UNAVAILABLE, "missing_contemporaneous_order_book", context))
        resting = Decimal("0")
        for book in contemporaneous:
            levels = book.asks if aggressor_side == "BUY" else book.bids
            for level_price, quantity in levels:
                if level_price == price:
                    resting = max(resting, quantity)
        if resting <= 0:
            return _of("ABSORPTION", _result(None, CalculationStatus.UNAVAILABLE, "missing_opposite_resting_quantity_at_price", context))
        max_displacement = max((abs(t.price - price) for t in xs if start <= t.timestamp <= end), default=Decimal("0"))
        if max_displacement > config.max_price_displacement:
            return _of("ABSORPTION", _result(Decimal("0"), CalculationStatus.VALID, "price_traversal_exceeded_configured_displacement", context))
        return _of("ABSORPTION", _result(Decimal("1"), CalculationStatus.VALID, "aggressive_trade_and_contemporaneous_book_evidence", context))


class DerivativesEngine:
    calculation_version = SEMANTIC_VERSION

    def analyze(
        self,
        current: CanonicalDerivatives,
        prior: CanonicalDerivatives | None = None,
        prior_velocity: Decimal | None = None,
        context: QuantitativeContext | None = None,
    ) -> Mapping[str, CalculationResult]:
        context = _ctx(context)
        if not isinstance(current, CanonicalDerivatives):
            raise TypeError("current must be CanonicalDerivatives")
        if prior is not None and not isinstance(prior, CanonicalDerivatives):
            raise TypeError("prior must be CanonicalDerivatives or None")
        if prior is not None and prior.instrument_id != current.instrument_id:
            raise ValueError("current and prior derivatives must use the same instrument")
        if prior_velocity is not None:
            _finite_decimal(prior_velocity, "prior_velocity")
        out: dict[str, CalculationResult] = {}
        out["FUNDING_RATE"] = (
            _result(current.funding_rate, CalculationStatus.VALID, "canonical_funding_rate", context)
            if current.funding_rate is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_canonical_funding_rate", context)
        )
        out["FUNDING_CHANGE"] = (
            _result(current.funding_change, CalculationStatus.VALID, "canonical_funding_change", context)
            if current.funding_change is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_canonical_funding_change", context)
        )
        if current.funding_velocity is not None:
            out["FUNDING_VELOCITY"] = _result(current.funding_velocity, CalculationStatus.VALID, "canonical_funding_velocity", context)
        elif prior is None or prior.funding_rate is None or current.funding_rate is None:
            out["FUNDING_VELOCITY"] = _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "missing_prior_funding_observation", context)
        else:
            elapsed = Decimal(str((current.timestamp - prior.timestamp).total_seconds()))
            if elapsed <= 0:
                out["FUNDING_VELOCITY"] = _result(None, CalculationStatus.INVALID_INPUT, "non_positive_derivative_elapsed_time", context)
            else:
                out["FUNDING_VELOCITY"] = _result((current.funding_rate - prior.funding_rate) / elapsed, CalculationStatus.VALID, "derived_from_ordered_canonical_observations", context)

        velocity = out["FUNDING_VELOCITY"].value
        if velocity is None or velocity is not None and out["FUNDING_VELOCITY"].status is not CalculationStatus.VALID:
            out["FUNDING_ACCELERATION"] = _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "missing_prior_velocity_observation", context)
        elif prior_velocity is None:
            out["FUNDING_ACCELERATION"] = _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "missing_prior_velocity_observation", context)
        else:
            elapsed = Decimal(str((current.timestamp - prior.timestamp).total_seconds())) if prior is not None else Decimal("0")
            if elapsed <= 0:
                out["FUNDING_ACCELERATION"] = _result(None, CalculationStatus.INVALID_INPUT, "non_positive_derivative_elapsed_time", context)
            else:
                out["FUNDING_ACCELERATION"] = _result((velocity - prior_velocity) / elapsed, CalculationStatus.VALID, "derived_from_ordered_velocity_observations", context)

        if current.open_interest_delta is not None:
            out["OI_DELTA"] = _result(current.open_interest_delta, CalculationStatus.VALID, "canonical_oi_delta", context)
        elif prior is None or current.open_interest is None or prior.open_interest is None:
            out["OI_DELTA"] = _result(None, CalculationStatus.INSUFFICIENT_HISTORY, "missing_prior_open_interest_observation", context)
        else:
            out["OI_DELTA"] = _result(current.open_interest - prior.open_interest, CalculationStatus.VALID, "derived_from_ordered_canonical_observations", context)
        out["OPEN_INTEREST"] = (
            _result(current.open_interest, CalculationStatus.VALID, "canonical_open_interest", context)
            if current.open_interest is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_canonical_open_interest", context)
        )
        out["BASIS"] = (
            _result(current.basis, CalculationStatus.VALID, "canonical_basis", context)
            if current.basis is not None else
            _result(None, CalculationStatus.UNAVAILABLE, "missing_canonical_basis", context)
        )
        return out
