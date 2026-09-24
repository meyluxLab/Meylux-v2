"""Authoritative Phase-5 Step-002 Fact Requirements Matrix model.

USR-03 has exactly three lifecycle dispositions. Subordinate reasons and governed
OQ/DD records never become lifecycle states.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class FRMValidationError(ValueError):
    pass


class USR03Disposition(str, Enum):
    AVAILABLE_PERSISTED = "AVAILABLE_PERSISTED"
    PRQ_DELIVERED = "PRQ_DELIVERED"
    UNAVAILABLE_DISPOSITIONED = "UNAVAILABLE_DISPOSITIONED"


class FRMReason(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT = "INSUFFICIENT"
    INVALID = "INVALID"
    STALE = "STALE"
    MISSING = "MISSING"
    NOT_REQUIRED = "NOT_REQUIRED"


@dataclass(frozen=True, slots=True)
class FactRequirement:
    specialist: str
    required_fact: str
    authoritative_source: str
    granularity: str
    timeframe: str
    minimum_history: str
    mandatory: bool
    disposition: USR03Disposition
    reason: FRMReason
    provenance_requirement: str
    lookahead_rule: str
    evidence: tuple[str, ...]
    dependency_owner: str = ""
    dependency_route: str = ""
    governed_disposition: str = ""
    source_audit: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, field in (
            (self.specialist, "specialist"),
            (self.required_fact, "required_fact"),
            (self.authoritative_source, "authoritative_source"),
            (self.granularity, "granularity"),
            (self.timeframe, "timeframe"),
            (self.minimum_history, "minimum_history"),
            (self.provenance_requirement, "provenance_requirement"),
            (self.lookahead_rule, "lookahead_rule"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise FRMValidationError(f"{field} must be non-empty")
        if not isinstance(self.mandatory, bool):
            raise FRMValidationError("mandatory must be bool")
        if not isinstance(self.evidence, tuple) or not self.evidence:
            raise FRMValidationError("each FRM row requires repository evidence")
        if self.disposition in {USR03Disposition.AVAILABLE_PERSISTED, USR03Disposition.PRQ_DELIVERED}:
            if self.reason is not FRMReason.NOT_REQUIRED:
                raise FRMValidationError("available/delivered rows must use NOT_REQUIRED reason")
            if self.governed_disposition:
                raise FRMValidationError("available/delivered rows cannot carry an unavailable disposition record")
        if not self.source_audit:
            raise FRMValidationError("every FRM row requires row-level source audit evidence")
        if self.disposition is USR03Disposition.UNAVAILABLE_DISPOSITIONED:
            if self.reason is FRMReason.NOT_REQUIRED:
                raise FRMValidationError("unavailable rows require a subordinate reason")
            if not self.governed_disposition.strip():
                raise FRMValidationError("every unavailable row requires an OQ/DD or other governed disposition record")


SPECIALISTS = tuple(f"S-{i:02d}" for i in range(1, 19))


def validate_frm(rows: Iterable[FactRequirement]) -> tuple[FactRequirement, ...]:
    rows = tuple(rows)
    if not rows:
        raise FRMValidationError("FRM cannot be empty")
    specialists = {row.specialist for row in rows}
    if specialists != set(SPECIALISTS):
        raise FRMValidationError(
            f"specialist coverage mismatch: missing={sorted(set(SPECIALISTS)-specialists)}, "
            f"extra={sorted(specialists-set(SPECIALISTS))}"
        )
    if len({(row.specialist, row.required_fact) for row in rows}) != len(rows):
        raise FRMValidationError("FRM contains duplicate specialist/fact rows")
    if any(row.disposition not in set(USR03Disposition) for row in rows):
        raise FRMValidationError("FRM contains a non-USR-03 disposition")
    return rows


def _row(
    specialist: str, fact: str, source: str, granularity: str, timeframe: str,
    history: str, mandatory: bool, disposition: USR03Disposition, reason: FRMReason,
    provenance: str, lookahead: str, evidence: tuple[str, ...],
    owner: str = "", route: str = "", governed: str = "",
) -> FactRequirement:
    return FactRequirement(
        specialist, fact, source, granularity, timeframe, history, mandatory,
        disposition, reason, provenance, lookahead, evidence, owner, route, governed, SOURCE_AUDIT[specialist]
    )


OQ1 = "OQ-P5-002-PRQ1-FACT-AVAILABILITY"
OQ2 = "OQ-P5-002-PRQ2-VENUE-ORDERFLOW"
OQ3 = "OQ-P5-002-PRQ3-DERIVATIVES"
OQ4 = "OQ-P5-002-PRQ4-QUALITY-EVIDENCE"
ROADMAP_S15 = "docs/blueprint/PHASE5_ROADMAP.md §16.2 S-15 — SKIPPED / NO_NEWS_PROVIDER_CONFIGURED"
SOURCE_AUDIT = {
"S-01": ("schema=meylux","table=calculated_indicator_vectors","columns=record_id,symbol,timeframe,event_time,source_ref,venue_context,version,calculation_version,status,reason,value_numeric,payload_json,identity_hash,persisted_at","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED_BY_PRODUCER; knowledge_time=ABSENT"),
"S-02": ("schema=meylux","table=market_structure_events + market_structure_zones","columns=record_id,symbol,timeframe,event_time,event_type/zone_type,source_ref,venue_context,version,calculation_version,status,reason,payload_json,identity_hash,persisted_at","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED_BY_PRODUCER; knowledge_time=ABSENT"),
"S-03": ("schema=meylux","table=calculated_indicator_vectors + canonical_candles","columns=vector payload_json; candle payload_json,event_time,identity_hash","identity=vector record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED_BY_PRODUCER; knowledge_time=ABSENT"),
"S-04": ("schema=meylux","table=canonical_derivatives","columns=record_id,event_id,instrument_id,event_time,provenance_id,source_record_id,lineage_parent_id,quality_state,quality_score,payload_json,canonical_bytes,identity_hash,persisted_at","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; knowledge_time=ABSENT"),
"S-05": ("schema=meylux","table=canonical_trades + canonical_orderbook_depth + P4 order-flow facts","columns=record_id,event_id,instrument_id,event_time,provenance_id,source_record_id,lineage_parent_id,quality_state,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; knowledge_time=ABSENT"),
"S-06": ("schema=meylux","table=calculated_indicator_vectors + market_structure_*","columns=record_id,symbol,timeframe,event_time,status,reason,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; complete timeframe coverage not evidenced; knowledge_time=ABSENT"),
"S-07": ("schema=meylux","table=canonical market tables","columns=instrument_id,event_time,provenance_id,source_record_id,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; venue is payload/provenance context; knowledge_time=ABSENT"),
"S-08": ("schema=meylux","table=calculated_indicator_vectors","columns=record_id,symbol,timeframe,event_time,source_ref,venue_context,version,calculation_version,status,reason,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; required sub-facts/timeframes not evidenced; knowledge_time=ABSENT"),
"S-09": ("source=all contributing P2/P3/P4 rows","identity=each source record_id + identity_hash","runtime=UNVERIFIED; Snapshot receipt is not availability evidence","knowledge_time=each source must expose it; current P4 schemas do not"),
"S-10": ("schema=meylux","table=data_quality_logs + acquisition contracts","columns=log_id,record_id,quality_state,lifecycle_state,quality_score,reason_codes,validation_result,provenance_id,source_record_id,lineage_parent_id,payload_fingerprint,logged_at","identity=log_id; record_id indexed","runtime=UNVERIFIED; knowledge_time=ABSENT"),
"S-11": ("schema=meylux","table=canonical_candles + market_structure_zones","columns=record_id,instrument_id,event_time,payload_json,identity_hash + zone fields","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; knowledge_time=ABSENT"),
"S-12": ("schema=meylux","table=market_structure_zones + canonical_orderbook_depth","columns=zone/depth record_id,event_time,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; knowledge_time=ABSENT"),
"S-13": ("source=authoritative Snapshot source facts","identity=source record_id + identity_hash","runtime=UNVERIFIED; source completeness not evidenced","knowledge_time=must come from each source; current schemas do not provide it"),
"S-14": ("schema=meylux","table=market_regime_states + market_structure_events/zones","columns=record_id,symbol,timeframe,event_time,status,reason,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; minimum history not evidenced; knowledge_time=ABSENT"),
"S-15": ("source=N/A; no news provider configured","identity=N/A","runtime=ROADMAP-CONTRACT-SKIPPED","knowledge_time=N/A"),
"S-16": ("source=authoritative P4 Snapshot source facts","identity=source record_id + identity_hash","runtime=UNVERIFIED; checklist inputs not evidenced","knowledge_time=each source must expose it"),
"S-17": ("schema=meylux","table=volume_profile_sessions","columns=record_id,symbol,timeframe,session_start,session_end,source_ref,venue_context,version,calculation_version,status,reason,payload_json,identity_hash,persisted_at","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; two sessions not evidenced; knowledge_time=ABSENT"),
"S-18": ("schema=meylux","table=market_regime_states + market_structure_events/zones","columns=record_id,symbol,timeframe,event_time,regime_state/status,reason,payload_json,identity_hash","identity=record_id PK; identity_hash UNIQUE","runtime=UNVERIFIED; theoretically executable but live evidence absent; knowledge_time=ABSENT")
}



FRM_ROWS = (
    _row("S-01", "EMA20 / RSI14 / ATR14 indicator facts by timeframe",
          "meylux.calculated_indicator_vectors / P4 quantitative contract",
          "persisted vector per symbol + timeframe + event_time", "15M / 1H / 4H",
          "EMA20 requires sufficient candle history; current runtime availability requires CONTROL evidence",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "EvidenceRef: source_family, record_id, identity_hash, event_time, knowledge_time, timeframe, venue",
          "knowledge_time <= snapshot.as_of; event_time preserved independently",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-01", "docs/audits/AR-P4-015.md — P4 inventory"),
          "P4", "PRQ-1 / quantitative fact operationalization", OQ1),

    _row("S-02", "market structure events and zones",
          "meylux.market_structure_events / meylux.market_structure_zones; P4 structure contract",
          "event / zone record", "as persisted",
          "latest confirmed event plus relevant zone history",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef for every actual event/zone record",
          "knowledge_time <= snapshot.as_of; event_time remains distinct",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-02", "migrations/versions/0005_quantitative_foundation.sql"),
          "P4", "PRQ-1 / structure fact operationalization", OQ1),

    _row("S-03", "volume / RVOL facts",
          "P4 quantitative volume contract / persisted quantitative facts",
          "persisted volume fact/vector", "primary timeframe as persisted",
          "configured RVOL lookback; current persisted availability requires CONTROL evidence",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to actual persisted volume facts",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-03",),
          "P4", "PRQ-1 / volume fact operationalization", OQ1),

    _row("S-04", "funding / OI / basis derivatives facts",
          "P2 acquisition boundary + P4 derivatives contract; canonical_derivatives when populated",
          "derivatives observation", "provider/product cadence as persisted",
          "current derivatives delivery is not established by source/table existence",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNSUPPORTED,
          "Structured EvidenceRef only after authoritative derivatives delivery",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-04",),
          "P2/P4", "PRQ-3 / derivatives acquisition and persistence", OQ3),

    _row("S-05", "delta / CVD / imbalance / absorption",
          "P4 Order Flow contract; no P5-owned order-flow generation",
          "trade-derived / order-flow fact", "trade event/session as persisted",
          "series depth is required for CVD/change comparisons",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to actual persisted order-flow facts; no derivation here",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-05",),
          "P2/P4", "PRQ-1/2 / order-flow and trade/depth capability", OQ2),

    _row("S-06", "corresponding quantitative facts across 15M / 1H / 4H",
          "authoritative P4 quantitative tables",
          "one fact per symbol/timeframe/event_time", "15M / 1H / 4H",
          "all mandatory requested timeframes must be independently available",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "EvidenceRef per actual source fact",
          "knowledge_time <= snapshot.as_of; HTF event_time cannot imply future primary data",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-06",),
          "P4", "PRQ-1 / HTF fact operationalization", OQ1),

    _row("S-07", "same-instrument facts per venue",
          "canonical/P4 facts carrying venue context",
          "fact record per venue", "Binance / MEXC as actually persisted",
          "both venues are mandatory for a complete cross-exchange requirement",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef per venue; no venue substitution",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-07",),
          "P2", "PRQ-2 / second-venue capability", OQ2),

    _row("S-08", "ATR / HV / percentile / bandwidth",
          "P4 quantitative indicator contract",
          "indicator vector per symbol/timeframe", "15M / 1H / 4H",
          "all mandatory sub-facts/timeframes must be evidenced",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to each actual indicator record",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-08",),
          "P4", "PRQ-1 / additional indicator families", OQ1),

    _row("S-09", "all mandatory risk-relevant source facts consumed by the shared Snapshot",
          "authoritative Snapshot and its P2/P3/P4 source facts",
          "source fact", "same as contributing facts",
          "all mandatory contributing facts must be available; Snapshot receipt alone is not evidence",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Every contributing source fact retains complete structured EvidenceRef",
          "knowledge_time <= snapshot.as_of; event_time is retained separately",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-09", "docs/blueprint/PHASE5_ROADMAP.md — PD-4 Stage-1"),
          "P2/P3/P4", "PRQ-1 / complete source-fact availability", OQ1),

    _row("S-10", "quality context / capability declarations / acquisition state",
          "P3 quality and acquisition contracts",
          "quality/capability record", "as persisted",
          "required persisted quality evidence must be present and provenance-complete",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to persisted quality/acquisition record",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-10",),
          "P3", "PRQ-4 / persisted quality evidence", OQ4),

    _row("S-11", "closed-candle price-action inputs; structure zones when used",
          "meylux.canonical_candles; structure zones when actually persisted",
          "closed candle / zone", "15M primary; other persisted timeframes when required",
          "all mandatory candles/zones must be runtime-evidenced for the requested snapshot",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to every candle/zone used",
          "knowledge_time <= snapshot.as_of; candle event_time remains distinct",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-11", "migrations/versions/0003_canonical_persistence_event_outbox.sql"),
          "P2/P4", "PRQ-1 / authoritative fact availability", OQ1),

    _row("S-12", "liquidity zones; optional depth",
          "P4 structure zones; canonical_orderbook_depth for depth",
          "zone / depth observation", "as persisted",
          "mandatory liquidity-zone facts must be available; depth remains optional where roadmap permits",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to actual zone/depth records; no synthetic liquidity",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-12",),
          "P2/P4", "PRQ-1/2 / liquidity and depth facts", OQ2),

    _row("S-13", "shared Snapshot facts for deterministic counter-evidence",
          "authoritative Snapshot + P4 facts",
          "source fact", "same as contributing facts",
          "all mandatory source facts must be available before this composite requirement is available",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Original structured EvidenceRef is retained; no specialist output is consumed",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-13", "docs/blueprint/PHASE5_ROADMAP.md — PD-4"),
          "P2/P3/P4", "PRQ-1 / complete source-fact availability", OQ1),

    _row("S-14", "historical state series",
          "P4 regime/structure persisted facts",
          "historical series", "same instrument; per-candle-close",
          "configured minimum history must be independently available",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.INSUFFICIENT,
          "Structured EvidenceRef to every historical source record",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-14",),
          "P4", "PRQ-1 / historical fact persistence", OQ1),

    _row("S-15", "news / event facts",
          "no provider configured; contract-only specialist",
          "none", "N/A",
          "not applicable under the current roadmap disposition",
          False, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNSUPPORTED,
          "No fabricated EvidenceRef; no provider data is admitted",
          "N/A",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-15: SKIPPED / NO_NEWS_PROVIDER_CONFIGURED",),
          "", "Roadmap-defined skipped disposition; no provider activation", ROADMAP_S15),

    _row("S-16", "boolean setup-validation facts from Snapshot",
          "authoritative P4 facts in Snapshot",
          "source fact", "same as source facts",
          "all source facts required by the validation checklist must be available",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef per checklist criterion source",
          "knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-16", "docs/blueprint/PHASE5_ROADMAP.md — PD-4"),
          "P2/P3/P4", "PRQ-1 / complete source-fact availability", OQ1),

    _row("S-17", "volume profile sessions",
          "meylux.volume_profile_sessions",
          "session record", "session timeframe as persisted",
          "at least two persisted sessions for prior-session POC comparison",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef to actual persisted sessions only",
          "session end and knowledge_time <= snapshot.as_of",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-17", "migrations/versions/0005_quantitative_foundation.sql"),
          "P2/P4", "PRQ-1/2 / volume-profile persistence", OQ1),

    _row("S-18", "market regime state + independently sourced structural state",
          "meylux.market_regime_states + authoritative structure fact",
          "regime + structure observation", "as persisted",
          "both regime and structural components are mandatory for this composite requirement",
          True, USR03Disposition.UNAVAILABLE_DISPOSITIONED, FRMReason.UNAVAILABLE,
          "Structured EvidenceRef for regime and structural source records; no specialist dependency",
          "knowledge_time <= snapshot.as_of; event_time preserved independently",
          ("docs/blueprint/PHASE5_ROADMAP.md — S-18",),
          "P4", "PRQ-1 / structural companion availability", OQ1),
)


validate_frm(FRM_ROWS)
