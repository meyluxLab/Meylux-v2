# Meylux V2 — Evidence Policy

**Status:** RECONCILED / PENDING CONTROL VERIFICATION  
**Scope:** V2 evidence provenance, classification, integrity, verification, acceptance, and governance boundaries

## 1. Purpose

This policy defines what may be used as evidence for Meylux V2 state and completion claims. Evidence must establish the specific fact being claimed; evidence existence alone does not prove unrelated behavior.

Claims such as `IMPLEMENTED`, `EXECUTED`, `TESTED`, `VERIFIED`, `ACCEPTED`, `COMPLETE`, `GREEN`, `RATIFIED`, `FROZEN`, or `CLOSED` require identifiable supporting evidence appropriate to the claim and its governing boundary.

## 2. Evidence Classes

Evidence is classified by what it establishes:

### 2.1 Structural evidence

Examples:

- repository artifacts;
- schemas and contracts;
- registry records;
- configuration structure;
- artifact lineage;
- content/version identifiers.

Structural evidence can establish that an artifact or definition exists in a particular repository state. It does not by itself establish runtime behavior.

### 2.2 Behavioral evidence

Behavioral evidence records observed behavior from an authorized test or execution context. It must identify the behavior observed, the context in which it was observed, and the evidence source.

### 2.3 Test evidence

Test evidence may include:

- static checks;
- unit tests;
- contract tests;
- integration tests;
- failure/negative tests;
- property tests;
- replay tests;
- chaos tests;
- end-to-end tests;
- soak tests;
- other explicitly approved verification methods.

A passing test proves only the scope and behavior actually exercised by that test.

### 2.4 Operational evidence

Operational evidence includes actual Operator execution output, EXEC-LOG records, deployment evidence, runtime verification, or other physical/environment evidence where explicitly authorized.

Operational evidence MUST NOT be fabricated from design or test artifacts.

### 2.5 Governance evidence

Governance evidence includes:

- authorized Task Orders;
- Build Reports;
- Audit Reports;
- ADR/ACR decisions;
- approvals and ratifications;
- controlled checkpoint transitions;
- freeze/closure records.

Governance evidence establishes authority and lifecycle state. It does not replace technical or analytical evidence.

### 2.6 Data / analytical evidence

Data/analytical evidence includes:

- validated market data;
- data-quality records;
- deterministic computation outputs;
- market-structure evidence;
- derivatives/order-flow evidence;
- specialist outputs;
- analytical conclusions and contradiction results.

Analytical evidence must remain traceable to its inputs and relevant as-of time where applicable. Missing, stale, contradictory, or unavailable market data remains explicitly represented.

## 3. Provenance Minimum

Every material evidence item SHOULD be traceable through the strongest applicable set of fields:

```yaml
evidence_id: <stable or local evidence identifier>
source_type: <artifact|test|execution|data|analysis|governance>
source_reference: <path, command/result reference, test case, execution log, or data source>
subject: <fact/behavior/state being evidenced>
affected_stable_ids: []
parent_task_order: <TO-ID when applicable>
phase: <PH-ID when applicable>
step: <STEP-ID when applicable>
producer_or_executor: <role/person/process when applicable>
observed_at_utc: <timestamp when applicable>
content_or_version_reference: <commit/hash/version when applicable>
verification_status: <UNVERIFIED|VERIFIED|...>
```

Not every field is applicable to every evidence type. When provenance cannot be established sufficiently for the claim, the evidence remains `UNVERIFIED`.

## 4. Integrity and Reproducibility

Where practical and applicable, evidence SHOULD include a repository commit, content hash, immutable execution reference, test run identifier, or equivalent version context.

A hash or commit identifies content/version lineage. It does not by itself prove execution, correctness, or acceptance.

Deterministic verification evidence must be reproducible from the declared inputs and approved method. Pure mathematical claims must not depend on mutable external state unless that dependency is explicitly part of the approved verification method.

## 5. Evidence Hierarchy

For market intelligence, the project evidence hierarchy remains:

```text
Verified Real Market Data
→ Deterministic Computation
→ Market Structure
→ Derivatives / Order Flow
→ Specialist Outputs
→ AI Interpretation
→ Hypothesis
```

AI interpretation cannot override deterministic mathematical truth or fabricate missing market evidence.

For governance, authority follows the ratified governance and artifact chain. Governance evidence and analytical/data evidence are complementary, not interchangeable.

