"""Deterministic Phase-4 quantitative foundation and indicator engine."""
from .numeric import quantize, serialize_decimal
from .primitives import (
    rolling_mean, average, weighted_average, exponential_smoothing,
    standard_deviation, percentile, accumulate, normalize_min_max,
)
from .golden import run_golden_vectors, load_golden_vectors
from .indicators import (
    ADX, ATR, EMA, HMA, MACD, RSI, RVOL, SMA, WMA, VWAP, AnchoredVWAP,
    ATRPercentile, HistoricalVolatility, BollingerBands, Supertrend, VolumeSMA,
    atr, atr_percentile, adx, anchored_vwap, bollinger_bands, bollinger_bandwidth,
    ema, ema_candles, historical_volatility, hma, hma_candles, macd, rsi,
    sma, sma_candles, supertrend, volume_activity, volume_climax, volume_sma,
    volume_spike, vwap, wma, wma_candles, volatility_expansion_ratio,
    BandPoint, MACDPoint, SupertrendPoint, VolumeActivityPoint,
)
from .market_structure import MarketStructureEngine, MarketStructureAnalysis, StructuralEvent, BarState, SEMANTIC_VERSION

__all__ = [
    "quantize", "serialize_decimal",
    "rolling_mean", "average", "weighted_average", "exponential_smoothing",
    "standard_deviation", "percentile", "accumulate", "normalize_min_max",
    "run_golden_vectors", "load_golden_vectors",
    "ADX", "ATR", "EMA", "HMA", "MACD", "RSI", "RVOL", "SMA", "WMA", "VWAP",
    "AnchoredVWAP", "ATRPercentile", "HistoricalVolatility", "BollingerBands",
    "Supertrend", "VolumeSMA", "atr", "atr_percentile", "adx", "anchored_vwap",
    "bollinger_bands", "bollinger_bandwidth", "ema", "ema_candles",
    "historical_volatility", "hma", "hma_candles", "macd", "rsi", "sma",
    "sma_candles", "supertrend", "volume_activity", "volume_climax", "volume_sma",
    "volume_spike", "vwap", "wma", "wma_candles", "volatility_expansion_ratio",
    "BandPoint", "MACDPoint", "SupertrendPoint", "VolumeActivityPoint",
    "MarketStructureEngine", "MarketStructureAnalysis", "StructuralEvent", "BarState", "SEMANTIC_VERSION",
    "VOLUME_ORDERFLOW_DERIVATIVES_SEMANTIC_VERSION", "VolumeProfileConfig", "VolumeProfileAnalysis",
    "VolumeProfileEngine", "ClosedBar", "OrderFlowConfig", "OrderFlowEngine", "DerivativesEngine",
]
from .volume_orderflow_derivatives import (
    SEMANTIC_VERSION as VOLUME_ORDERFLOW_DERIVATIVES_SEMANTIC_VERSION,
    VolumeProfileConfig, VolumeProfileAnalysis, VolumeProfileEngine,
    ClosedBar, OrderFlowConfig, OrderFlowEngine, DerivativesEngine,
)
