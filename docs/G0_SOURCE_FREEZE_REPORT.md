# WP-G0-SOURCE-FREEZE-001 report

Date: 2026-09-07  
Repository: `F:\-DEV-\120.Samin-PDF`  
Baseline Git commit: `4f4cb3ffd61b2366d6c4aae507916eca2932bf36`

## Outcome

G0 source freeze passes after the R1 independent-review remediation documented below. All four official source files remain unchanged and hash verified. The 53 canonical source units remain unchanged, unique, contiguous, and exact-text hash matched. One official source requirement is recorded in a separate stable namespace and verified against its exact OOXML source location and 2026 marking.

The source requirement participates in translation evidence preparation but is not a canonical source unit and cannot be inserted automatically into a final DOCX. Its final inclusion remains unresolved.

## Official source hashes

- `20260130-Using-SPICT-4ALL-2025.docx`: `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca` (111045 bytes)
- `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`: `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d` (68949 bytes)
- `20260521-Word-template-SPICT-4ALL-translations-2026.docx`: `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581` (66914 bytes)
- `20260521-Word-template-SPICT-4ALL-translations-2026.pdf`: `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72` (223468 bytes)

Canonical source-unit count: 53.  
Official source-requirement count: 1.  
Translation-evidence source count after G0: 54.

## Unresolved conflicts

1. `S4A-REQ-2026-001`
   - Exact English: `A liver transplant is not possible.`
   - Exact-text SHA-256: `1b64512313b1820b42bf0692274c18740b11a2c395750605cfda023afcc7bc93`
   - Official source: `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`
   - Provenance: `word/document.xml`, table 0, row 31, column 2, paragraph 0
   - 2026 marking: font color `w:val=385623`, theme `accent6`, shade `80`
   - Canonical source presence: false
   - Final inclusion: `UNRESOLVED`
   - Publication blocking: true
2. `S4A-2026-000`
   - Translation and review evidence may be prepared.
   - Authoritative final title wording still requires human/source-authority disposition.

## Blocker semantics

The unresolved discrepancies do not block canonical source verification, G0, engineering, independent Agent A or Agent B evidence preparation, synthesis, blind back-translation, critic review, or human adjudication.

They block final source reconciliation. `S4A-REQ-2026-001` blocks final publication while unresolved. Neither discrepancy permits a claim that the final source set is authority-resolved.

## Files created

- `data/source_requirements.jsonl`
- `docs/G0_SOURCE_FREEZE_REPORT.md`
- `schemas/source_requirement.schema.json`
- `scripts/create_g0_audit_zip.py`
- `src/spict4all/requirements.py`
- `tests/test_requirements.py`
- `deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip`
- `deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip.sha256`

## Files changed

- `.gitignore`
- `README.md`
- `config/quality_gates.yaml`
- `data/README.md`
- `docs/METHODOLOGY.md`
- `docs/OFFICIAL_TRANSLATION_GUIDANCE.md`
- `docs/SOURCE_PROVENANCE.md`
- `docs/WORKFLOW.md`
- `prompts/01-agent-a-forward.md`
- `prompts/02-agent-b-forward.md`
- `prompts/03-agent-c-synthesis.md`
- `schemas/translation_candidate.schema.json`
- `src/spict4all/artifacts.py`
- `src/spict4all/cli.py`
- `src/spict4all/gates.py`
- `tests/test_artifacts.py`
- `tools.ps1`

No file under `sources/official/` was modified, renamed, rewritten, or regenerated.

## Tests and checks

- `.\tools.ps1 -Task Test`: PASS=50, FAIL=0; audit-packaging run result `50 passed in 0.72s`.
- `.\tools.ps1 -Task VerifySources`: PASS=6, FAIL=0; four official files, 53 canonical units, and one official requirement verified.
- `.\tools.ps1 -Task ValidateRequirements`: PASS=1, FAIL=0.
- `.venv\Scripts\python.exe -m compileall -q src scripts tests`: PASS=1, FAIL=0; exit code 0 with no output.
- Total counted checks: PASS=58, FAIL=0.
- Audit ZIP open: PASS=1, FAIL=0.
- Audit ZIP CRC: PASS=1, FAIL=0.
- Archived-file index SHA-256 verification: PASS=89, FAIL=0.
- Required official archive members: PASS=4, FAIL=0.
- Forbidden archive members: 0.

Source verification result: PASS. The exact change-spec text, text hash, source-file linkage, source-file hash, source role, OOXML location and 2026 marking were verified. Exact absence from the canonical Word template was verified. Source-derived marked-change completeness prevents the conflict from silently disappearing.

## Assumptions and decisions

- The canonical Word template remains the canonical document/layout source.
- The official change specification is authoritative evidence that its explicitly marked 2026 requirement exists.
- No inference was made about final inclusion.
- `AUTHORITY_DECISION_REQUIRED` on `S4A-2026-000` remains an authority blocker for final wording, not a translation-stage blocker.
- Per the project owner's selected audit convention, the exact final ZIP SHA-256 is stored in an external `.sha256` sidecar because an archive cannot contain its own final SHA-256 without changing that hash.

## Remaining blockers

- Human/source-authority inclusion or exclusion disposition for `S4A-REQ-2026-001`.
- Human/source-authority disposition for authoritative final title wording in `S4A-2026-000`.
- The bootstrap-noted page-image inspection limitation remains separate from this G0 source-freeze verification.

## Git status

Expected final uncommitted status after audit packaging:

```text
 M .gitignore
 M README.md
 M config/quality_gates.yaml
 M data/README.md
 M docs/METHODOLOGY.md
 M docs/OFFICIAL_TRANSLATION_GUIDANCE.md
 M docs/SOURCE_PROVENANCE.md
 M docs/WORKFLOW.md
 M prompts/01-agent-a-forward.md
 M prompts/02-agent-b-forward.md
 M prompts/03-agent-c-synthesis.md
 M schemas/translation_candidate.schema.json
 M src/spict4all/artifacts.py
 M src/spict4all/cli.py
 M src/spict4all/gates.py
 M tests/test_artifacts.py
 M tools.ps1
?? data/source_requirements.jsonl
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip.sha256
?? docs/G0_SOURCE_FREEZE_REPORT.md
?? schemas/source_requirement.schema.json
?? scripts/create_g0_audit_zip.py
?? src/spict4all/requirements.py
?? tests/test_requirements.py
```

`git diff --stat` for tracked files before packaging:

