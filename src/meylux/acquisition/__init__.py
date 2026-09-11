"""Provider-neutral acquisition boundary for Meylux V2."""

from .binance import BinanceAdapter, RetryPolicy
from .collector import AcquisitionCollector, CollectorStats
from .mexc import MEXCAdapter
from .models import RawAcquisitionRecord
from .persistence import PersistenceResult, RawStagingRepository
from .provider import ProviderAdapter
from .transport import AcquisitionQueuePublisher

__all__ = [
    "AcquisitionCollector",
    "AcquisitionQueuePublisher",
    "BinanceAdapter",
    "CollectorStats",
    "MEXCAdapter",
    "PersistenceResult",
    "ProviderAdapter",
    "RawAcquisitionRecord",
    "RawStagingRepository",
    "RetryPolicy",
]
