# Independent forward translation A — G1

Work package: `WP-G1-A-INDEPENDENT-FORWARD-TRANSLATION-001`.

| Evidence | Expected | Translated |
| --- | ---: | ---: |
| Canonical source units | 53 | 53 |
| Official source requirements | 1 | 1 |
| Total | 54 | 54 |

The output is `candidates.jsonl`: 54 **DRAFT** records using the existing translation-candidate schema. Exact English, source SHA-256, typed source provenance, frozen source record, translator identity, run identity, timestamp, and uncertainty are retained in each record. Additional audit fields use the schema's `extensions.g1_agent_a` container, which confers no authority. Canonical membership remains 000–052. The separate dialysis texts (019 and 020), title placeholder, and footer are retained.

## Independence and actual model

Forward Translator A used only this worktree's exact English source, frozen requirements, governance/methodology, T0/T1 terminology evidence, and recorded human terminology decisions. No Agent B candidate, synthesis, back-translation, or translation critic output was read. No sibling worktree was searched. Directory names and schema/workflow instructions are not translation evidence. Repository tests use synthetic fixtures; no existing translation workspace was copied into their fixture.

The session identifies its model as **GPT-6**. The exact backend variant and effort setting are not exposed. This differs from `docs/MODEL_STRATEGY.md`'s planned GPT-5.6 Sol Medium; no claim is made that the planned model ran. The live user assignment selected this session as Forward Translator A. No other translator or reviewer was delegated work.

## Terminology and self-check

The six recorded human wording decisions were used in context: elinikää lyhentävät terveydentilat; hengityskone; kokonaisvaltainen hoito; terveydentila on heikentynyt; toimintakyky on heikentynyt; ei ole riittävän hyväkuntoinen syöpähoitoon. The usual-activities scope remains explicit in units 004 and 014. No glossary rows were promoted or treated as approved merely because of model suggestions.

One genuine unresolved wording uncertainty is recorded for **S4A-2026-021**: whether plain-language **hauraus** adequately conveys the full frailty concept to the target reader. This is not a reopened pre-G1 terminology blocker, an invented human decision, or a request for new terminology research.

Translator A checked all 54 English/Finnish pairs for omissions, additions, negation, degree, time, alternatives, agency, and treatment choice. Contextual wording decisions are recorded for carer, chest, chest infections, and spiritual problems. Initial wording is preserved in `translation_input.json`; `self_edit_log.json` records three pre-packaging self-edits concerning breathlessness at rest and the rolling past-year interval. No prior candidate artifact was overwritten. There is no independent review or human approval in this work package.

Mechanical checks cover exact membership and duplicate IDs, schema validity, frozen hashes and input bytes, exact English, source contracts and provenance, blank/unchanged candidates, common accidental English residue, alternatives, and selected negation/modality/time/agency anchors. These lexical tripwires cannot prove semantic equivalence or exhaustive absence of omissions/additions.

## Unresolved source authority

**S4A-REQ-2026-001** is translated as “Maksansiirto ei ole mahdollinen.” It remains an official change requirement, noncanonical, `UNRESOLVED_CANONICAL_OMISSION`, final inclusion `UNRESOLVED`, publication-blocking, and not eligible for document insertion. Its translation is evidence only.

**S4A-2026-000** remains canonical through its existing verified layout normalization; its separate title authority remains unresolved, publication-blocking, and not eligible for insertion. Neither source-authority question was resolved here. All units still require explicit human sign-off.

## Executed checks

Results and complete command output are in `checks/20260908T104119369506Z/`.

- **311 repository tests passed** in an isolated pre-G1 fixture, with authorized source/governance/tooling copies and empty historical `.gitkeep` placeholders. Historical T1 validators assert that no translation work exists; the fixture preserves that original test condition without altering those validators or examining other translation workspaces.
- **12 Agent A tests passed** against this worktree's candidate artifact, including corruption rejection for missing/extra/duplicate items, hash, English, provenance, blank candidates, negation, agency, approval, and authority.
- T1 closure validation passed in the pre-G1 fixture. Its `g1_started: false` refers only to that historical fixture, not the now-completed Agent A translation run.
- Live source, canonical, requirement, governance, and T0 terminology validators passed.
- Live candidate-schema validation with required coverage passed: 54 records; no missing or extra IDs.
- Agent A extended evidence checks passed for all 54 records and every recorded input digest.
- Repository Ruff and strict mypy passed. Ruff also passed for all four new Agent A Python files.
- Final tracked-source/governance/terminology diff was empty. Official files were never modified.

## Files and reproduction

All new evidence and tooling is isolated under `work/agent-a/`:

- `candidates.jsonl`: source-linked translation evidence.
- `translation_input.json`: preserved initial Finnish wording.
- `self_edit_log.json`: explicit pre-packaging self-edits.
- `run_metadata.json`: existing run schema, timestamp, and input hashes.
- `build_evidence.py`: deterministic packaging of the recorded wording; exclusive creation refuses overwrites.
- `validate_evidence.py`: source/audit checks and lexical tripwires.
- `test_evidence.py`: 12 Agent A integrity and corruption tests.
- `run_checks.py`: reproducible fixture creation and logged validation, with a new timestamped log directory each time.
- `checks/20260908T104119369506Z/`: 12 command logs, `commands.json`, and `evidence_validation.json`.
- `REPORT.md`, `git_status.txt`, `artifact_manifest.json`: handoff report, final Git status, and output hashes. The hash manifest excludes itself and ignored temporary/cache files.

From the repository root, run `.venv/Scripts/python.exe work/agent-a/run_checks.py` to repeat checks. Packaging an existing candidate again is intentionally refused; preserve prior files and use a separate run directory for future candidate revisions. The wording is recorded model output, not a promise of identical stochastic regeneration.

Git: only new untracked Agent A files; no tracked files modified or staged. The local Python 3.12 virtual environment and isolated test fixture are ignored work products. No commit, push, G2, human approval, or clinical validation was performed or claimed.
