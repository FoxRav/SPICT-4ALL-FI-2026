# SPICT-4ALL FI 2026 - evidence-traceable translation project

Goal: produce a Finnish SPICT-4ALL 2026 translation suitable for review by the SPICT International Programme / University of St Andrews.

This repository is designed as an **AI-assisted, human-approved translation and cross-cultural adaptation workflow**. AI performs independent translations, synthesis, back-translation and structured critique. Human clinical/methodological reviewers remain the final authority.

## Canonical source

`sources/official/20260521-Word-template-SPICT-4ALL-translations-2026.docx`

The official template instructs that the translated text goes after each line in English. The original file is immutable. Never edit it in place.

The manifest-verified canonical template is the authority for canonical unit
text. Every source unit must resolve to visible DOCX text at its exact location,
either directly or through an enumerated layout-only normalization recorded in
`data/canonical_unit_exceptions.jsonl`. An exception cannot create canonical
text. Separate,
explicitly marked changes found in official change specifications are recorded in
`data/source_requirements.jsonl`; they are evidence inputs, not automatic additions
to the canonical template. Human/source-authority disposition is required before an
unresolved requirement can be included in a final publication.

## Engineering setup on Windows 11

```powershell
cd F:\-DEV-\120.Samin-PDF
.\tools.ps1 -Task Setup
.\tools.ps1 -Task VerifySources
.\tools.ps1 -Task ValidateCanonical
.\tools.ps1 -Task ValidateRequirements
.\tools.ps1 -Task ValidateGovernance
.\tools.ps1 -Task BuildTerminology
.\tools.ps1 -Task ValidateTerminology
.\tools.ps1 -Task Test
.\tools.ps1 -Task TypeCheck
.\tools.ps1 -Task Lint
```

`data/Sanasto/**` is registered only as Finnish terminology/reference evidence.
Its files cannot alter the English SPICT corpus. `BuildTerminology` regenerates
source-linked discoveries, explicit conflicts, and a conservative relevance
map; only rows with explicit human `APPROVED` status may later constrain both
independent forward translations.

The package requires Python 3.12 or newer. Direct dependencies are pinned in `pyproject.toml`, and the Windows development environment is fully version-pinned in `requirements-dev.lock`. The PowerShell setup creates a repository-local `.venv`; no model API integration is installed.

## Validation commands

```powershell
# Validate a manual-session candidate artifact against its JSON schema and source hashes
.venv\Scripts\python.exe -m spict4all.cli --root . validate-artifact work\agent-a\candidates.jsonl `
  --schema schemas\translation_candidate.schema.json --require-coverage

# Generate a mechanical A/B discrepancy table; the output path must not already exist
.venv\Scripts\python.exe -m spict4all.cli --root . report-discrepancies `
  --agent-a work\agent-a\candidates.jsonl --agent-b work\agent-b\candidates.jsonl `
  --output work\synthesis\discrepancies.tsv
```

Run directories created with `create-run` are immutable: an existing run ID is never overwritten. Human-review and quality-gate checks must pass before a workflow artifact can be marked final. Unresolved source-authority decisions do not prevent independent translation evidence work, but they block final source reconciliation and, when marked publication-blocking, publication.

## Core rule

**Target: zero known translation errors. No model output is accepted solely because a model produced it. Every final unit requires human sign-off.**

See `docs/WORKFLOW.md`, `docs/METHODOLOGY.md`, and `config/quality_gates.yaml`.