```text
 .gitignore                                |  1 +
 README.md                                 |  9 +++-
 config/quality_gates.yaml                 | 18 ++++---
 data/README.md                            |  4 +-
 docs/METHODOLOGY.md                       |  9 +++-
 docs/OFFICIAL_TRANSLATION_GUIDANCE.md     |  7 +++
 docs/SOURCE_PROVENANCE.md                 | 11 +++-
 docs/WORKFLOW.md                          | 19 +++++--
 prompts/01-agent-a-forward.md             |  6 ++-
 prompts/02-agent-b-forward.md             |  2 +-
 prompts/03-agent-c-synthesis.md           |  3 +-
 schemas/translation_candidate.schema.json |  2 +-
 src/spict4all/artifacts.py                | 17 +++++--
 src/spict4all/cli.py                      | 83 +++++++++++++++++++++++++++----
 src/spict4all/gates.py                    | 59 ++++++++++++++++++++++
 tests/test_artifacts.py                   | 15 ++++++
 tools.ps1                                 |  5 +-
 17 files changed, 233 insertions(+), 37 deletions(-)
```

Nothing was committed or pushed.

## No-translation confirmation

No Finnish translation content, Finnish candidate, model-generated translation, Agent A run, or Agent B run was created during WP-G0-SOURCE-FREEZE-001. No model API was called.

## R1 independent-review remediation

Work package: `WP-G0-SOURCE-FREEZE-001-R1`  
Baseline Git commit remains: `4f4cb3ffd61b2366d6c4aae507916eca2932bf36`

### HIGH findings

**HIGH-1 — Change-spec completeness must be derived: FIXED**

- Implementation: `requirements.py` now enumerates relevant WordprocessingML parts, extracts visible text from individual `w:r` runs, recognises yellow and green `w:highlight` markers plus accent6 font-colour markers, records exact part/table/row/column/paragraph provenance, and derives completeness from the official DOCX. Every marked paragraph element must match canonical content or a source requirement.
- The in-code expected requirement-ID allow-list was removed. New requirements need data records, not Python allow-list changes.
- Regression tests: `test_current_change_spec_marker_census_passes`, `test_undiscovered_marked_paragraph_fails`, `test_legitimate_additional_requirements_need_no_python_allow_list`, and `test_disappearing_known_requirement_fails_source_derived_completeness`.
- Final status: PASS.

**HIGH-2 — Canonical source must always be verified: FIXED**

- Implementation: canonical-presence and completeness paths first locate the unique manifest entry with role `canonical_source`, then verify filename linkage, byte count, and SHA-256 before parsing any canonical OOXML.
- Regression test: `test_corrupted_canonical_template_fails_before_presence_scan`.
- Final status: PASS.

### MEDIUM findings

**MEDIUM-1 — Verify marking on visible text runs: FIXED**

- Implementation: markers are accepted only from the specific visible `w:r/w:rPr` run. Paragraph properties and paragraph-mark-only formatting are excluded.
- Regression test: `test_invisible_paragraph_mark_formatting_cannot_satisfy_marking`.
- Final status: PASS.

**MEDIUM-2 — Scan all relevant Word parts: FIXED**

- Implementation: reusable part enumeration scans `word/document.xml`, `word/header*.xml`, `word/footer*.xml`, `word/footnotes.xml`, and `word/endnotes.xml` when present. Provenance records `document_part`.
- Regression test: `test_canonical_text_in_header_is_detected`.
- Final status: PASS.

**MEDIUM-3 — Publication-blocking semantics: FIXED**

- Implementation: JSON Schema and the `SourceRequirement` domain model require unresolved canonical omissions to remain authority-required, `UNRESOLVED`, and publication-blocking. Executable publication gates defensively treat unresolved canonical omissions as blockers. Only a resolved authority disposition with `INCLUDE` or `EXCLUDE` can downgrade the stored blocker.
- Regression tests: `test_unresolved_publication_blocking_true_passes`, `test_unresolved_publication_blocking_false_fails`, `test_unresolved_publication_blocker_is_enforced_by_domain_model`, `test_resolved_authority_disposition_path_can_downgrade_blocker`, and `test_unresolved_conflict_blocks_reconciliation_and_publication`.
- Final status: PASS.

**MEDIUM-4 — Remove hardcoded expected requirement IDs: FIXED**

- Implementation: `EXPECTED_REQUIREMENT_IDS` was removed. Omission detection is derived from marked official source text. The current liver requirement disappears only if its source-derived unaccounted paragraph also disappears, which cannot occur without an official source hash change.
- Regression tests: `test_legitimate_additional_requirements_need_no_python_allow_list` and `test_disappearing_known_requirement_fails_source_derived_completeness`.
- Final status: PASS.

**MEDIUM-5 — Type the evidence-source contract: FIXED**

- Implementation: immutable `EvidenceSource`, `EvidenceProvenance`, `EvidenceSourceKind`, and `FinalInclusionStatus` types now carry explicit text, hash, provenance, evidence/review requirements, final inclusion state, and document-insertion eligibility. Stage-7 selection uses only explicit `eligible_for_document_insertion`.
- Canonical units are eligible. The unresolved official requirement is ineligible. Only an explicit authority `INCLUDE` disposition makes a requirement eligible.
- Regression tests: `test_typed_evidence_source_document_eligibility`, `test_unresolved_requirement_cannot_be_made_docx_insertable`, and `test_invalid_evidence_source_kind_fails`.
- Final status: PASS.

### Low-risk related items

- Accumulated requirement validation failures: FIXED.
- Exact OOXML visible-text rules documented in code and `docs/SOURCE_PROVENANCE.md`: FIXED.
- Audit wording no longer claims byte-for-byte ZIP determinism; timestamps and captured Git state intentionally vary: FIXED.
- Forbidden-member verification includes five known-bad probes, one safe probe, and actual archive-member checking: FIXED.
- Final checks report source-authority blockers before attempting to load release-ready translated review artifacts: FIXED; regression test `test_final_cli_reports_source_authority_before_missing_review_files`.
- `PENDING_AUTHORITY` review disposition for unresolved noncanonical requirements: FIXED; regression test `test_pending_authority_is_valid_for_unresolved_requirement`.
- Deferred low-risk items: none.

### R1 source verification

- Official source hashes remain:
  - `20260130-Using-SPICT-4ALL-2025.docx`: `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca`
  - `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`: `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.docx`: `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.pdf`: `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72`
- Canonical source-unit count: 53.
- Official source-requirement count: 1.
- Marked-change census: 32 yellow-highlighted runs; 4 green-highlighted runs; 1 accent6 green-font run; 18 marked paragraph elements.
- Marked paragraphs absent from canonical: exactly 1 — `A liver transplant is not possible.`

