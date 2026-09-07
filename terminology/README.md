# Terminology evidence layer

This directory contains project-controlled Finnish terminology evidence. It is
separate from SPICT source authority.

- `sources/terminology_source_manifest.json` registers every local reference
  file by exact filename, bytes, SHA-256, provenance, role, and unresolved
  metadata.
- `sources/pdf_extraction_rules.json` permits only exact, page-located PDF
  fragments. CSV evidence is extracted from explicit columns and row IDs.
- `extracted/terminology_evidence.jsonl` contains source-provided discoveries;
  source text and later project interpretation are separate fields.
- `conflicts/terminology_conflicts.jsonl` retains mechanically detected
  conflicting definitions or candidate terms without resolving them.
- `terms.csv` is the project glossary decision queue. Only `APPROVED` rows with
  a human decision may become mandatory terminology.
- `reports/source_unit_terminology_map.tsv` uses conservative exact English
  phrase matching. Zero matches are valid.

Run `.\tools.ps1 -Task BuildTerminology` to rebuild generated evidence and
`.\tools.ps1 -Task ValidateTerminology` to verify source hashes, schema
constraints, reproducibility, conflicts, glossary state, mapping, and report.

`ValidateTerminology` does not own official SPICT source integrity. Unmanifested
files under `sources/official/` are rejected by `VerifySources`. Passing
terminology validation alone is not a complete repository source-integrity PASS.

Precedence is:
1. English SPICT source and official change requirements.
2. Verified official Finnish healthcare/palliative-care terminology evidence.
3. Other high-quality Finnish health/social-care reference evidence.
4. AI suggestions, which are candidates only.
5. Explicit human project decisions, which may become approved terminology.

Levels 2–5 can guide Finnish wording but cannot alter Level 1 meaning.
