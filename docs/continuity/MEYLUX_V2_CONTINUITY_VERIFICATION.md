# MEYLUX V2 — CONTINUITY VERIFICATION

Produce one concise report after the bootstrap reading sequence.

Use exactly these fields:

```text
PROJECT:
SOURCE OF TRUTH:
ARCHITECTURE STATE:
CURRENT CHECKPOINT:
CURRENT GATE:
CURRENT PHASE:
CURRENT STEP:
OPEN QUESTIONS:
DEFERRED DECISIONS:
ACTIVE TASK:
LATEST VERIFIED COMMIT:
NEXT AUTHORIZED ACTION:
CONTINUITY STATUS:
```

## Verification rules

- Report only facts established by authoritative artifacts.
- `CURRENT_STEP` may be `NOT ESTABLISHED` when no active step is authorized.
- `ACTIVE TASK` may be `NONE / NOT ESTABLISHED` when no active Task Order is present.
- Do not infer an active Phase 0 step from the future continuation boundary.
- Treat `2e2415ffba14c253e1927f4214285639ffbdb214` as the supplied transfer baseline commit unless a newer authoritative repository checkpoint supersedes it.
- Do not convert package preparation into independent GitHub verification.
- Do not declare Phase 0 authorized.
- If a genuine conflict exists between repository artifacts, report the conflict and stop only the affected action.
- If no genuine conflict exists, do not manufacture uncertainty.

## Information vs execution

Information required to understand state:
- identity, mission, Source of Truth, architecture status, checkpoint, gates, formation state, Registry state, repository baseline, VPS boundary, Open Questions, Deferred Decisions.

Information required to execute the next task:
- the specific active/approved Task Order, its affected SIDs/paths, required evidence, and any Operator execution prerequisites.

Do not require the entire historical chat when these are already available in authoritative artifacts.
