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
- Authority: the canonical 2026 Word template remains the source of truth for translation units. The change specification is a required reconciliation reference and does not silently add or replace canonical source text.

## Open source reconciliation issue
The change specification contains the liver-problem line `A liver transplant is not possible.` at table 0, row 31, column 2. That line is absent from the canonical 2026 Word template and from `data/source_units.jsonl`. This repository does not infer whether the line should be translated. The discrepancy must be resolved by the project owner or SPICT source authority before translation begins.

Exact SHA-256 values are stored in `sources/manifests/source_manifest.json`.
