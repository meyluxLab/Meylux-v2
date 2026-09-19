from __future__ import annotations
import json
from typing import Iterable,Mapping
from contracts.canonical.candle import CanonicalCandle
from meylux.orchestration import QuantitativeOrchestrator,QuantOrchestrationConfig,QuantOrchestrationResult
from meylux.persistence.quantitative import _json
class QuantitativeReplay:
    def __init__(self,orchestrator=None): self._orchestrator=orchestrator or QuantitativeOrchestrator()
    def run(self,candles:Iterable[CanonicalCandle],config:QuantOrchestrationConfig,*,previous_regime=None,higher_timeframes:Mapping[str,Iterable[CanonicalCandle]]|None=None)->QuantOrchestrationResult:
        return self._orchestrator.process(candles,config,previous_regime=previous_regime,higher_timeframes=higher_timeframes)
    def fingerprint(self,result:QuantOrchestrationResult)->str: return json.dumps(_json(result),sort_keys=True,separators=(",",":"))
