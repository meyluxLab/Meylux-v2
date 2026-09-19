# PROJECT OWNER DIRECTIVE — Resolution of AR-P4-013 Open Evidence Boundary

**Date:** 2026-09-20
**Phase / Step:** PH-P4 / STEP-P4-006
**Current Task Order at issuance:** TO-P4-007
**Authority:** Project Owner
**Decision:** BOTH Decision A and Decision B authorized

## Decision A — Governed real-data vertical slice

CONTROL is authorized to establish and verify a bounded governed real-data path for:

BTCUSDT — 15M primary + 1H + 4H

The path MUST reuse the existing P2 provider-adapter, P3 validation/normalization, and CanonicalPersistence boundaries and contracts.

Explicit prohibitions:
- no P2 bypass;
- no P3 validation/normalization bypass;
- no CanonicalPersistence bypass;
- no synthetic data represented as real;
- no direct quantitative-table injection outside governed persistence;
- no account credentials or authenticated/private market-data access;
- no trading/order/portfolio/capital/custody endpoints;
- no V1 access or mutation;
- no frozen architecture or canonical contract alteration without separate authority.

If implementation is required, CONTROL shall issue an appropriate bounded Task Order/amendment and delegate implementation to ROL-V2-002. CONTROL retains SentinelX-only VPS execution authority and owns the official EXEC-LOG.

CONTROL shall determine the minimum governed historical window from authoritative Phase-4 requirements and actual warm-up semantics, and shall record the exact acquired and processed window.

Required evidence includes, as applicable:
- canonical data availability;
- P2 -> P3 -> CanonicalPersistence integrity;
- BTCUSDT 15M + 1H + 4H MTF execution;
- persistence;
- deterministic replay;
- restart/recovery;
- G-4 evidence.

No synthetic/fabricated substitution is permitted.

## Decision B — Performance gap

CONTROL SHALL NOT modify or reopen the previously verified EMA or Market Structure engines under this directive.

CONTROL is authorized to:
1. define the exact workload basis of the roadmap performance target;
2. reproduce/profile the observed cost;
3. evaluate orchestrator/runtime-level optimizations;
4. determine output-preservation feasibility;
5. evaluate the effect of the Decimal numeric policy;
6. record the evidence and conclusion.

Any optimization must preserve the exact verified outputs/semantics of existing engines.

If the target cannot be reached within these boundaries, CONTROL shall not silently change the target or reopen verified engines. The unresolved matter shall be recorded through the authoritative Deferred Decisions mechanism with an evidence-based trigger.

Engine-level optimization, reopening P4-002/P4-003 verification, or revision of the authoritative performance target requires further Owner authority.

## Governance

The two remaining findings shall receive distinct repository-assigned Open Question identifiers.

This directive shall remain traceable through the repository Change Ledger and the applicable Task Order/audit records.

Rule 1 continuation applies. STEP-P4-006, PH-P4 and G-4 remain open until evidence exists and CONTROL independently verifies it.

Phase 5 remains NOT AUTHORIZED.
