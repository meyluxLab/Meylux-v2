"""Append-only persistence for Phase-5 specialist outputs."""
from __future__ import annotations
from typing import Any
from contracts.specialist import SpecialistOutput,canonical_json
TABLE="meylux.specialist_outputs"
class SpecialistPersistence:
    def __init__(self,connection:Any): self._connection=connection
    async def persist(self,output:SpecialistOutput)->bool:
        evidence=[]; seen=set()
        for ref in output.evidence_refs:
            if ref.evidence_id not in seen: evidence.append(ref.as_dict()); seen.add(ref.evidence_id)
        for finding in output.findings:
            for ref in finding.evidence_refs:
                if ref.evidence_id not in seen: evidence.append(ref.as_dict()); seen.add(ref.evidence_id)
        async with self._connection.transaction():
            result=await self._connection.execute(f"""INSERT INTO {TABLE}
(record_id,specialist_id,output_version,snapshot_id,snapshot_version,config_name,config_version,config_identity_hash,environment,status,reason,findings_json,evidence_refs_json,payload_json,identity_hash)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,$13::jsonb,$14::jsonb,$15)
ON CONFLICT (identity_hash) DO NOTHING""",
                output.identity_hash,output.specialist_id,output.output_version,output.snapshot_id,output.snapshot_version,
                output.config.name,output.config.version,output.config.identity_hash,output.config.environment,
                output.status.value,output.reason,canonical_json([f.as_dict() for f in output.findings]),
                canonical_json(evidence),output.serialize(),output.identity_hash)
        return str(result).strip()=="INSERT 0 1"
    async def fetch_by_identity(self,identity_hash:str):
        if not isinstance(identity_hash,str) or len(identity_hash)!=64: raise ValueError("identity_hash must be SHA-256")
        return await self._connection.fetchrow(f"SELECT * FROM {TABLE} WHERE identity_hash=$1",identity_hash)