### R1 authority status

- `S4A-REQ-2026-001`: exact official evidence; absent from canonical; translation evidence required; final inclusion `UNRESOLVED`; authority confirmation required; publication-blocking; not a translation-stage blocker.
- `S4A-2026-000`: authoritative final title wording remains unresolved; translation and review evidence may proceed.

### R1 checks

- `.\tools.ps1 -Task Test`: PASS=64, FAIL=0; `64 passed in 2.04s`.
- `.\tools.ps1 -Task VerifySources`: PASS=6, FAIL=0.
- `.\tools.ps1 -Task ValidateRequirements`: PASS=1, FAIL=0.
- `.venv\Scripts\python.exe -m compileall -q src scripts tests`: PASS=1, FAIL=0.
- Counted checks: PASS=72, FAIL=0.

### R1 files

R1 adds `src/spict4all/evidence.py` and `scripts/create_g0_r1_audit_zip.py`; it substantially extends `src/spict4all/requirements.py`, its schema and tests, and updates the CLI, evidence consumers, executable gates, reviews, workflow documentation, quality gates, report, and audit tooling. No official source file changed.

### R1 final Git status

The final uncommitted status includes 22 modified tracked files and 12 untracked files:

```text
 M .gitignore
 M README.md
 M config/quality_gates.yaml
 M data/README.md
 M docs/METHODOLOGY.md
 M docs/OFFICIAL_TRANSLATION_GUIDANCE.md
 M docs/SOURCE_PROVENANCE.md
 M docs/WORKFLOW.md
 M prompts/01-agent-a-forward.md
 M prompts/02-agent-b-forward.md
 M prompts/03-agent-c-synthesis.md
 M schemas/translation_candidate.schema.json
 M scripts/create_audit_zip.py
 M src/spict4all/artifacts.py
 M src/spict4all/cli.py
 M src/spict4all/coverage.py
 M src/spict4all/gates.py
 M src/spict4all/reports.py
 M src/spict4all/reviews.py
 M tests/test_artifacts.py
 M tests/test_reviews_and_gates.py
 M tools.ps1
?? data/source_requirements.jsonl
?? deliverables/audit/SPICT4ALL-FI-G0-R1-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-R1-source-freeze-audit-20260907.zip.sha256
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip.sha256
?? docs/G0_SOURCE_FREEZE_REPORT.md
?? schemas/source_requirement.schema.json
?? scripts/create_g0_audit_zip.py
?? scripts/create_g0_r1_audit_zip.py
?? src/spict4all/evidence.py
?? src/spict4all/requirements.py
?? tests/test_requirements.py
```

Tracked `git diff --stat` before R1 audit packaging:

```text
 .gitignore                                |   1 +
 README.md                                 |   9 ++-
 config/quality_gates.yaml                 |  19 ++++--
 data/README.md                            |   4 +-
 docs/METHODOLOGY.md                       |  11 +++-
 docs/OFFICIAL_TRANSLATION_GUIDANCE.md     |   7 ++
 docs/SOURCE_PROVENANCE.md                 |  18 ++++-
 docs/WORKFLOW.md                          |  24 +++++--
 prompts/01-agent-a-forward.md             |   6 +-
 prompts/02-agent-b-forward.md             |   2 +-
 prompts/03-agent-c-synthesis.md           |   3 +-
 schemas/translation_candidate.schema.json |   2 +-
 scripts/create_audit_zip.py               |   2 +-
 src/spict4all/artifacts.py                |  34 ++++++++--
 src/spict4all/cli.py                      | 105 +++++++++++++++++++++++++++---
 src/spict4all/coverage.py                 |  14 +++-
 src/spict4all/gates.py                    |  64 ++++++++++++++++++
 src/spict4all/reports.py                  |  16 ++++-
 src/spict4all/reviews.py                  |  31 +++++++--
 tests/test_artifacts.py                   |  15 +++++
 tests/test_reviews_and_gates.py           |  54 +++++++++++++++
 tools.ps1                                 |   5 +-
 22 files changed, 396 insertions(+), 50 deletions(-)
```

No commit or push was performed.

### R1 no-translation confirmation

No Finnish translation content, Finnish candidate, model-generated translation, Agent A run, or Agent B run was created during R1. No model API was called.

## R2 independent-review remediation

Work package: `WP-G0-SOURCE-FREEZE-001-R2`  
Baseline Git commit remains: `4f4cb3ffd61b2366d6c4aae507916eca2932bf36`

### HIGH-A — canonical unit text must be proven against canonical DOCX: FIXED

- The manifest role, filename, byte count, and SHA-256 of the canonical DOCX are
  verified before any unit resolution.
- `verify_canonical_units_against_source` validates source-unit IDs, uniqueness,
  exact-text hashes, typed authority status, and exact text at the recorded
  WordprocessingML table/row/column/paragraph location.
- The canonical corpus is built only from visible text in the verified DOCX.
  Source-unit JSONL text is never unioned into it.
- Unmatched units require a unique, schema-validated, unit-hash and
  canonical-file-hash-linked record in `data/canonical_unit_exceptions.jsonl`.
- Evidence sources can be built only from a completed canonical verification.
  An unresolved source—canonical exception or official requirement—cannot be
  document-insertable.
- Result: 53/53 units resolved; 52 direct DOCX resolutions and 1 explicit
  exception.
- Anti-laundering regressions:
  `test_liver_requirement_cannot_be_laundered_into_canonical_namespace` hard
  fails when the requirement is removed and the liver line is added as a
  self-hashed canonical unit;
  `test_unresolved_laundered_liver_exception_is_never_insertable` proves an
  unresolved exception remains non-insertable and still cannot satisfy
  change-spec completeness.
- Final status: PASS.

### `S4A-2026-000` exception/provenance status

The title does not resolve as an exact visible canonical DOCX paragraph. Its
machine-readable exception records the unit ID and source hash, exception type,
canonical DOCX filename and SHA-256, the existing `page header / template title`
source reference, why exact paragraph matching is not applicable, and typed
authority/evidence states. It remains `AUTHORITY_DECISION_REQUIRED`,
publication-blocking, and non-insertable. Translation evidence may proceed, but
this record does not assert final authoritative title wording.

### MEDIUM-A — canonical unit authority status must be typed: FIXED

- `TranslationStatus` permits only `UNTRANSLATED`,
  `AUTHORITY_DECISION_REQUIRED`, and `AUTHORITY_RESOLVED`; typo and arbitrary
  values fail.
