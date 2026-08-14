# ADR-010 — Tradition Profiles, Rule Precedence, and Conflict Resolution

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-004 Classical Knowledge & Rule Engine](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect

## Context

Classical Jyotish is not a single doctrine: BPHS, Bṛhat Jātaka, Jātaka
Pārijāta, Phaladīpikā, Sūrya Siddhānta, and regional schools disagree on
specifics. JRE-004 must incorporate all of them without choosing silently:
every synthesis must be attributable to a named tradition, rules from
different sources must have a deterministic order, and genuine disagreements
must be surfaced rather than hidden.

## Decision

### 1. Tradition profiles are first-class, explicit, versioned data

- A `TraditionProfile` names its included sources, an **explicit
  `source_priority` order**, a `conflict_policy` (`FIRST_WINS` /
  `REPORT_ALL`), an optional domain scope, and passthrough config that is
  echoed but never interpreted.
- Initial profiles: `bphs-classical` (default), `brihat-jataka`,
  `jataka-parijata`, `phaladeepika`, `surya-siddhanta-vedanga`,
  `regional-*`.
- A synthesis always resolves a profile; there is no unprofiled mode. The
  default profile is explicit in `config/knowledge.toml`.

### 2. Precedence is a deterministic total order

Within a profile, matched rules are ordered by (higher first):

1. rank of primary `source_id` in the profile's `source_priority`;
2. rule specificity (number of condition atoms);
3. authored `authority_tier`;
4. `rule_version` (semver, newer first);
5. `rule_id` lexicographic tiebreak.

`precedence.py` is a pure comparator; the algorithm name is echoed in
`SearchMetadata`.

### 3. Conflicts are detected and resolved explicitly — never silently

- Detection: ACTIVE rules in the same domain with authored
  `conflicts_with` pairs (structural contradiction validation catches
  malformed declarations).
- `FIRST_WINS`: the higher-precedence rule is kept; the loser moves to
  `suppressed_rules`; a `ConflictRecord` with the reason and policy is
  **always** emitted.
- `REPORT_ALL`: nothing is suppressed; both rules are returned with a
  `ConflictRecord` noting the disagreement.
- There is no hidden override path: resolution is a function of the profile,
  the catalog, and the query.

Rationale:

- The request demands "conflict-resolution mechanism", "tradition profiles",
  and "rule precedence" as separate, explicit capabilities. Encoding the
  tradition as data with an explicit priority order is the only way to let
  the same engine serve BPHS-classical and regional consumers without mixing
  systems (mirrors JRE-003's "explicit house systems, never mixed").
- Recording every suppression preserves auditability and lets future
  synthesis layers weigh disagreements instead of hiding them.

Rejected alternatives:

- **Global rule priority** (no profiles) — silently imposes one tradition on
  all consumers; violates the "no hidden defaults" requirement.
- **Silent last-write-wins** — information-destroying and non-auditable.
- **Weighted scoring of sources** — arbitrary, non-reproducible across
  authors; the explicit order is reviewable data.

## Consequences

- All six initial profiles ship with documented priority orders.
- Precedence and both conflict policies are unit-tested with golden catalogs.
- `SynthesisResult` always exposes `profile`, `conflicts`, and
  `suppressed_rules` so consumers can audit every choice.

## References

- [JRE-004 Architecture §10–§12](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- [JRE-004 Data Contract §5–§6](../architecture/JRE-004-DATA-CONTRACT.md)
- [JRE-003 Architecture: explicit house systems §9](../architecture/JRE-003-JYOTISH-CORE.md)
