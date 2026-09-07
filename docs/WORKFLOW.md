# Translation workflow

## Stage 0 - freeze source
Run `python scripts/verify_sources.py`. Any hash mismatch is a hard stop.

## Stage 1 - Agent A
Input: `data/source_units.jsonl`, approved terminology only, project rules.
Output: `work/agent-a/candidates.jsonl`.
Agent A must not see B.

## Stage 2 - Agent B
Same source input. Output: `work/agent-b/candidates.jsonl`.
Agent B must not see A.

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
Use `templates/human_review.tsv`. Every unit must be explicitly signed off. High-risk or disputed units require clinical reviewer attention even if models agree.

## Stage 7 - document generation
Only after G0-G5 pass:
- copy official DOCX
- insert approved Finnish text after the corresponding English line
- never alter original English
- preserve original layout and marks
- render DOCX to images and inspect every page

## Stage 8 - field testing / external review
Record target-user/staff testing, revisions, and University of St Andrews / SPICT programme review state. Do not call a draft approved before that state is documented.