- A resolved canonical exception requires a schema-validated, unit-linked
  disposition containing decision, decision maker/authority, decision date,
  evidence reference, and final status.
- Publication and reconciliation gates consume the verified canonical
  resolution object rather than free-text source-unit status.
- Regressions cover typo/arbitrary status, blocker clearing without a
  disposition, unresolved-final prevention, disposition unit linkage, valid
  authority disposition, and the continuing `S4A-2026-000` blocker.
- Final status: PASS.

### LOW findings

- **LOW-1 — static analysis: FIXED.** Pinned `mypy==1.18.2`,
  `ruff==0.13.2`, and type stubs were added to project and lock configuration.
  Reproducible `TypeCheck` and `Lint` tasks were added. Mypy strict and Ruff
  pass without broad code reformatting.
- **LOW-2 — change year schema: FIXED.** Only 2025 and 2026 are accepted.
  Year-specific marking semantics require yellow highlight for 2025 and green
  highlight/accent6 font colour for 2026. Regressions cover both supported
  years and one unsupported year.
- **LOW-3 — empty Finnish candidate: FIXED.** Completed candidate states
  require `candidate_fi` `minLength: 1`; an empty `DRAFT` separately represents
  a not-yet-generated candidate. Tests use fixture text only and generate no
  Finnish translation.
- **LOW-4 — census wording: FIXED.** Documentation and command output now say
  `marked paragraph elements`; no deduplication claim is made.

### R2 source and authority results

- Official source hashes remain:
  - `20260130-Using-SPICT-4ALL-2025.docx`: `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca`
  - `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`: `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.docx`: `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.pdf`: `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72`
- Canonical source-unit count: 53; original index SHA-256 remains
  `f4751a7e67ff42338fc5c23a842cc7af07c03f2c6a394dea1819f26546c127a5`.
- Canonical-unit exception count: 1.
- Official source-requirement count: 1.
- Marked-change census: 32 yellow-highlighted visible runs, 4
  green-highlighted visible runs, 1 accent6 green-font visible run, and 18
  marked paragraph elements.
- Unresolved authority conflicts:
  - `S4A-2026-000`: final authoritative title wording unresolved.
  - `S4A-REQ-2026-001`: final inclusion unresolved and publication-blocking.
- G0 passes because both conflicts are explicit and provenance-linked.
  Publication and final source reconciliation remain blocked.

### R2 exact checks

- `.\tools.ps1 -Task Test`: PASS; `87 passed in 3.84s`, FAIL=0.
- `.\tools.ps1 -Task VerifySources`: PASS=6, FAIL=0.
- `.\tools.ps1 -Task ValidateCanonical`: PASS=1, FAIL=0; 53 resolved,
  52 direct, 1 exception.
- `.\tools.ps1 -Task ValidateRequirements`: PASS=1, FAIL=0.
- `.venv\Scripts\python.exe -m mypy --strict src/spict4all`: PASS;
  no issues in 15 source files.
- `.venv\Scripts\python.exe -m ruff check src scripts tests`: PASS; all
  checks passed.
- `.venv\Scripts\python.exe -m compileall -q src scripts tests`: PASS,
  exit code 0 with no output.
- `git diff --check`: PASS.
- `git diff -- sources/official`: empty; no official source changed.

### R2 Git status before audit creation

The uncommitted working tree contained 29 modified tracked files and 16
reviewable untracked files (45 status entries total). The tracked aggregate diff
was 623 insertions and 68 deletions across 29 files. This includes the
uncommitted G0 and R1 work; R2 did not commit or push.

### R2 no-translation confirmation

No Finnish translation content, Finnish candidate, model-generated translation,
Agent A run, or Agent B run was created during R2. No model API was called.

## R3 adversarial remediation and terminology foundation

Work package:
`WP-G0-SOURCE-FREEZE-001-R3-AND-TERMINOLOGY-FOUNDATION`  
Baseline Git commit remains: `4f4cb3ffd61b2366d6c4aae507916eca2932bf36`

### Correction to historical R2 status

The R2 section above is retained as the status reported at that review. A later
adversarial review demonstrated that its HIGH-A conclusion was incomplete:
`APPROVE_CANONICAL_EXCEPTION` could make arbitrary absent text canonical and
document-insertable. R3 therefore re-opened that finding and replaced
exception-authorized text creation with a positive DOCX-existence invariant.

### BLOCKER-1 — canonical exceptions created canonical text: FIXED

- Every canonical unit now resolves to visible text in the manifest-verified
  canonical DOCX, directly or through one enumerated deterministic
  layout-whitespace normalization.
- `LINE_BREAK_TO_SPACE` replaces a Word line break and adjacent horizontal layout
  whitespace with one space. Verification confirms the lexical token sequence is
  unchanged.
- Exception provenance identifies canonical filename and SHA-256, Word part,
  paragraph index, extraction method, normalization method, exact
  pre-normalization text and SHA-256, normalized canonical text, unit text, and
  unit SHA-256.
- Verification independently extracts the paragraph and recomputes every text
  and hash relationship. Free-text fields cannot corroborate one another.
- Approval can affect authority state only after DOCX text existence and
  normalization equality have been proven. It cannot create absent text.
- `S4A-2026-000` resolves to `word/header1.xml`, paragraph index 1, through
  line-break normalization. Its existing authority state remains unresolved,
  publication-blocking, and non-insertable.

Result: 53/53 units source-proven; 52 direct, 1 normalized, 1 normalization
exception record.

### HIGH findings — source omission coverage and provenance: FIXED

- Every marked change-spec paragraph element absent from exact canonical DOCX
  text must match exactly one `official_change_requirement` by text and
  structural location.
- Canonical units, canonical exceptions, human-review state, and canonical
  authority dispositions cannot account for absent marked change text.
- The current absent line remains mapped only to `S4A-REQ-2026-001`. Zero
  requirements and duplicate requirements both hard fail.
- Adversarial tests separately execute requirement removal plus a liver
  canonical unit, unresolved exception, approved exception, arbitrary fabricated
  text, nonexistent provenance, undeclared normalization, semantic mismatch,
  duplicate requirement, and final-gate paths.

### MEDIUM findings — review, tests, and dispositions: FIXED

- Human-review validation now reads `review_row` for each unit's reviewer names,
  approved text, and remaining issues. Two-order regression fixtures prove the
  same deficient row fails regardless of row order.
- Previously dead anti-laundering assertions were separated into executable test
  cases.
