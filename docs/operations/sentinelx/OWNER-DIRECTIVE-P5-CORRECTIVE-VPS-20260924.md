# PROJECT OWNER — CORRECTIVE VPS RECONCILIATION, SYNCHRONIZATION AND BRING-UP

**Date:** 2026-09-24  
**Phase:** PH-P5  
**Current completed Step:** STEP-P5-002  
**Authority:** PROJECT OWNER  
**Execution authority:** CONTROL / REVIEWER (ROL-V2-001)  
**VPS mechanism:** SentinelX only

## Purpose

This document is the durable repository record of the Project Owner directive authorizing bounded corrective VPS reconciliation and bring-up to resolve the evidenced P5 runtime synchronization gap.

The authorization is corrective/runtime-reconciliation only. It does not reopen completed implementation work, activate STEP-P5-003, authorize new P5 product functionality, or retroactively attribute corrective execution to TO-P5-001 or TO-P5-002.

## Authorized objective

CONTROL is authorized, after independent pre-mutation reconciliation, to:

1. synchronize /srv/meylux-v2 to the correct governed main revision;
2. reconcile actual database migration state against the repository migration chain;
3. apply 0007_specialist_foundation.sql when verified as the next authorized migration;
4. bring up the existing governed compose stack;
5. verify database/schema/privilege/runtime integrity;
6. verify preservation of existing persisted data;
7. determine, from authoritative runtime evidence, whether P5 persisted facts satisfy AVAILABLE_PERSISTED.

## Prohibitions

No architecture change, new service, provider activation, secret change, trading/capital/custody activity, Futures/Forex implementation, modification of migrations 0001–0006, destructive database operation, volume reset/replacement, cleanup unrelated to the corrective objective, or retroactive historical rewriting is authorized.

## Historical integrity

The Roadmap-to-Task-Order VPS discrepancy remains historically visible. Corrective execution is recorded as new CONTROL execution and is not attributed to TO-P5-001 or TO-P5-002.

## Closure ownership

CONTROL owns execution evidence, independent verification, and ADR-GOVERNANCE-012 peripheral synchronization. STEP-P5-002 remains COMPLETE / VERIFIED and PH-P5 remains ACTIVE / AUTHORIZED unless a separate governed lifecycle action changes those states.
