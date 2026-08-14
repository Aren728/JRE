# datasets/knowledge — JRE-004 catalogs

Versioned, checksummed data catalogs for the Classical Knowledge & Rule
Engine. All files are JSON documents carrying `catalog_id`,
`catalog_version`, `schema_version`, `source_citation`, and a
`checksum_sha256`.

## Checksum policy (SPEC §5.2, ADR-008)

- `checksum_sha256` is the SHA-256 of the catalog document **with the
  `checksum_sha256` field removed**, canonicalized as
  `json.dumps(document, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False)` (UTF-8). The loader (`models.read_catalog_file`)
  recomputes this and raises `CatalogIntegrityError` on mismatch.
- Any catalog change is a versioned decision (JSP-001 versioning rule):
  bump `catalog_version` (and re-pin `config/knowledge.toml` when pins are
  in force), then recompute the checksum.
- To recompute after editing:

```python
import json, hashlib, pathlib
p = pathlib.Path("datasets/knowledge/sources/sources.json")
doc = json.loads(p.read_text(encoding="utf-8"))
body = {k: v for k, v in doc.items() if k != "checksum_sha256"}
canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
print(hashlib.sha256(canonical.encode("utf-8")).hexdigest())
```

## Layout

| Path | Contents | Version |
|---|---|---|
| `sources/sources.json` | 7 classical sources + real bibliographic edition records (ADR-008) | `1.0.0` |
| `profiles/profiles.json` | 7 tradition profiles with explicit source priority (ADR-010) | `1.0.0` |
| `rules/rules:yoga.json` | `YOGA_DEFINITION` rules (incl. one `conflicts_with` pair + one `exception_for` chain) | `1.0.0` |
| `rules/rules:drishti.json` | `DRISHTI` rules | `1.0.0` |
| `rules/rules:karaka.json` | `KARAKA` / `BHAVA_MEANING` rules | `1.0.0` |

## Provenance and licenses

- The source registry holds bibliographic provenance only — no manuscript
  text, no prose corpora (request constraint, ADR-008).
- Edition records cite published English translations of classical Sanskrit
  works (see each entry's `editions` list). Exact bibliographic details are
  confirmed by the VALIDATOR stage.
- Rule conclusions are authored data citing chapter/verse of the listed
  editions; the engine never evaluates them (ADR-009).