- Requirement authority disposition now requires a linked `requirement_id`,
  typed inclusion/exclusion decision, `FINAL` status, decision maker, ISO date,
  and evidence reference. The decision must match final inclusion status.
  `S4A-REQ-2026-001` has no disposition and remains unresolved.

### Mutable governance data integrity

`data/governance_integrity_manifest.json` records deterministic byte counts and
SHA-256 values for `data/source_requirements.jsonl` and
`data/canonical_unit_exceptions.jsonl`. These remain mutable project governance
files, not official immutable sources. The ledger deliberately does not hash
itself; tracked Git history and the external audit index/archive are its trust
anchor.

### Terminology evidence foundation

- Five files under `data/Sanasto/` are registered as
  `TERMINOLOGY_REFERENCE`, never as SPICT source authority.
- Their exact byte counts, SHA-256 values, file types, content-supported
  metadata, evidence level, confidence, licence/reuse status, and unresolved
  metadata are schema-validated.
- A local pinned extractor regenerates 136 source-provided evidence entries:
  explicit CSV columns/rows plus exact PDF fragments/pages. Missing English
  equivalents and definitions remain null rather than inferred.
- Six differing-definition conflicts and eight cross-source duplicate Finnish
  term groups remain explicit. No conflict was auto-resolved.
- The conservative exact-English relevance map contains 0 matches. Zero matches
  are valid and preferable to inferred English/Finnish equivalence.
- The project glossary contains 10 high-risk concepts requiring human review and
  0 approved Finnish terms.
- `T0_terminology_evidence_ready` is a separate required pre-G1 control. It does
  not alter or block G0 and incomplete terminology licensing metadata remains
  explicit.

### R3 verification results

- `.\tools.ps1 -Task Test`: PASS; `115 passed`, FAIL=0.
- `.\tools.ps1 -Task VerifySources`: PASS=7, FAIL=0.
- `.\tools.ps1 -Task ValidateRequirements`: PASS=1, FAIL=0.
- `.\tools.ps1 -Task ValidateCanonical`: PASS=1, FAIL=0; direct=52,
  normalized=1, exceptions=1.
- `.\tools.ps1 -Task ValidateGovernance`: PASS=1, FAIL=0.
- `.\tools.ps1 -Task ValidateTerminology`: PASS=1, FAIL=0; sources=5,
  extracted=136, conflicts=6, approved=0, relevance matches=0.
- `.venv\Scripts\python.exe -m mypy --strict src/spict4all`: PASS; no
  issues in 17 source files.
- `.venv\Scripts\python.exe -m ruff check src scripts tests`: PASS.
- `.venv\Scripts\python.exe -m compileall -q src scripts tests`: PASS.
- `git diff --check`: PASS.
- `git diff -- sources/official`: empty; no official source changed.

### R3 unresolved source-authority conflicts

- `S4A-2026-000`: source text is normalization-proven, but the existing final
  title authority disposition remains unresolved.
- `S4A-REQ-2026-001`: final inclusion remains unresolved and
  publication-blocking.

G0 source integrity passes because the conflicts are explicit and provenance
linked. T0 terminology readiness passes independently. Final source
reconciliation and publication remain blocked.

### R3 no-translation confirmation

No SPICT text was translated, no Finnish candidate or approved Finnish project
terminology was generated, and no Agent A or Agent B translation run occurred.
The unauthenticated external parser was not used; local deterministic extraction
processed only terminology/reference evidence.

## R4 final remediation

Work package: `WP-G0-T0-R4-FINAL-REMEDIATION`  
Date: 2026-09-07  
Baseline Git commit remains: `4f4cb3ffd61b2366d6c4aae507916eca2932bf36`

This pass closed the complete currently known independent adversarial finding
set: HIGH 1, MEDIUM 2, LOW 8. Historical R1/R2/R3 results above are retained
unchanged.

### HIGH-1 — non-blank authority attribution: FIXED

Whitespace-only `decision_maker`, `evidence_reference`, `status`, and
`decision_date` values can no longer satisfy a final authority disposition.

- JSON Schema requires a non-whitespace character (`pattern: \S`) on attribution
  fields, plus an ISO calendar `decision_date`.
- Domain models in `src/spict4all/authority.py` reject blank and whitespace-only
  values with `.strip()` even if schema validation is bypassed.
- The invariant applies to both `SourceRequirement` dispositions and canonical
  exception dispositions, and to both INCLUDE/EXCLUDE and APPROVE/REJECT paths.
- An invalid disposition cannot clear a publication blocker, make an evidence
  source document-insertable, or exclude an official requirement or canonical
  exception.

Executable regressions live in `tests/test_authority_attribution.py`. Final
status: PASS.

### MEDIUM-1 — terminology metadata must be evidence-bound: FIXED

Terminology source records now separate file facts, source-verified metadata,
explicitly unresolved metadata, and project-inferred assessment.

- Source-verified publisher, date, title, URL, copyright, or licence values must
  re-derive from a machine-checkable PDF page or CSV cell. Filename inference is
  not accepted.
- A field cannot be populated as source-verified and listed as unresolved.
- `FILE_VERIFIED_METADATA_UNRESOLVED` cannot claim publisher, date, or URL.
- Upgrading `provenance_status` without the required evidence fails.
- Current honest terminology records remain valid: 3 PDF sources with partial
  content-verified metadata, 2 CSV sources with explicit unknown publisher/date
  /URL/licence metadata, and CSV titles bound to declared title rows.

Executable regressions cover fabricated publisher, date, title, URL, licence
status, self-contradiction, and provenance upgrade without evidence. Final
status: PASS.

### MEDIUM-2 — completed candidate_fi must be non-blank: FIXED

Completed candidate states `READY_FOR_SYNTHESIS`, `READY_FOR_HUMAN_REVIEW`,
`HUMAN_APPROVED`, and `HUMAN_REJECTED` require `candidate_fi` with at least one
non-whitespace character.

- Schema: `minLength: 1` and `pattern: \S`.
- Domain validation in `artifacts.py` repeats the `.strip()` check if schema
  validation is bypassed.
- Empty, space-only, tab/newline-only, and missing `candidate_fi` fail. The
  existing non-blank test fixture still passes. No Finnish SPICT translation was
  generated.

Final status: PASS.

### LOW findings

- **LOW-1 — candidate additionalProperties: FIXED.** Translation candidate
  records set `additionalProperties: false`. Forward-compatibility uses an
  explicit `extensions` object. `human_signoff`, `gates_passed`, and
  `eligible_for_document_insertion` are rejected unless defined.
