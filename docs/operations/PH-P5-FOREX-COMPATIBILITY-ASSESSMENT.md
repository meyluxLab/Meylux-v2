# PH-P5 Forex Compatibility Assessment — Paper-Only

**Status:** CONTROL assessment; no implementation authorization
**Scope:** Future product intent only; no Forex acquisition, code, VPS action, credentials, or provider activation.

## Findings

### (a) ProviderAdapter / canonical instrument / quality model

The existing `ProviderAdapter` is provider-neutral and capability-oriented. It exposes immutable provider identity and a capability sequence; provider-specific I/O remains behind the adapter boundary.

`CanonicalInstrument` already contains `market_type`, `contract_type`, `contract_multiplier`, precision fields, active state, provenance and time semantics. This provides a structural place for a future Forex instrument without requiring a new top-level provider abstraction.

The existing acquisition/data-quality architecture also distinguishes availability/invalidity rather than requiring a fabricated numeric fallback. On the evidence reviewed, no architectural obstacle was found that inherently prevents a future Forex adapter.

### (b) Credentials and secret handling

The current environment contract explicitly prohibits provider/market credentials in the foundation-only `/srv/meylux-v2/.env` mechanism. Staging/production secrets must use an explicitly governed environment-specific secret-handling mechanism. A future Forex provider requiring credentials would therefore require provider-specific secret material through that governed mechanism; it must not be added to repository or chat.

### (c) Weekend / session closure

The canonical model already supports explicit unavailable/gap/quality states, and the project rule is to detect and classify missing/invalid data rather than silently repair it. Forex weekend closure and venue session calendars would therefore need to be represented through the existing explicit availability/gap/quality semantics. A future implementation may require provider/session-calendar fields or rules if the concrete source exposes semantics that cannot be represented by existing contracts. That is an implementation-time assessment, not an authorization to add them now.

### (d) Work classification

**Preliminary classification:** bounded-additive-under-P2 appears structurally plausible, because the existing provider abstraction and canonical instrument contract already provide the main extension points and no frozen architecture restriction to crypto venues was identified in the inspected artifacts. This is not a final change-control determination: the actual future provider, wire semantics, authentication requirements, instrument/session model and concrete contract delta must be assessed when Forex is authorized. If those facts require a frozen architectural change, formal ADR/change control is required.

## Evidence basis

- `src/meylux/acquisition/provider.py`
- `src/meylux/acquisition/binance.py`
- `src/meylux/acquisition/mexc.py`
- `contracts/canonical/instrument.py`
- `docs/environment/ENVIRONMENT_MANIFEST.yaml`
- `DOC-V2-ARCH-001`
- `DOC-P5-001`

This assessment does not authorize Forex implementation.
