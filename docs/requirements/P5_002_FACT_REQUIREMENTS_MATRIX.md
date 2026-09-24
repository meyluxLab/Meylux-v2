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


## Row-level authoritative source audit

The following audit is repository-derived from the Phase-3 canonical persistence migration, Phase-4 quantitative persistence migration/adapter, quantitative contracts, the Phase-5 roadmap, and the governed P5-002 OQ records. It deliberately separates schema existence from live runtime availability.

| Specialist | Authoritative source | Identity / columns checked | Runtime status at Producer boundary | Knowledge-time semantics |
|---|---|---|---|---|
| S-01 | `meylux.calculated_indicator_vectors` | `record_id`, `symbol`, `timeframe`, `event_time`, `source_ref`, `venue_context`, `version`, `calculation_version`, `status`, `reason`, `payload_json`, `identity_hash` | UNVERIFIED_BY_PRODUCER | No dedicated `knowledge_time`; `persisted_at` is not substituted |
| S-02 | `meylux.market_structure_events`, `meylux.market_structure_zones` | event/zone `record_id`, `symbol`, `timeframe`, `event_time`, status/reason, payload, identity | UNVERIFIED_BY_PRODUCER | No dedicated `knowledge_time` |
| S-03 | canonical candle + quantitative vector facts | candle/vector identity, event time, payload | UNVERIFIED_BY_PRODUCER | No dedicated `knowledge_time` |
| S-04 | `meylux.canonical_derivatives` | canonical identity/provenance/event fields + payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-05 | `meylux.canonical_trades` / `meylux.canonical_orderbook_depth` + P4 order-flow facts | canonical identity/provenance/event fields + payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-06 | P4 quantitative/structure persisted families | record identity, symbol/timeframe/event time/status/reason/payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-07 | canonical market tables with venue carried through payload/provenance context | canonical identity/event/provenance/payload | UNVERIFIED; second venue not evidenced | No dedicated `knowledge_time`; no silent venue substitution |
| S-08 | `meylux.calculated_indicator_vectors` | vector identity, symbol/timeframe/event time/status/reason/payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-09 | all contributing authoritative source facts | source-specific record identity | UNVERIFIED | Each source must independently expose `knowledge_time`; current P4 schemas do not |
| S-10 | `meylux.data_quality_logs` + acquisition contracts | log/record, quality/lifecycle, reason codes, provenance | UNVERIFIED | `logged_at` is not `knowledge_time` |
| S-11 | `meylux.canonical_candles` + structure zones | candle/zone identity, event time, payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-12 | structure zones + canonical depth | zone/depth identity, event time, payload | UNVERIFIED | No dedicated `knowledge_time` |
| S-13 | contributing Snapshot source facts | source record identity | UNVERIFIED | Must inherit explicit source `knowledge_time`; cannot infer it |
| S-14 | regime + structure historical facts | record identity, symbol/timeframe/event time/status/reason/payload | UNVERIFIED; minimum history not evidenced | No dedicated `knowledge_time` |
| S-15 | no provider configured | N/A | ROADMAP CONTRACT: SKIPPED | N/A |
| S-16 | contributing authoritative P4 facts | source record identity | UNVERIFIED | Each source must expose explicit `knowledge_time` |
| S-17 | `meylux.volume_profile_sessions` | session identity, symbol/timeframe/session bounds/status/reason/payload | UNVERIFIED; two sessions not evidenced | No dedicated `knowledge_time` |
| S-18 | `meylux.market_regime_states` + structure facts | regime/structure identity, symbol/timeframe/event time/status/reason/payload | UNVERIFIED; executable in principle but live evidence absent | No dedicated `knowledge_time` in P4 persistence schemas |

**Critical semantic result:** the repository schemas expose `event_time` and persistence timestamps, but do not expose a dedicated authoritative `knowledge_time` column for the P4 quantitative/canonical persistence families above. P5-002 therefore never substitutes `event_time` or `persisted_at` for `knowledge_time`. Such facts cannot be admitted to an authoritative P5 Snapshot until the upstream semantic gap is governed and independently evidenced.

## Roadmap §37 — growth / retention boundary

The governing persistence/data-growth doctrine requires explicit treatment of:

- logical event identity;
- deduplication key;
- unique constraint;
- expected rate;
- peak rate;
- daily growth;
- retention;
- compression/archive;
- maximum acceptable cardinality;
- alert threshold;
- recovery path;
- backfill semantics;
- replay semantics.

P5-002 introduces none of these as a new durable high-volume persistence owner. The Snapshot remains deterministic/in-memory and FRM remains version-controlled. No runtime retention mechanism, migration, high-volume writer, archive policy, or durable Snapshot store is introduced. Any future durable Snapshot/Execution persistence must undergo a separately governed Step/change assessment using the complete §37 field set.

Existing P2/P3/P4 persistence ownership remains unchanged.