- **LOW-2 — dead canonical test fixture: FIXED.**
  `test_liver_requirement_cannot_be_laundered_into_canonical_namespace` now
  exercises canonical verification only. It no longer asserts an unused
  temporary requirements file.
- **LOW-3 — requirement ID documentation drift: FIXED.** Runtime still has no
  Python requirement-ID allow-list. CLI and audit reporting derive current
  identifiers from `data/source_requirements.jsonl`. Documentation states that
  named IDs are examples from the current frozen source set.
- **LOW-4 — nested Word paragraph extraction: FIXED.** Visible text and runs are
  attributed to leaf `w:p` elements. Container paragraphs do not concatenate
  nested textbox paragraph text. Header/title resolution is preserved.
- **LOW-5 — CSV row-2 magic number: FIXED.** Both current CSV sources declare
  header and non-entry row semantics in `csv_structure`. Row 2 is skipped only
  because it is declared `HUMAN_READABLE_COLUMN_LABELS`. Changing that
  declaration causes the label cell to be extracted.
- **LOW-6 — terminology report disclosure: FIXED.**
  `terminology/reports/TERMINOLOGY_EVIDENCE_REPORT.md` now states: extracted
  entries = 136; source-provided English labels = 41; remaining entries have no
  source-provided English label; conservative SPICT relevance matches = 0
  because of missing exact English overlap, not extractor failure; no Finnish
  terminology without explicit English labels is auto-mapped; semantic mapping
  would require a separately reviewed methodology.
- **LOW-7 — requirements.py indentation: FIXED.** The missing blank line before
  `enumerate_wordprocessing_parts` was restored. No unrelated formatting churn.
- **LOW-8 — terminology/official source separation: FIXED.**
  `ValidateTerminology` does not own official-source integrity. `VerifySources`
  still rejects unmanifested files under `sources/official/`. Workflow, quality
  gates, terminology README, and an integration test document the composition:
  a rogue official file fails `VerifySources` while terminology validation of
  the repository remains a separate control.

### R4 source and authority results

- Official source hashes remain:
  - `20260130-Using-SPICT-4ALL-2025.docx`: `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca`
  - `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx`: `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.docx`: `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581`
  - `20260521-Word-template-SPICT-4ALL-translations-2026.pdf`: `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72`
- Canonical source-unit count: 53; 52 direct + 1 declared safe normalization.
- Canonical-unit exception count: 1.
- Official source-requirement count: 1, identifier derived from data:
  `S4A-REQ-2026-001`.
- Terminology sources: 5; extracted entries: 136; source-provided English
  labels: 41; conflicts: 6; approved terminology: 0; relevance matches: 0.
- Unresolved authority conflicts:
  - `S4A-2026-000`: authority unresolved, publication-blocking, non-insertable.
  - `S4A-REQ-2026-001`: UNRESOLVED, publication-blocking, non-insertable.
- Governance integrity manifest remains a mutable project ledger, not source
  authority.

### R4 exact checks

- `.\tools.ps1 -Task Test`: PASS; `208 passed`, FAIL=0.
- `.\tools.ps1 -Task VerifySources`: PASS=7, FAIL=0.
- `.\tools.ps1 -Task ValidateRequirements`: PASS=1, FAIL=0.
- `.\tools.ps1 -Task ValidateCanonical`: PASS=1, FAIL=0; direct=52,
  normalized=1, exceptions=1.
- `.\tools.ps1 -Task ValidateGovernance`: PASS=1, FAIL=0.
- `.\tools.ps1 -Task ValidateTerminology`: PASS=1, FAIL=0; sources=5,
  extracted=136, source_provided_english=41, conflicts=6, approved=0,
  relevance_matches=0.
- `.venv\Scripts\python.exe -m mypy --strict src/spict4all`: PASS; no
  issues in 18 source files.
- `.venv\Scripts\python.exe -m ruff check src scripts tests`: PASS.
- `.venv\Scripts\python.exe -m compileall -q src scripts tests`: PASS,
  exit code 0 with no output.
- `git diff --check`: PASS.
- `git diff -- sources/official`: empty; no official source changed.

### R4 adversarial self-check

Independent unsafe attempts all failed:

- whitespace-only authority disposition
- whitespace-only evidence reference
- whitespace-only completed candidate
- fabricated terminology publisher/date/title/URL/licence
- terminology metadata self-contradiction
- liver requirement laundering through every canonical path
- fabricated canonical text
- human-review dirty non-final row, order-independent
- unapproved terminology promoted to mandatory glossary

### R4 no-translation confirmation

No SPICT text was translated, no Finnish candidate or approved Finnish project
terminology was generated, and no Agent A or Agent B translation run occurred.
No commit or push was performed.



## R5 final acceptance remediation

Work package: WP-G0-T0-R5-FINAL-REMEDIATION, 2026-09-07.
Implementation results: BLOCKER fixed 1/1; HIGH fixed 1/1; MEDIUM fixed 2/2.
These are engineering verification results, not independent acceptance approval,
clinical validation, terminology approval, or source-authority disposition.
R1-R4 history and archives are preserved. No commit or push was performed.

### BLOCKER-1: complete canonical membership and identity

`src/spict4all/canonical_freeze.py` is the versioned extraction specification for
all 53 existing unit identities. It was audited against the existing frozen unit
index and each exact structural location in the hash-verified canonical DOCX.
The original unit-index hash remains
`f4751a7e67ff42338fc5c23a842cc7af07c03f2c6a394dea1819f26546c127a5`;
the existing regression confirms all original IDs and source hashes are unchanged.
No new source wording or source-authority approval was introduced.

`canonical_binding_records` re-extracts every specified paragraph from the official
DOCX, applies only the specified layout normalization, and builds the full binding.
`data/canonical_unit_manifest.json` is a schema-backed, deterministic materialization:
unit ID, exact text and hash, official filename/hash, Word part and structural
location, source-index location, extraction/normalization method, authority flag,
and baseline translation/inclusion/blocking/insertion states. Runtime validation
requires exact equality with the independently re-derived full mapping and exact
membership and text/location identity of current source units. Rewriting this
artifact or regenerating mutable governance hashes cannot redefine the extraction
specification. This is not a single file-digest check.

The specification and verifier are project-controlled code, protected by version
review and audit evidence; the threat model does not claim to resist an attacker
who can replace the verifier itself. A future source-freeze migration requires
review of the specification and evidence. The governance ledger is not authority.

S4A-2026-000 remains normalized from word/header1.xml paragraph 1, has
AUTHORITY_DECISION_REQUIRED, final inclusion UNRESOLVED, is publication-blocking
and non-insertable. The normalization record is mandatory. Existing attributable
human/source-authority disposition handling still passes its positive regressions;
no disposition has been recorded for the real project title.

