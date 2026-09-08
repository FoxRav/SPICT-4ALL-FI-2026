# T1 terminology adjudication preparation

Work package: WP-T1-TERMINOLOGY-ADJUDICATION-PREP-001

NO TERMINOLOGY DECISION HAS BEEN APPROVED BY THIS RUN

## Scope and counts

Inspected all 54 translation-evidence sources: 53 canonical units and S4A-REQ-2026-001. The canonical title and liver requirement retain their separate unresolved source-authority states. Source text and hashes are preserved in source_screening.jsonl and input_integrity.json.

All 136 extracted entries from 5 registered references were semantically considered, including 41 entries with explicit English labels and 95 without. semantic_search_scope.json records the entire search inventory. This was model analysis of the extracted evidence; no new translation, clinical validation, source extraction, or external literature search was performed.

- Terminology-sensitive decision concepts found / queue count: 29 / 29.
- Clinical risks: HIGH 21, MEDIUM 8, LOW 0.
- Direct source-provided English/Finnish relationship for the SPICT concept (SOURCE_EXPLICIT): 0.
- Finnish-only candidate wording with model correspondence (SOURCE_DERIVED_FINNISH_ONLY): 4.
- Model-proposed wording or transferred relationship from evidence (MODEL_PROPOSED_FROM_EVIDENCE): 9.
- No reliable correspondence in the extracted set (NO_RELIABLE_TERMINOLOGY_EVIDENCE): 16.
- Concepts with a retained MODEL_SEMANTIC_MAPPING connection: 13 (31 evidence edges). This overlaps Finnish-only and model-proposed counts; it is not an additional mutually exclusive category.
- Relevant existing conflicts: 3; not included: 3.
- APPROVED project terminology: 0. Conservative exact-English relevance matches remain 0.

A term appearing in Finnish is not proof of an English/Finnish pair. In particular, source-explicit advance care planning is preserved literally; using its Finnish wording for SPICT care plans is a model transfer. Patient and healthcare client labels do not establish an equivalent for person. No direct pair was manufactured to raise the direct-evidence count.

No-evidence candidates and alternatives are blank, not model guesses. No-evidence means no reliable correspondence among these 136 extracted records, not absence from all Finnish terminology or every page of the original PDFs. The source terms Dyspnea and Inoperaabeli remain visible alongside the exact Finnish definitions from which the proposed plain wording is taken.

## MUST DECIDE BEFORE G1

5 proposed human scope dispositions:

- T-001 — palliative care: see the exact evidence, limitations and alternatives in the human review document.
- T-002 — life shortening health conditions: see the exact evidence, limitations and alternatives in the human review document.
- T-003 — carer: see the exact evidence, limitations and alternatives in the human review document.
- T-004 — care plans / planning future care: see the exact evidence, limitations and alternatives in the human review document.
- T-005 — reduce, stop or not have treatment / stopping or not starting dialysis: see the exact evidence, limitations and alternatives in the human review document.

These five priorities address repeated scope, agency and role risks. A human disposition may explicitly LEAVE UNCONTROLLED or require further clinical review; it need not approve a single Finnish wording. They are preparation recommendations, not a new executable gate or evidence that G1 has been released. No decision has been made by this run.

## MAY REMAIN UNCONTROLLED FOR INDEPENDENT A/B TRANSLATION

The remaining concepts may remain uncontrolled while A/B independently produce evidence from the English source. High clinical risk still requires later careful review and per-unit human sign-off; it does not by itself justify forcing unapproved terminology into the independent inputs.

