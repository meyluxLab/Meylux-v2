"""Append-only adapter to the existing authoritative Phase-4 quantitative tables."""
from __future__ import annotations
from dataclasses import asdict,is_dataclass
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,json
from typing import Any,Mapping
from contracts.quantitative.base import CalculationResult
from meylux.orchestration.engine import QuantOrchestrationResult

def _json(v:Any)->Any:
    if isinstance(v,Decimal):
        if not v.is_finite(): raise ValueError("non-finite Decimal")
        return format(v,"f")
    if isinstance(v,datetime):
        if v.tzinfo is None or v.utcoffset()!=timezone.utc.utcoffset(v): raise ValueError("datetime must be UTC")
        return v.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
    if is_dataclass(v): return _json(asdict(v))
    if isinstance(v,Mapping): return {str(k):_json(x) for k,x in sorted(v.items(),key=lambda x:str(x[0]))}
    if isinstance(v,(tuple,list)): return [_json(x) for x in v]
    if isinstance(v,(str,int,bool)) or v is None: return v
    raise TypeError(f"unsupported value: {type(v).__name__}")

def _calc(v:CalculationResult)->dict[str,Any]:
    return {"value":None if v.value is None else format(v.value,"f"),"status":v.status.value,"reason":v.reason,"context":_json(v.context)}

class QuantitativePersistence:
    TABLES={"indicator":"meylux.calculated_indicator_vectors","structure_event":"meylux.market_structure_events","structure_zone":"meylux.market_structure_zones","volume_profile":"meylux.volume_profile_sessions","regime":"meylux.market_regime_states"}
    def __init__(self,connection:Any): self._connection=connection
    @staticmethod
    def _id(material:Mapping[str,Any])->str: return hashlib.sha256(json.dumps(_json(material),sort_keys=True,separators=(",",":")).encode()).hexdigest()
    async def persist_orchestration(self,result:QuantOrchestrationResult)->int:
        rows=[]
        for name,calc in result.indicators.items():
            payload=_calc(calc); material={"family":"indicator","name":name,"symbol":result.symbol,"timeframe":result.timeframe,"event_time":result.as_of,"version":result.configuration_version,"payload":payload}
            rows.append(("indicator",self._id(material),name,calc.status.value,calc.reason,calc.value,calc.context,payload,"1.0.0"))
        payload={"state":result.regime.state,"transition":result.regime_transition,"result":_calc(result.regime.result),"source_provenance":result.source_provenance,"htf":_json(result.htf)}
        material={"family":"regime","symbol":result.symbol,"timeframe":result.timeframe,"event_time":result.as_of,"version":result.configuration_version,"payload":payload}
        rows.append(("regime",self._id(material),result.regime.state,result.regime.result.status.value,result.regime.result.reason,result.regime.result.value,result.regime.result.context,payload,result.regime.calculation_version))
        payload={"event_count":result.structure_event_count,"state":result.structure_state,"source_provenance":result.source_provenance}
        material={"family":"structure_event","symbol":result.symbol,"timeframe":result.timeframe,"event_time":result.as_of,"version":result.configuration_version,"payload":payload}
        rows.append(("structure_event",self._id(material),"ORCHESTRATION","valid","orchestration_snapshot",None,None,payload,"1.0.0"))
        async with self._connection.transaction():
            inserted=0
            for family,rid,kind,status,reason,value,ctx,payload,calc_version in rows:
                source=ctx.source_ref if ctx else f"canonical-provenance:{'|'.join(result.source_provenance)}"; venue=ctx.venue_context if ctx else None
                pj=json.dumps(_json(payload),sort_keys=True,separators=(",",":"))
                if family=="indicator":
                    sql=f"INSERT INTO {self.TABLES[family]} (record_id,symbol,timeframe,event_time,source_ref,venue_context,version,calculation_version,status,reason,value_numeric,payload_json,identity_hash) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,$13) ON CONFLICT(identity_hash) DO NOTHING"
                    args=(rid,result.symbol,result.timeframe,result.as_of,source,venue,result.configuration_version,calc_version,status,reason,value,pj,rid)
                elif family=="regime":
                    sql=f"INSERT INTO {self.TABLES[family]} (record_id,symbol,timeframe,event_time,regime_state,source_ref,venue_context,version,calculation_version,status,reason,value_numeric,payload_json,identity_hash) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14) ON CONFLICT(identity_hash) DO NOTHING"
                    args=(rid,result.symbol,result.timeframe,result.as_of,kind,source,venue,result.configuration_version,calc_version,status,reason,value,pj,rid)
                else:
                    sql=f"INSERT INTO {self.TABLES[family]} (record_id,symbol,timeframe,event_time,event_type,source_ref,venue_context,version,calculation_version,status,reason,value_numeric,payload_json,identity_hash) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14) ON CONFLICT(identity_hash) DO NOTHING"
                    args=(rid,result.symbol,result.timeframe,result.as_of,kind,source,venue,result.configuration_version,calc_version,status,reason,value,pj,rid)
                if str(await self._connection.execute(sql,*args)).startswith("INSERT"): inserted+=1
        return inserted
    async def fetch_family(self,family:str,symbol:str,timeframe:str,*,start:datetime|None=None,end:datetime|None=None,limit:int=100)->list[Any]:
        if family not in self.TABLES: raise ValueError("unsupported quantitative family")
        if not symbol or not timeframe: raise ValueError("symbol and timeframe are required")
        if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=1000: raise ValueError("limit must be 1..1000")
        sql=f"SELECT * FROM {self.TABLES[family]} WHERE symbol=$1 AND timeframe=$2"; args=[symbol,timeframe]\n        if start is not None:\n            if start.tzinfo is None or start.utcoffset()!=timezone.utc.utcoffset(start): raise ValueError("start must be UTC")\n            sql+=f" AND event_time>${len(args)+1}"; args.append(start)\n        if end is not None:\n            if end.tzinfo is None or end.utcoffset()!=timezone.utc.utcoffset(end): raise ValueError("end must be UTC")\n            if start is not None and end<start: raise ValueError("end must not precede start")\n            sql+=f" AND event_time<${len(args)+1}"; args.append(end)\n        sql+=f" ORDER BY event_time,record_id LIMIT ${len(args)+1}"; args.append(limit)\n        return list(await self._connection.fetch(sql,*args))