### HIGH-1: field-specific terminology evidence

The five honest terminology source records retain their metadata values. Each
verified field now explicitly names its metadata field, source file and hash,
page/row/header, extraction rule, exact source text and semantic evidence type.
`metadata_bindings.py` freezes audited field-specific locations and complete spans
for these source hashes. Runtime verification compares the supplied evidence with
the rule for that source hash AND field, then extracts the precise PDF line range,
checks the complete contextual line(s), and checks the exact field span.
Publisher copyright/working-group attributions cannot become document titles;
retrieval/persistent URLs cannot be replaced by unrelated URL occurrences.

PDF rules distinguish running/document/imprint titles, copyright or working-group
publisher attribution, dated publication lines, retrieval footer/persistent URN,
and copyright notice. Date precision remains unchanged. CSV title evidence must
match the declared VOCABULARY_TITLE non-entry row and the explicit primary-term
header, and the source cell is still re-read. Unknown CSV publisher/date/URL and
all unresolved reuse terms remain explicitly unresolved. No metadata was fabricated.
The inference/licence and metadata contradiction checks remain active.

### MEDIUM-1: official filename-role binding

Only canonical_source, official_change_spec and official_reference are supported.
The four official filenames are bound to their required roles in OFFICIAL_ROLES;
VerifySources also requires the complete four-file manifest set. Wrong known roles,
unknown/empty/terminology roles and duplicate canonical/change-spec assignments fail
even with unchanged bytes and hashes. Existing synthetic test fixtures now use
permitted official filenames so that they continue to exercise their original checks.

### MEDIUM-2: recursive official membership

Every regular file below sources/official is enumerated recursively with sorted,
relative POSIX paths. Unexpected text, DOCX, PDF copies and hidden files fail.
The sole explicit pre-existing metadata exception is the root README.md, the
repository's read-only source instructions; it is not official source authority.
A nested README is not exempt. Symlinks, junctions, all Windows reparse points and
nonregular filesystem entries fail closed before source file hashing. A real
Windows junction regression ran successfully without being skipped.

### Exact regression evidence

`tests/test_r5_security.py` adds 29 executable cases:
- test_canonical_membership_identity_attacks: delete_052, duplicate_053,
  replace_000, swap_ids, location, remove_normalization, rewrite_freeze.
  Every case regenerates governance hashes and checks both ValidateCanonical and
  check-final. Substitution cannot reach review/gate input loading.
- test_title_blocker_and_clean_canonical_remain.
- test_metadata_field_binding_attacks: publisher_as_title, title_as_publisher,
  same_page, truncated_publisher, unrelated_url, relabel_evidence,
  csv_title_as_publisher.
- test_valid_title_and_publisher_bindings.
- test_official_role_binding_attacks: 8 role/filename combinations, including
  unknown, terminology, empty, wrong Using/canonical/Edits roles and duplicate roles.
- test_recursive_unmanifested_official_files: text, DOCX, official PDF copy, hidden file.
- test_official_directory_junction_or_symlink_rejected.

`docs/R5_SELF_ATTACK_RESULTS.json` records a separate scratch-copy execution of all
four original acceptance findings, including finalization after title substitution
and regenerated governance hashes. All four returned exit 1 for the intended reason.
The same run reran 41 prior security cases (exact test node IDs and output recorded):
liver laundering with an approved-looking exception, fabricated canonical text,
blank/whitespace canonical and requirement authority dispositions, dirty human-review
rows in both orders, whitespace completed candidates, and unapproved glossary
promotion. All unsafe inputs were rejected; all 41 regression cases passed.

### Full test battery and retained state

- .\tools.ps1 -Task Test: PASS, 237 passed in 19.92s, 0 failures, 0 skips.
- .\tools.ps1 -Task VerifySources: PASS, official files 4/4; canonical 53;
  requirements 1; governance files 2.
- .\tools.ps1 -Task ValidateRequirements: PASS, 18 marked paragraphs,
  32 yellow runs, 4 green-highlighted runs, 1 accent6 run; exactly one absent
  marked paragraph accounted for by S4A-REQ-2026-001.
- .\tools.ps1 -Task ValidateCanonical: PASS, 53 = 52 direct + 1 normalized.
- .\tools.ps1 -Task ValidateGovernance: PASS, 2 files hash-matched.
- .\tools.ps1 -Task ValidateTerminology: PASS, 5 sources, 136 extracted entries,
  41 source-provided English entries, 6 conflicts, 0 approved, 0 relevance matches.
- .venv\Scripts\python.exe -m mypy --strict src/spict4all: PASS, 20 source files.
- .venv\Scripts\python.exe -m ruff check src scripts tests: PASS.
- .venv\Scripts\python.exe -m compileall -q src scripts tests: PASS.

The audit builder reruns every command and embeds its exact final output.
S4A-2026-000 and S4A-REQ-2026-001 remain unresolved, publication-blocking and
non-insertable. Approved terminology remains 0; unapproved discoveries cannot
constrain Agent A/B. No SPICT Finnish translation content or translation artifacts
exist in the project work directories. The existing Finnish source-reference
terminology evidence is not a SPICT translation. No Agent A/B run was started.

### Official source hashes (unchanged)

- 20260521-Word-template-SPICT-4ALL-translations-2026.docx: `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581` (66914 bytes), canonical_source.
- 20260130-Using-SPICT-4ALL-2025.docx: `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca` (111045 bytes), official_reference.
- 20260521-Word-template-SPICT-4ALL-translations-2026.pdf: `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72` (223468 bytes), official_reference.
- 20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx: `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d` (68949 bytes), official_change_spec.

### R5 files and Git state

The working tree already contained uncommitted R1-R4 changes at entry. Those changes
were preserved. R5 created or changed the following 16 reviewable files, plus its
new ZIP and SHA-256 sidecar:

- `src/spict4all/sources.py`
- `src/spict4all/requirements.py`
- `src/spict4all/terminology.py`
- `src/spict4all/canonical_freeze.py`
- `src/spict4all/metadata_bindings.py`
- `data/canonical_unit_manifest.json`
- `schemas/canonical_unit_manifest.schema.json`
- `schemas/terminology_source_manifest.schema.json`
- `terminology/sources/terminology_source_manifest.json`
- `tests/test_sources.py`
- `tests/test_requirements.py`
- `tests/test_r5_security.py`
- `scripts/create_g0_r5_audit_zip.py`
- `scripts/run_r5_self_attack.py`
- `docs/R5_SELF_ATTACK_RESULTS.json`
- `docs/G0_SOURCE_FREEZE_REPORT.md`