## 6. Independence

Producer-generated evidence is not independent verification of the Producer's own work.

The Producer may self-check within scope and must report actual results, but MUST NOT self-audit, self-verify, self-accept, self-ratify, or self-close the governed work.

CONTROL / REVIEWER (`ROL-V2-001`) remains the independent verification authority for the Producer artifact chain unless an applicable higher-authority process explicitly assigns another verifier.

Operator execution evidence is independently distinct from Producer evidence. The Operator records what was actually executed; the Operator does not grant architecture or governance authority through execution alone.

## 7. Lifecycle and Claim Rules

The following states remain distinct:

```text
DESIGNED
DRAFT
PROPOSED
APPROVED
IMPLEMENTED
EXECUTED
TESTED
VERIFIED
ACCEPTED
RATIFIED
FROZEN
CLOSED
```

Rules:

- Documentation of intended behavior is not execution evidence.
- `IMPLEMENTED` does not imply `EXECUTED`.
- `EXECUTED` does not imply `TESTED`.
- `TESTED` does not imply `VERIFIED`.
- `VERIFIED` does not imply `ACCEPTED` without the required acceptance authority/evidence.
- `ACCEPTED` does not imply `RATIFIED`.
- `RATIFIED` does not imply `FROZEN`.
- A Build Report is Producer evidence and remains unverified until independent audit.
- A gate is not closed merely because its requirements are described.

## 8. Negative, Missing, and Contradictory Evidence

The following must remain explicit:

- missing evidence;
- failed tests;
- unavailable execution output;
- stale evidence;
- contradictory evidence;
- insufficient sample/data coverage;
- unauthorized execution.

Negative evidence may demonstrate that a claim was not established. It must not be silently converted into positive evidence.

Contradictory evidence requires controlled reconciliation or an explicit unresolved disposition. It must not be silently discarded.

## 9. Acceptance / Verification / Ratification / Freeze Boundaries

**Verification** determines whether the available evidence supports the claimed result under the approved verification method.  
**Acceptance** is the decision of the authorized acceptance authority to accept that verified result for the defined scope.  
**Ratification** is the formal governance act of the authority entitled to ratify the relevant decision or artifact.  
**Freeze** establishes a controlled immutability boundary subject to the project's change process.  
**Closure** records that the applicable gate/Step/work item has satisfied its defined completion protocol.

These meanings must not be conflated.

## 10. Analytical/Data Evidence vs Governance Evidence

Analytical/data evidence answers questions about market facts, calculations, structure, and intelligence. Governance evidence answers questions about authorization, ownership, lifecycle, audit, acceptance, ratification, and freeze.

Examples:

- A valid market-data replay cannot prove that a Task Order was authorized.
- An authorized Task Order cannot prove that market data was valid.
- A passing deterministic test cannot prove production deployment.
- A ratified ADR cannot prove a runtime behavior that was never executed.
- A runtime observation cannot silently rewrite a higher-level architectural invariant.

## 11. Evidence for Gate Closure

Gate evidence must cover the gate's defined entry criteria and required evidence classes. Where applicable, the closure package must include:

1. gate identity and scope;
2. entry criteria evidence;
3. required structural evidence;
4. required behavioral/test evidence;
5. required operational evidence;
6. provenance and version context;
7. unresolved issues or explicit no-blocker disposition;
8. independent verification disposition;
9. authorized acceptance/closure decision;
10. resulting state transition and lineage.

A missing required evidence item is a gap, not an implicit pass.

## 12. Unauthorized Activity

Evidence generated through unauthorized runtime, deployment, V1/VPS mutation, market/trading/capital activity, or provider-runtime activity MUST NOT be used to legitimize the unauthorized action or silently convert it into approved project state.

The absence of unauthorized activity is a governance condition and, where required, must be supported by the appropriate execution/audit evidence rather than unsupported assertion.

## 13. Repository Authority

The GitHub repository is the authoritative project record. Chat messages, hidden model memory, informal summaries, or unrecorded local state do not override repository artifacts.

Historical evidence must retain its lineage. Corrections occur through the governed artifact process and must not silently invalidate prior evidence.

## 14. Current Status

This policy is `RECONCILED / PENDING CONTROL VERIFICATION` as part of `TO-P0-009`. Independent CONTROL audit remains required before this policy or `STEP-P0-008` may be treated as verified/complete.
