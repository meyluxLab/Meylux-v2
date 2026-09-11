"""Provider-neutral acquisition boundary for Meylux V2."""

from .binance import BinanceAdapter, RetryPolicy
from .collector import AcquisitionCollector, CollectorStats
from .mexc import MEXCAdapter
from .persistence import PersistenceResult, RawStagingRepository
from .provider import ProviderAdapter

__all__ = [
    "AcquisitionCollector",
    "BinanceAdapter",
    "CollectorStats",
    "MEXCAdapter",
    "PersistenceResult",
    "ProviderAdapter",
    "RawStagingRepository",
    "RetryPolicy",
]
