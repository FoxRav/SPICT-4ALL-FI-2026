# SPICT-4ALL FI engineering bootstrap report

Date: 2026-09-07  
Repository: `F:\-DEV-\120.Samin-PDF`

## Outcome

The engineering bootstrap is complete. The repository now has a Python 3.12 package and Windows-native commands for source verification, source-unit loading, schema-linked JSONL validation, coverage enforcement, human-review enforcement, quality-gate enforcement, immutable run creation, input hashing, and deterministic A/B discrepancy reporting.

No SPICT-4ALL content was translated. No Finnish candidates, model API integrations, final documents, commits, or pushes were created.

## New official source inspection and provenance

The file `sources/official/20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx` was inspected read-only and added to the official source manifest with role `official_change_spec`.

Structural inspection found:

- one Word table and one document section;
- no tracked insertions or deletions;
- no comments;
- 38 OOXML highlight elements;
- yellow markings described by the document as 2025 changes;
- green markings described by the document as 2026 changes.

The packaged document renderer was also attempted, but the workspace dependency bundle did not contain `soffice.exe`. The renderer stopped with `FileNotFoundError: LibreOffice soffice.exe was not found on PATH`. No installed desktop LibreOffice was substituted. The structural inspection and programmatic highlight inspection completed; page-image inspection remains pending.

The change specification contains `A liver transplant is not possible.` at table 0, row 31, column 2. This line is absent from the canonical 2026 Word template and from `data/source_units.jsonl`. No source unit was invented or changed. This requires source-authority resolution before translation begins.

## Official source hashes

| Role | File | Bytes | SHA-256 |
|---|---|---:|---|
| `official_reference` | `20260130-Using-SPICT-4ALL-2025.docx` | 111045 | `1b8ee715051ca53a27d0a2261a7f879face8a57727fbfd12fc6a830ef1c155ca` |
| `official_change_spec` | `20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx` | 68949 | `0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d` |
| `canonical_source` | `20260521-Word-template-SPICT-4ALL-translations-2026.docx` | 66914 | `aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581` |
| `official_reference` | `20260521-Word-template-SPICT-4ALL-translations-2026.pdf` | 223468 | `d22418ca1d1b68a2be762bcdf48ae0e6ad41ac41c8e3d76b419e9062d4357f72` |

The immutable `sources/official/README.md` also retained its original package hash: `ed16cc002863d55fdeed9f0a931c5424c3a45e412ca21090b93e29ba90817af6`.

## Files created

- `pyproject.toml`
- `requirements-dev.lock`
- `tools.ps1`
- `src/spict4all/__init__.py`
- `src/spict4all/artifacts.py`
- `src/spict4all/cli.py`
- `src/spict4all/coverage.py`
- `src/spict4all/errors.py`
- `src/spict4all/gates.py`
- `src/spict4all/hashing.py`
- `src/spict4all/jsonl.py`
- `src/spict4all/reports.py`
- `src/spict4all/reviews.py`
- `src/spict4all/runs.py`
- `src/spict4all/sources.py`
- `src/spict4all/units.py`
- `schemas/gate_results.schema.json`
- `schemas/run_metadata.schema.json`
- `tests/conftest.py`
- `tests/test_artifacts.py`
- `tests/test_coverage.py`
- `tests/test_reviews_and_gates.py`
- `tests/test_runs_and_reports.py`
- `tests/test_sources.py`
- `tests/test_units.py`
- `docs/BOOTSTRAP_REPORT.md`

## Files changed

- `.gitignore`
- `README.md`
- `docs/OFFICIAL_TRANSLATION_GUIDANCE.md`
- `docs/SOURCE_PROVENANCE.md`
- `scripts/check_translation_coverage.py`
- `scripts/verify_sources.py`
- `sources/manifests/source_manifest.json`

No file under `sources/official/` was changed. The pre-existing `PACKAGE_MANIFEST.json` was preserved as the immutable inventory of the originally supplied bootstrap package; it is not treated as the current repository manifest.

## Tests and checks

Final commands were executed through the repository-local Python 3.12.14 environment.

| Command | PASS | FAIL | Exact result |
|---|---:|---:|---|
| `.\tools.ps1 -Task Setup` | 1 | 0 | Exit 0; exact-version development dependencies installed and editable package installed |
| `.\tools.ps1 -Task Test` | 36 | 0 | `36 passed in 0.43s` |
| `.\tools.ps1 -Task VerifySources` | 5 | 0 | Four manifested official files hash/size matched; 53 source units were unique, contiguous, and hash-matched |
| `.venv\Scripts\python.exe -m compileall -q src scripts tests` | 1 | 0 | Exit 0 |

The 36 pytest cases cover:

- repository source integrity;
- official source hash and byte-count changes;
- missing and unmanifested official files;
- invalid/duplicate manifest entries;
- duplicate, missing, malformed, translated, or hash-mismatched source units;
- malformed JSONL and JSON Schema failures;
- candidate/source hash mismatch and duplicate candidate IDs;
- missing, extra, and duplicate coverage;
- missing human dispositions, reviewers, approved text, and unresolved issues;
- rejected human dispositions blocking release;
- draft/failing-gate finalization attempts;
- run input hashes and immutable run directories;
- discrepancy report output and overwrite refusal.

## Assumptions and decisions

- The canonical 2026 Word template remains the translation source of truth until a human/source authority explicitly resolves any difference with the official change specification.
- Direct runtime and test dependencies are pinned in `pyproject.toml`; the complete resolved Windows development dependency set is pinned in `requirements-dev.lock`.
- JSONL evidence files may contain forward-compatible additional fields, but every record must satisfy its selected schema and source linkage checks.
- Run metadata stores resolved absolute input paths plus SHA-256 and byte counts so the originating run is auditable. Moving a repository does not alter the recorded provenance.
- Mechanical discrepancy reports record presence, exact candidate equality, statuses, and issue counts. They do not make semantic or clinical judgments.
- `APPROVED` and `REVISED` human dispositions may proceed when all required reviewer/date/text fields are complete and no issues remain; `REJECTED` is recorded but blocks release.

## Blockers

Bootstrap engineering: none.

Translation start blockers:

1. Resolve the change-specification line that is absent from the canonical template and source-unit index.
2. Resolve the existing authority-required document-title unit `S4A-2026-000` before it can become final wording.

Inspection limitation:

- Page-image visual inspection of the new DOCX could not be completed because the provided workspace dependency bundle had no bundled LibreOffice executable. Structural and text/highlight inspection completed successfully.

## Git status and diff

The repository has no `HEAD` commit (`git rev-parse --verify HEAD` exited 128). All supplied and bootstrap files are currently untracked. Final `git status --short` reported:

```text
?? .cursor/
?? .editorconfig
?? .gitignore
?? AGENTS.md
?? BOOTSTRAP_CODEX.md
?? NOTICE.md
?? PACKAGE_MANIFEST.json
?? README.md
?? SPICT/
?? config/
?? data/
?? deliverables/
?? docs/
?? prompts/
?? pyproject.toml
?? requirements-dev.lock
?? schemas/
?? scripts/
?? sources/
?? src/
?? templates/
?? terminology/
?? tests/
?? tools.ps1
?? work/
```

Both `git diff --stat` and `git diff --cached --stat` were empty because there is no tracked baseline and nothing is staged. No commit or push was performed.
