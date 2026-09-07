# Source provenance

## Canonical source
- File: `20260521-Word-template-SPICT-4ALL-translations-2026.docx`
- Purpose: official editable translation template for SPICT-4ALL 2026.
- Rule: immutable; translated Finnish text is inserted only into a copy at final document generation.

## Visual reference
- File: `20260521-Word-template-SPICT-4ALL-translations-2026.pdf`
- Purpose: visual/layout reference for the 3-page template.

## Supporting guidance
- File: `20260130-Using-SPICT-4ALL-2025.docx`
- Purpose: official user-facing guidance/context. It is reference context, not a substitute for the 2026 translation template.

## Official change specification
- File: `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`
- Purpose: official change specification identifying 2025 changes in yellow and 2026 changes in green.
- Source URL: `https://www.spict.org.uk/wp-content/uploads/sites/74/2026/05/20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`
- Inspection: structurally inspected on 2026-09-07 without modifying or re-saving the file. The document contains one table, no tracked insertions/deletions, no comments, and highlighted change runs.
- Authority: the canonical 2026 Word template remains the canonical document/layout source. The change specification is authoritative evidence for its explicitly marked requirements, but it does not silently add or replace canonical source text.

## Source-derived change census
G0 derives the marked-change census directly from the hash-verified official DOCX. It recognises visible run-level `w:highlight` values `yellow` and `green`, plus the accent6 green font-colour mechanism used by the liver-transplant line. The immutable current change specification contains 32 yellow-highlighted visible runs, 4 green-highlighted visible runs, 1 accent6 green-font visible run, and 18 marked paragraph elements. Exactly one marked paragraph element is absent from the verified canonical source: `A liver transplant is not possible.`

Formatting counts only when it is attached to a `w:r` that contributes visible content through `w:t`, `w:tab`, `w:br`, `w:cr`, or an explicit soft/no-break hyphen. Paragraph properties and paragraph-mark-only formatting do not mark source text. Boundary layout whitespace is removed from paragraph source text; internal visible whitespace is preserved.

Canonical presence is determined only after manifest role, filename, byte count,
and SHA-256 verification. Text is scanned in every present relevant
WordprocessingML part: `word/document.xml`, `word/header*.xml`,
`word/footer*.xml`, `word/footnotes.xml`, and `word/endnotes.xml`. Source units
must match visible text at a typed location, directly or through an enumerated
layout-whitespace normalization. Source-unit JSONL and exception text are never
unioned into the canonical DOCX corpus.

## Source layers
1. `data/source_units.jsonl` records 53 indexed English units.
2. `data/canonical_unit_exceptions.jsonl` records normalization provenance for text already present in the canonical DOCX and typed authority status. It cannot create canonical text.
3. `data/source_requirements.jsonl` records official, provenance-linked requirements that are not canonical units. Requirement IDs use a separate `S4A-REQ-...` namespace.
4. A human/source-authority disposition decides whether an unresolved exception or requirement is included in the final source set. Translation or review evidence does not itself make that decision.

## Canonical title exception
`S4A-2026-000` independently resolves to visible text at
`word/header1.xml`, paragraph index 1. The DOCX text contains a Word line break
and adjacent layout whitespace between `Care` and `Indicators`. The only declared
normalization replaces the line break and adjacent horizontal layout whitespace
with one space. The exception records the exact pre-normalization text and hash,
normalized text, unit text and hash, canonical filename and hash, Word part,
paragraph index, extraction method, and normalization method. Verification
recomputes all relationships. Its existing `AUTHORITY_DECISION_REQUIRED` state
remains publication-blocking and ineligible for document insertion; approval
could change that authority state only because the text is already proven in the
canonical DOCX.

## Open source reconciliation issue
Requirement `S4A-REQ-2026-001` records the exact line `A liver transplant is not possible.` at table 0, row 31, column 2, paragraph 0. Its exact-text SHA-256 is `1b64512313b1820b42bf0692274c18740b11a2c395750605cfda023afcc7bc93`. OOXML inspection confirms the line is marked with the 2026 green font color (`w:val=385623`, theme `accent6`, shade `80`). The line is absent from the canonical 2026 Word template and canonical source-unit index.

The verifier requires every marked paragraph element absent from the canonical
DOCX to map by exact text and location to exactly one official change
requirement. A canonical unit, canonical exception, review state, or canonical
authority disposition cannot account for this line.

The discrepancy is `UNRESOLVED` and publication-blocking. It does not block G0, engineering, independent forward translation evidence, synthesis, blind back-translation, critique, or human adjudication. It blocks final source reconciliation, final publication while unresolved, and any claim that the final source set is authority-resolved. The line must not be inserted into the canonical template or final DOCX without an explicit source-authority/human inclusion disposition.

Requirement identifiers named in this document, including `S4A-REQ-2026-001`,
are examples from the current frozen source set in
`data/source_requirements.jsonl`. Verification and audit reporting derive the
current identifiers from that data. They are not a Python security allow-list.

Exact SHA-256 values are stored in `sources/manifests/source_manifest.json`.