- T-006 — kidney dialysis
- T-007 — quality of life
- T-008 — dementia
- T-009 — frailty
- T-010 — heart failure
- T-011 — liver transplant
- T-012 — short of breath / respiratory problems
- T-013 — breathing machine
- T-014 — symptoms / treatment to help with symptoms
- T-015 — no treatment available / treatment will not work well
- T-016 — holistic care
- T-017 — functional problems / ongoing disability
- T-018 — spiritual problems
- T-019 — cultural problems
- T-020 — urgent or emergency hospital admissions or visits
- T-021 — specialist help
- T-022 — person: scope relative to patient / healthcare client
- T-023 — help and care needed
- T-024 — nurse, doctor, social worker or other staff
- T-025 — surgery is not possible
- T-026 — medicines and other treatments
- T-027 — one or more strokes
- T-028 — difficulty with swallowing
- T-029 — being confused at times

## All six existing conflicts

The existing conflict ledger remains unchanged and HUMAN_REVIEW_REQUIRED. NOT_INCLUDED below is a model relevance assessment, not a resolution. Some pairs appear to differ in link markup; that observation does not authorize this run to resolve them.

- TERM-CONFLICT-001 — RELEVANT; decisions: T-023. MODEL_SEMANTIC_MAPPING: Potential service-need narrowing of help/care is assessed in T-023. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.
- TERM-CONFLICT-002 — RELEVANT; decisions: T-022. MODEL_SEMANTIC_MAPPING: Patient-versus-person scope is assessed in T-022. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.
- TERM-CONFLICT-003 — NOT_INCLUDED; decisions: none. MODEL_SEMANTIC_MAPPING: The 54 sources do not name the combined healthcare-and-social-welfare system; no controlled system term is proposed. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.
- TERM-CONFLICT-004 — RELEVANT; decisions: T-022. MODEL_SEMANTIC_MAPPING: Healthcare-client-versus-person scope is assessed in T-022. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.
- TERM-CONFLICT-005 — NOT_INCLUDED; decisions: none. MODEL_SEMANTIC_MAPPING: The 54 sources do not name the healthcare system as a terminology decision; care must not be equated with that system. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.
- TERM-CONFLICT-006 — NOT_INCLUDED; decisions: none. MODEL_SEMANTIC_MAPPING: No source unit names health services as such; help/care/support are not automatically formal health services. Status remains HUMAN_REVIEW_REQUIRED; resolution blank.

## Screening and evidence limits

The 29 decisions group closely related source occurrences, not all individual words. source_screening.jsonl contains a row for every inspected unit, including headings and observations without an added control. Ordinary cancer/kidney/liver headings, weight change, oxygen use, infections, and the version identifier receive no invented terminology requirement. Concrete liver observations remain plain observations rather than inferred diagnoses. Power of Attorney is absent from these 54 sources and was not imported from the older glossary's guidance-only item.

Review risks and semantic correspondence are model assessments. The quoted original metadata/definitions may be incomplete or dated; human reviewers must assess currency and clinical applicability. This run supplies no treatment advice and no clinical validation.

## Files and reproducibility

- TERMINOLOGY_ADJUDICATION_QUEUE.tsv: 19 requested columns, one row per decision. Pipe-separated IDs; quoted multiline cells preserve the complete English source text in listed-ID order.
- TERMINOLOGY_HUMAN_REVIEW.md: all decisions, exact source quotations/provenance and unchecked choices.
- human_terminology_decisions.tsv: same IDs; every decision, final-term and attribution field blank.
- terminology_adjudication_evidence.jsonl: exact original evidence record per proposed connection, source hashes, explicit English origin, model explanation and blank human decision.
- model_mapping_plan.json: authored model analysis and six conflict relevance assessments, not source evidence or a human decision.
- source_screening.jsonl, semantic_search_scope.json and input_integrity.json: complete inspection scope and protected-input hashes.

Validate with `.venv/Scripts/python.exe scripts/validate_t1_adjudication.py`. Full command outcomes and Git status are recorded in T1_VALIDATION_RESULTS.json after the preparation checks run. Tests cover blank human fields, approval injection, source/evidence references, origin laundering, unresolved conflicts, protected source integrity and absence of translation work artifacts.

Preparation does not modify the approved glossary, original evidence, English sources, quality gates or source-authority decisions. A/B receive no mandatory wording from this queue. No Agent A/B run, commit or push was performed.
