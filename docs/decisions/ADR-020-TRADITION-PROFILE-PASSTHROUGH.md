# ADR-020 — Tradition-Profile Passthrough: Echo and Provenance Only (v0.2.0)

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (resolution of architecture §30.5)
- Decision maker: Specialist

## Context

JRE-004 has tradition profiles. JRE-005 must define an interface so a
caller can tag an analysis with a tradition **without** implementing
JRE-004 interpretation, and so any future tradition-specific behavior is
explicit and provenance-bearing rather than silent.

## Decision

1. **`BhavaConfig.tradition_profile: str | None`** — a validated
   passthrough: `None` or a non-empty string. JRE-005 does **not** look
   up JRE-004 profiles, does not parse them, and does **not** change any
   computation in v0.2.0 (all computation uses the pinned defaults).
   An unknown profile string is valid and must not raise.
2. **Provenance-bearing**: the value is echoed in
   `ChartEcho.tradition_profile` and in every `DerivationBlock` — every
   result records the profile it was computed under.
3. **Future tradition-specific behavior is explicit and versioned**:
   when a tradition genuinely changes computation (category tables,
   orbs, counting frames), it becomes an explicit versioned parameter or
   frame selection with its own derivation id — never a silent side
   effect of the passthrough string.
4. The passthrough stays **orthogonal to JRE-004 profile semantics**:
   JRE-005 treats the string as opaque; JRE-004's profile resolution is
   untouched.

Rationale:

- A validated, echoed passthrough gives consumers a place to declare
  tradition without coupling JRE-005 to JRE-004's profile machinery.
- Echo + provenance means the audit trail always records which tradition
  context a fact set was produced under, even when the computation is
  identical.

Rejected alternatives:

- **No hook at all** — future tradition-aware behavior would need a
  breaking config change; the passthrough is the additive seam.
- **Parse JRE-004 profiles in JRE-005** — duplicates JRE-004 resolution
  and couples layers (forbidden boundary, ADR-013).
- **Tradition-dependent computation now** — no tradition-specific
  computation is validated for v0.2.0; adding it later is versioned.

## Consequences

- `tradition_profile` omitted from `config/bhava.toml` (TOML has no
  null) → `None` default; settable via API/config dict.
- TEST-PLAN §5a: echo + provenance + no-computation-change assertions.

## References

- [JRE-005 architecture §30.5](../architecture/JRE-005-BHAVA-CORE.md)
- [JRE-005 specialist spec §32](../architecture/JRE-005-SPECIALIST-SPEC.md)
- [JRE-004 tradition profiles (ADR-010)](ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md)
