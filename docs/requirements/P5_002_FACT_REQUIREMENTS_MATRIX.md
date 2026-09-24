# P5-002 Fact Requirements Matrix

Task Order: TO-P5-002 Rev 1.2

USR-03 lifecycle dispositions are exactly: AVAILABLE_PERSISTED, PRQ_DELIVERED, UNAVAILABLE_DISPOSITIONED.

AVAILABLE_PERSISTED is a CONTROL-owned runtime evidence state. Source-code capability, table existence, or historical evidence does not establish it. Producer makes no unverified AVAILABLE_PERSISTED claim in this baseline.

All 18 specialist domains S-01 through S-18 are represented in the implementation model. Every unavailable requirement carries a governed dependency disposition. S-15 uses the roadmap's explicit contract-only skipped disposition.

EvidenceRef completeness requires source_family, record_id, identity_hash, event_time, knowledge_time, timeframe, and venue. source_reference is not a substitute. event_time and knowledge_time are preserved independently, and knowledge_time must be <= snapshot.as_of.

Snapshot growth/retention policy: no new durable high-volume persistence owner is introduced. Snapshot is deterministic/in-memory; FRM is version-controlled. Existing upstream persistence ownership remains unchanged. Any future durable Snapshot/Execution persistence requires a separately governed growth/retention analysis.

Live persisted-fact availability remains CONTROL-owned SentinelX evidence; Producer performs no VPS mutation or provider activation.
