# Translation workflow

## Stage 0 - freeze source
Run `python scripts/verify_sources.py`. Any official-file, canonical-unit,
source-requirement, or governance-ledger integrity failure is a hard stop.

G0 distinguishes:
- canonical source units, each resolved to verified DOCX visible text directly or by an enumerated layout-only normalization;
- canonical-unit exceptions, which record independently recomputable normalization provenance but can never create canonical text;
- official source requirements, which preserve explicit change-specification evidence in a separate namespace;
- final inclusion decisions, which require explicit human/source-authority disposition.

An explicit unresolved authority conflict may pass G0 when it remains provenance-linked and truthfully unresolved. G0 permits translation evidence work; it does not assert that the final source set is authority-resolved.

G0 completeness is source-derived: every visibly marked paragraph element absent
from the verified canonical DOCX must map by exact text and structural location to
exactly one official source requirement. Canonical exceptions, human-review
states, and canonical authority dispositions cannot account for an absent marked
change. No source-unit data text or in-code requirement-ID allow-list defines
completeness.

## T0 - terminology evidence readiness
T0 is a separate pre-G1 control and does not redefine or block G0 source
authority. It verifies hashes and provenance for `data/Sanasto/**`, reproducible
source-provided extraction, explicit conflicts, glossary status, and the
conservative source-unit relevance map. Incomplete licence metadata is recorded
but does not turn terminology references into SPICT authority.

`ValidateTerminology` does not own official-source integrity. `VerifySources`
remains responsible for rejecting unmanifested files under `sources/official/`.
A standalone `ValidateTerminology` PASS is not a complete repository
source-integrity PASS.

## Stage 1 - Agent A
Input after G0 and T0 pass: all translation-evidence sources: canonical records
from `data/source_units.jsonl` plus records in
`data/source_requirements.jsonl` where `translation_evidence_required` is true;
the same explicitly `APPROVED` project terminology supplied to Agent B; project
rules. Agent A receives no Agent B translation, synthesis output, or critic
conclusions from the other forward run.
Output: `work/agent-a/candidates.jsonl`.
Agent A must not see B.

## Stage 2 - Agent B
Same source input and same explicitly `APPROVED` project terminology. Output:
`work/agent-b/candidates.jsonl`. Agent B must not see Agent A's translation,
synthesis output, or critic conclusions from the other forward run. Unapproved
terminology discoveries are not mandatory wording for either forward translator.

## Stage 3 - Agent C synthesis
Input: exact source + A + B + approved glossary.
Output: `work/synthesis/synthesis.jsonl` and `work/synthesis/disagreements.tsv`.
Every changed/combined decision gets a short auditable note.

## Stage 4 - blind back-translation
Create an input containing only `unit_id` + synthesized Finnish text. No English source text.
Output: `work/backtranslation/backtranslation.jsonl`.

## Stage 5 - critics
Run at least:
- clinical/semantic critic
- Finnish plain-language/cultural critic
- adversarial independent critic
Output structured issue records in `work/critics/`.

## Stage 6 - human adjudication
Use `templates/human_review.tsv`. Every translation-evidence source must be explicitly signed off. High-risk or disputed sources require clinical reviewer attention even if models agree. Translation adjudication does not resolve whether a noncanonical source requirement belongs in the final publication.

`PENDING_AUTHORITY` may record that an unresolved noncanonical requirement still awaits source-authority disposition. It cannot satisfy release readiness.

## Stage 6A - final source reconciliation
Record explicit source-authority/human dispositions for every authority-required canonical wording and official source requirement. Canonical exception dispositions require a unit-linked decision, decision maker/authority, date, evidence reference, and final status. `INCLUDE` or `EXCLUDE` is a source-set decision; neither may be inferred from model output, translation completion, or reviewer agreement. `S4A-2026-000` may proceed through translation and review, but its authoritative final title wording remains subject to this disposition.

## Stage 7 - document generation
Only after G0-G5 pass and final source reconciliation has no unresolved inclusion decisions:
- copy official DOCX
- insert approved Finnish text after the corresponding English line
- never alter original English
- never insert an unresolved official source requirement automatically
- select insertion inputs only from typed evidence sources whose `eligible_for_document_insertion` flag is explicitly true
- preserve original layout and marks
- render DOCX to images and inspect every page

## Stage 8 - field testing / external review
Record target-user/staff testing, revisions, and University of St Andrews / SPICT programme review state. Do not call a draft approved before that state is documented.
