from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
from typing import Any,Mapping
from contracts.canonical.candle import CanonicalCandle
from meylux.orchestration import QuantitativeOrchestrator,QuantOrchestrationConfig
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.queue import QueueEnvelope

def _candle(r:Mapping[str,Any])->CanonicalCandle:
    def dt(x): return datetime.fromisoformat(x.replace("Z","+00:00"))
    return CanonicalCandle(r["instrument_id"],r["timeframe"],dt(r["open_time"]),dt(r["close_time"]),Decimal(r["open"]),Decimal(r["high"]),Decimal(r["low"]),Decimal(r["close"]),Decimal(r["volume"]),None if r.get("quote_volume") is None else Decimal(r["quote_volume"]),r.get("trade_count"),r["is_closed"],r["provenance_id"])

def _higher(raw:Mapping[str,Any])->dict[str,tuple[CanonicalCandle,...]]:
    value=raw.get("higher_timeframes",{})
    if value is None:return {}
    if not isinstance(value,Mapping): raise ValueError("higher_timeframes must be a mapping")
    return {tf:tuple(_candle(x) for x in rows) for tf,rows in value.items()}

class QuantWorkerHandler:
    def __init__(self,persistence:QuantitativePersistence,config:QuantOrchestrationConfig): self._persistence=persistence; self._config=config; self._orchestrator=QuantitativeOrchestrator()
    async def __call__(self,envelope:QueueEnvelope)->None:
        if envelope.payload_contract!="CTR-P4-QUANT-CANDLE-CLOSE-1.0": raise ValueError("unsupported quantitative worker payload contract")
        raw=envelope.payload
        candles=tuple(_candle(x) for x in raw["candles"])
        if not candles or not candles[-1].is_closed: raise ValueError("worker requires closed candles")
        await self._persistence.persist_orchestration(self._orchestrator.process(candles,self._config,previous_regime=raw.get("previous_regime"),higher_timeframes=_higher(raw)))
