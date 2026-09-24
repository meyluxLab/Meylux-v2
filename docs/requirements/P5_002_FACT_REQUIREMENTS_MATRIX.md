# P5-002 Fact Requirements Matrix

Task Order: TO-P5-002 Rev 1.2

USR-03 lifecycle dispositions are exactly: AVAILABLE_PERSISTED, PRQ_DELIVERED, UNAVAILABLE_DISPOSITIONED.

AVAILABLE_PERSISTED is a CONTROL-owned runtime evidence state. Source-code capability, table existence, or historical evidence does not establish it. Producer makes no unverified AVAILABLE_PERSISTED claim in this baseline.

All 18 specialist domains S-01 through S-18 are represented in the implementation model. Every unavailable requirement carries a governed dependency disposition. S-15 uses the roadmap's explicit contract-only skipped disposition.

EvidenceRef completeness requires source_family, record_id, identity_hash, event_time, knowledge_time, timeframe, and venue. source_reference is not a substitute. event_time and knowledge_time are preserved independently, and knowledge_time must be <= snapshot.as_of.

Snapshot growth/retention policy: no new durable high-volume persistence owner is introduced. Snapshot is deterministic/in-memory; FRM is version-controlled. Existing upstream persistence ownership remains unchanged. Any future durable Snapshot/Execution persistence requires a separately governed growth/retention analysis.

Live persisted-fact availability remains CONTROL-owned SentinelX evidence; Producer performs no VPS mutation or provider activation.

## Corrected FRM dispositions

| Specialist | Required fact family | USR-03 disposition | Reason | Governed disposition |
|---|---|---|---|---|
| S-01 | indicator vectors | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-02 | structure events and zones | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-03 | volume / RVOL | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-04 | funding / OI / basis | UNAVAILABLE_DISPOSITIONED | UNSUPPORTED | OQ-P5-002-PRQ3-DERIVATIVES |
| S-05 | delta / CVD / imbalance / absorption | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ2-VENUE-ORDERFLOW |
| S-06 | multi-timeframe quantitative facts | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-07 | same-instrument multi-venue facts | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ2-VENUE-ORDERFLOW |
| S-08 | ATR / HV / percentile / bandwidth | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-09 | all mandatory risk source facts | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-10 | quality/acquisition state | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ4-QUALITY-EVIDENCE |
| S-11 | closed-candle price action and used zones | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-12 | liquidity zones / optional depth | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ2-VENUE-ORDERFLOW |
| S-13 | shared source facts for counter-evidence | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-14 | historical state series | UNAVAILABLE_DISPOSITIONED | INSUFFICIENT | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-15 | configured event/news facts | UNAVAILABLE_DISPOSITIONED | UNSUPPORTED | roadmap S-15: SKIPPED / NO_NEWS_PROVIDER_CONFIGURED |
| S-16 | setup-validation source facts | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-17 | volume-profile sessions | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |
| S-18 | regime state plus structural companion | UNAVAILABLE_DISPOSITIONED | UNAVAILABLE | OQ-P5-002-PRQ1-FACT-AVAILABILITY |

S-09 is not available merely because it consumes the shared Snapshot. S-18 is not available merely because a regime-state record exists; its mandatory structural companion must also be independently evidenced.

For each row the implementation model records source/contract, granularity, timeframe, history requirement, mandatory flag, provenance requirement, as-of rule, dependency owner and governed disposition. No upstream capability is implemented by P5-002.