Pre-package git diff --stat (tracked changes, including inherited work):

```text
 .gitignore                                |   2 +
 README.md                                 |  25 +++-
 config/model_roles.yaml                   |  10 ++
 config/quality_gates.yaml                 |  38 ++++--
 data/README.md                            |  23 +++-
 docs/METHODOLOGY.md                       |  46 ++++++-
 docs/OFFICIAL_TRANSLATION_GUIDANCE.md     |   7 ++
 docs/SOURCE_PROVENANCE.md                 |  48 +++++++-
 docs/WORKFLOW.md                          |  54 ++++++++-
 prompts/01-agent-a-forward.md             |  11 +-
 prompts/02-agent-b-forward.md             |   8 +-
 prompts/03-agent-c-synthesis.md           |   3 +-
 pyproject.toml                            |  15 +++
 requirements-dev.lock                     |   7 ++
 schemas/translation_candidate.schema.json |  42 ++++++-
 scripts/check_translation_coverage.py     |   2 +-
 scripts/create_audit_zip.py               |   7 +-
 scripts/verify_sources.py                 |   2 +-
 src/spict4all/artifacts.py                |  79 ++++++++++--
 src/spict4all/cli.py                      | 195 ++++++++++++++++++++++++++++--
 src/spict4all/coverage.py                 |  14 ++-
 src/spict4all/gates.py                    |  71 ++++++++++-
 src/spict4all/reports.py                  |  16 ++-
 src/spict4all/reviews.py                  |  46 +++++--
 src/spict4all/runs.py                     |   7 +-
 src/spict4all/sources.py                  |  93 +++++++++++---
 src/spict4all/units.py                    |  23 +++-
 terminology/terms.csv                     |  22 ++--
 tests/test_artifacts.py                   | 135 ++++++++++++++++++++-
 tests/test_reviews_and_gates.py           |  82 +++++++++++++
 tests/test_sources.py                     |  12 +-
 tests/test_units.py                       |  11 ++
 tools.ps1                                 |  24 +++-
 33 files changed, 1069 insertions(+), 111 deletions(-)
```

Pre-package git status --short:

```text
 M .gitignore
 M README.md
 M config/model_roles.yaml
 M config/quality_gates.yaml
 M data/README.md
 M docs/METHODOLOGY.md
 M docs/OFFICIAL_TRANSLATION_GUIDANCE.md
 M docs/SOURCE_PROVENANCE.md
 M docs/WORKFLOW.md
 M prompts/01-agent-a-forward.md
 M prompts/02-agent-b-forward.md
 M prompts/03-agent-c-synthesis.md
 M pyproject.toml
 M requirements-dev.lock
 M schemas/translation_candidate.schema.json
 M scripts/check_translation_coverage.py
 M scripts/create_audit_zip.py
 M scripts/verify_sources.py
 M src/spict4all/artifacts.py
 M src/spict4all/cli.py
 M src/spict4all/coverage.py
 M src/spict4all/gates.py
 M src/spict4all/reports.py
 M src/spict4all/reviews.py
 M src/spict4all/runs.py
 M src/spict4all/sources.py
 M src/spict4all/units.py
 M terminology/terms.csv
 M tests/test_artifacts.py
 M tests/test_reviews_and_gates.py
 M tests/test_sources.py
 M tests/test_units.py
 M tools.ps1
?? data/Sanasto/
?? data/canonical_unit_exceptions.jsonl
?? data/canonical_unit_manifest.json
?? data/governance_integrity_manifest.json
?? data/source_requirements.jsonl
?? deliverables/audit/SPICT4ALL-FI-G0-R1-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-R1-source-freeze-audit-20260907.zip.sha256
?? deliverables/audit/SPICT4ALL-FI-G0-R2-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-R2-source-freeze-audit-20260907.zip.sha256
?? deliverables/audit/SPICT4ALL-FI-G0-R3-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-R3-source-freeze-audit-20260907.zip.sha256
?? deliverables/audit/SPICT4ALL-FI-G0-R4-final-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-R4-final-audit-20260907.zip.sha256
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip
?? deliverables/audit/SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip.sha256
?? docs/G0_SOURCE_FREEZE_REPORT.md
?? docs/R5_SELF_ATTACK_RESULTS.json
?? schemas/canonical_unit_exception.schema.json
?? schemas/canonical_unit_manifest.schema.json
?? schemas/governance_integrity_manifest.schema.json
?? schemas/source_requirement.schema.json
?? schemas/terminology_extracted_entry.schema.json
?? schemas/terminology_pdf_extraction_rule.schema.json
?? schemas/terminology_source_manifest.schema.json
?? scripts/build_terminology_evidence.py
?? scripts/create_g0_audit_zip.py
?? scripts/create_g0_r1_audit_zip.py
?? scripts/create_g0_r2_audit_zip.py
?? scripts/create_g0_r3_audit_zip.py
?? scripts/create_g0_r4_audit_zip.py
?? scripts/create_g0_r5_audit_zip.py
?? scripts/run_r5_self_attack.py
?? scripts/update_governance_integrity_manifest.py
?? src/spict4all/authority.py
?? src/spict4all/canonical_freeze.py
?? src/spict4all/evidence.py
?? src/spict4all/governance.py
?? src/spict4all/metadata_bindings.py
?? src/spict4all/requirements.py
?? src/spict4all/terminology.py
?? terminology/README.md
?? terminology/conflicts/
?? terminology/extracted/
?? terminology/reports/
?? terminology/sources/
?? tests/test_authority_attribution.py
?? tests/test_canonical_units.py
?? tests/test_governance.py
?? tests/test_r5_security.py
?? tests/test_requirements.py
?? tests/test_terminology.py
```

### R5 audit package

Output: deliverables/audit/SPICT4ALL-FI-G0-R5-final-audit-20260907.zip.
External checksum: the same path with .sha256 appended.
The builder refuses to overwrite any existing output, runs the full battery,
verifies ZIP open/CRC and every AUDIT_INDEX hash, official sources 4/4,
terminology sources 5/5, forbidden members 0, translation artifacts 0, no nested
previous ZIPs, sidecar equality and byte equality of every archived project file
with the current tree. AUDIT_INDEX cannot contain its own hash; generated audit
results/index are not repository payload files. The actual ZIP digest is in the
external sidecar because embedding a ZIP's own digest would be circular.
Final archive verification results are emitted by the builder for the handoff.
