# Codex bootstrap task

You are the senior coding agent for the SPICT-4ALL FI 2026 translation project.

Read first:
- `AGENTS.md`
- `.cursor/rules/*.mdc`
- `docs/PROJECT_CHARTER.md`
- `docs/WORKFLOW.md`
- `config/quality_gates.yaml`
- `sources/manifests/source_manifest.json`

## Mission for bootstrap only
Build the engineering foundation for a reproducible, evidence-traceable translation workflow. **Do not translate any SPICT content yet.**

## Required implementation
1. Create a Python 3.12+ package under `src/spict4all/`.
2. Add `pyproject.toml` with minimal, pinned/controlled dependencies and pytest tooling.
3. Implement:
   - source-manifest verification;
   - source-unit loader;
   - JSONL artifact validation against schemas;
   - run metadata + hashes;
   - coverage checks;
   - discrepancy report generation;
   - immutable run directories / no destructive overwrite;
   - command-line entrypoints for validation and report generation.
4. Add tests that fail on:
   - source hash changes;
   - duplicate/missing unit IDs;
   - candidate source-hash mismatch;
   - malformed JSONL;
   - missing required human review disposition;
   - attempt to mark a draft as final without all gates.
5. Do not edit anything under `sources/official/`.
6. Do not add model API integration yet. The first workflow will support manual Cursor model sessions by importing/exporting schema-valid JSONL files.
7. Add a `Makefile` or PowerShell-native `tools.ps1` suitable for Windows 11; prefer PowerShell instructions in README.
8. Run all tests locally and report exact results.
9. Do not push Git. The project owner pushes manually.

## Deliverable
A clean bootstrap commit-ready repository plus a short `docs/BOOTSTRAP_REPORT.md` listing files created, tests run, assumptions, and remaining blockers.
