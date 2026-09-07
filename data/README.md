# Machine-readable source index

`source_units.jsonl` contains 53 extracted source units from the canonical SPICT-4ALL 2026 translation template plus the rendered title as unit `S4A-2026-000`.

`canonical_unit_exceptions.jsonl` records an enumerated normalization for visible
text that already exists at a typed location in the canonical DOCX. It records
pre- and post-normalization text and hashes and cannot create canonical content.
The current title normalization is source-proven; its separate authority state
remains authority-required, publication-blocking, and non-insertable.

`source_requirements.jsonl` contains provenance-linked official change requirements in a separate `S4A-REQ-...` namespace. These records may require translation evidence but do not automatically become canonical document content. Identifiers currently present in that file are the frozen source set; commands and audit reports derive them from the data rather than from a Python allow-list.

The manifest-verified canonical DOCX remains the canonical document/layout and
normal-text source. Source-unit JSONL text never expands the canonical corpus.
Final inclusion of an unresolved exception or requirement requires an explicit
human/source-authority disposition.

`governance_integrity_manifest.json` records hashes and byte counts for the two
mutable project governance JSONL files. It is not an official-source manifest and
does not make those files immutable. Its trust anchor is tracked Git history and
the external audit archive/index; changing governance data requires an explicit
ledger regeneration, avoiding self-referential hashes.

`Sanasto/` contains non-authoritative Finnish terminology/reference material.
Its separate manifest is under `terminology/sources/`; nothing in `Sanasto/` may
alter the English source corpus.
