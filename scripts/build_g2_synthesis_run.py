"""Build the G2-20260908-001 synthesis run from authored decisions and frozen inputs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from spict4all.errors import ArtifactValidationError, ImmutableRunError
from spict4all.g2_authored import DECISIONS
from spict4all.g2_synthesis import (
    ACTUAL_MODEL,
    AGENT_A_ARTIFACT,
    AGENT_A_MODEL,
    AGENT_B_MODEL,
    AGENT_B_R2_ARTIFACT,
    CLASSIFICATIONS,
    CONFIGURED_ROLE_MODEL,
    EXPECTED_AGREE,
    EXPECTED_COUNT,
    EXPECTED_DISAGREE,
    FROZEN_INPUT_HASHES,
    G2_ROLE,
    G2_RUN_ID,
    REQUIREMENT_ID,
    RUN_METADATA_ROLE,
    SAME_FAMILY_LIMITATION,
    STATUS,
    TITLE_ID,
    candidate_schema_failures,
    classification_counts,
    expected_source_index,
    g2_failures,
    load_jsonl_records,
    verify_frozen_inputs,
)
from spict4all.hashing import sha256_file
from spict4all.jsonl import load_jsonl
from spict4all.runs import build_run_metadata, create_immutable_run

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime.now(UTC).isoformat().replace("+00:00", "Z")


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def english_from_forward(row: dict[str, Any]) -> str:
    extensions = row.get("extensions")
    if isinstance(extensions, dict):
        agent_a = extensions.get("g1_agent_a")
        if isinstance(agent_a, dict) and isinstance(agent_a.get("source_text_en"), str):
            return str(agent_a["source_text_en"])
        forward = extensions.get("g1_forward")
        if isinstance(forward, dict) and isinstance(forward.get("exact_source_text_en"), str):
            return str(forward["exact_source_text_en"])
    raise ArtifactValidationError(f"{row.get('unit_id')}: missing English in G1 candidate")


def provenance_from_b(row: dict[str, Any]) -> dict[str, Any]:
    extensions = row.get("extensions")
    if not isinstance(extensions, dict):
        raise ArtifactValidationError(f"{row.get('unit_id')}: missing B extensions")
    forward = extensions.get("g1_forward")
    if not isinstance(forward, dict):
        raise ArtifactValidationError(f"{row.get('unit_id')}: missing g1_forward")
    return {
        "source_kind": forward.get("source_kind"),
        "source_role": forward.get("source_role"),
        "document_part": forward.get("document_part"),
        "source_location": forward.get("source_location"),
        "final_inclusion_status": forward.get("final_inclusion_status"),
        "eligible_for_document_insertion": forward.get("eligible_for_document_insertion"),
    }


def issues_for(unit_id: str, remaining: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if unit_id == TITLE_ID:
        issues.append(
            {
                "severity": "BLOCKER",
                "type": "unresolved_source_authority",
                "note": (
                    "S4A-2026-000 remains UNRESOLVED and not eligible for document "
                    "insertion. This G2 candidate is translation evidence only."
                ),
            }
        )
    if unit_id == REQUIREMENT_ID:
        issues.append(
            {
                "severity": "BLOCKER",
                "type": "unresolved_source_authority",
                "note": (
                    "S4A-REQ-2026-001 remains a noncanonical unresolved official "
                    "change requirement and publication-blocking. Not inserted "
                    "into canonical membership."
                ),
            }
        )
    if remaining.strip():
        issues.append(
            {
                "severity": "NOTE",
                "type": "wording_uncertainty",
                "note": remaining.strip(),
            }
        )
    return issues


def report_text(
    counts: dict[str, int],
    candidate_sha: str,
    decision_sha: str,
) -> str:
    return f"""# SPICT-4ALL FI — G2 synthesis

Work package: **WP-G2-SYNTHESIS-001**
Run: **{G2_RUN_ID}**
Role: **{G2_ROLE}**
**Actual model used: {ACTUAL_MODEL}**

Configured / planned synthesis role model in `config/model_roles.yaml`: {CONFIGURED_ROLE_MODEL}.
These identities differ. The discrepancy is preserved. Cursor Grok 4.6 performed G2.
Claude Opus, Claude Fable, and GPT-6 did not perform G2.

## Methodological limitation

Forward Translator A used **{AGENT_A_MODEL}**.
Forward Translator B used **{AGENT_B_MODEL}**.
G2 synthesis also used **{ACTUAL_MODEL}**.

{SAME_FAMILY_LIMITATION}

This limitation does not block G2.

## Coverage

- Translation-evidence items: **{EXPECTED_COUNT}/54**
- Canonical source units: **53** + source requirement **1**
- Exact A/B wording agreements: **{EXPECTED_AGREE}** (`A_B_AGREE`)
- A/B wording disagreements: **{EXPECTED_DISAGREE}**
- `SELECT_A`: {counts['SELECT_A']}
- `SELECT_B`: {counts['SELECT_B']}
- `COMBINE_A_B`: {counts['COMBINE_A_B']}
- `NEW_SYNTHESIS`: {counts['NEW_SYNTHESIS']}

Every unit has exactly one classification. Disagreements have an explicit
source-fidelity rationale. Status is `{STATUS}`: model-generated G2 synthesis
evidence, not human approval. No human-approval status is recorded.

## Binding human wording used

- T-002 elinikää lyhentävät terveydentilat (S4A-2026-001, S4A-2026-042)
- T-013 hengityskone (S4A-2026-035)
- T-016 kokonaisvaltainen hoito (S4A-2026-049)
- less well → terveydentila on heikentynyt (S4A-2026-001, S4A-2026-042)
- less able to manage usual activities → toimintakyky on heikentynyt with tavanomaisissa toimissa (S4A-2026-004, S4A-2026-014)
- not well enough for cancer treatment → ei ole riittävän hyväkuntoinen syöpähoitoon (S4A-2026-017)

No missing decision IDs were invented. Glossary APPROVED rows remain 0.

## Source authority preserved, not resolved

- `S4A-2026-000`: Finnish synthesis produced; UNRESOLVED; not insertable; publication-blocking where currently defined.
- `S4A-REQ-2026-001`: Finnish synthesis produced; noncanonical; unresolved canonical omission; publication-blocking; not silently added to canonical membership.

## Genuine remaining wording uncertainties

These did not block a working synthesis:

- Supportive care has no approved Finnish project term (S4A-2026-000).
- Frailty/hauraus has no recorded final human term (S4A-2026-021).
- spiritual is kept as henkinen ja hengellinen so it is not narrowed to religion only (S4A-2026-049).
- stroke/aivohalvaus scope remains a prior T1 SAMI item (S4A-2026-047).
- chest infections is rendered plainly as rintakehän infektioita rather than medicalized (S4A-2026-045).
- The English relative clause in S4A-2026-002 can attach to health problems or to both alternatives; Finnish follows the nearest-antecedent reading.

## Document-level review

The 54 Finnish units were reread as one body for omission, addition, negation,
modality, time, agency, roles, alternatives, causality, narrowing/expansion,
treatment choice, and terminology consistency. Carer is huolehtiva ihminen
(006, 046). Physical health is fyysinen (005, 041, 042, 047). Communicate is
viestiä (036, 043). Dialysis is dialyysi without an added hoito (019, 020).
Resting/moving/walking a few steps is aligned (015, 025). T-002, T-013, T-016
and the three recorded unbound human wordings are preserved where they apply.

Mechanical checks do not prove semantic or clinical correctness.
These results are not clinical validation.

## Frozen inputs

- `{AGENT_A_ARTIFACT}`: `{FROZEN_INPUT_HASHES[AGENT_A_ARTIFACT]}`
- `{AGENT_B_R2_ARTIFACT}`: `{FROZEN_INPUT_HASHES[AGENT_B_R2_ARTIFACT]}`
- `work/agent-b/candidates.jsonl` (historical original B only): `{FROZEN_INPUT_HASHES['work/agent-b/candidates.jsonl']}`
- G1 gate ZIP: `{FROZEN_INPUT_HASHES['deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip']}`

## Output hashes

- `work/synthesis/{G2_RUN_ID}/candidates.jsonl`: `{candidate_sha}`
- `work/synthesis/{G2_RUN_ID}/synthesis_decisions.jsonl`: `{decision_sha}`

G3 was not started. No commit or push is performed by this builder.
"""


def build_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    verify_frozen_inputs(ROOT)
    if len(DECISIONS) != EXPECTED_COUNT:
        raise ArtifactValidationError(f"authored decision count is {len(DECISIONS)}")
    ids = [str(row["unit_id"]) for row in DECISIONS]
    if len(set(ids)) != EXPECTED_COUNT:
        raise ArtifactValidationError("authored decision IDs are not unique")
    units = load_jsonl(ROOT / "data/source_units.jsonl")
    requirements = load_jsonl(ROOT / "data/source_requirements.jsonl")
    expected = expected_source_index(units, requirements)
    agent_a = load_jsonl_records((ROOT / AGENT_A_ARTIFACT).read_text(encoding="utf-8"))
    agent_b = load_jsonl_records((ROOT / AGENT_B_R2_ARTIFACT).read_text(encoding="utf-8"))
    a_by_id = {str(row["unit_id"]): row for row in agent_a}
    b_by_id = {str(row["unit_id"]): row for row in agent_b}
    authored = {str(row["unit_id"]): row for row in DECISIONS}
    if set(authored) != set(expected):
        raise ArtifactValidationError("authored IDs differ from frozen source universe")
    candidates: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for unit_id, (english, digest, kind) in expected.items():
        item = authored[unit_id]
        a_row = a_by_id[unit_id]
        b_row = b_by_id[unit_id]
        if english_from_forward(a_row) != english or english_from_forward(b_row) != english:
            raise ArtifactValidationError(f"{unit_id}: G1 English differs from frozen source")
        if a_row["source_text_sha256"] != digest or b_row["source_text_sha256"] != digest:
            raise ArtifactValidationError(f"{unit_id}: G1 source SHA differs from frozen source")
        classification = str(item["classification"])
        if classification not in CLASSIFICATIONS:
            raise ArtifactValidationError(f"{unit_id}: invalid classification")
        provenance = provenance_from_b(b_row)
        remaining = str(item["remaining"])
        candidate_fi = str(item["candidate_fi"])
        note = (
            f"G2 {classification}. Model-generated synthesis evidence; not human approval. "
            f"{str(item['source_fidelity_rationale'])}"
        )
        candidates.append(
            {
                "unit_id": unit_id,
                "source_text_sha256": digest,
                "model": ACTUAL_MODEL,
                "session_id": G2_RUN_ID,
                "prompt_version": "WP-G2-SYNTHESIS-001",
                "candidate_fi": candidate_fi,
                "decision_note": note,
                "issues": issues_for(unit_id, remaining),
                "status": STATUS,
                "extensions": {
                    "g2_synthesis": {
                        "run_id": G2_RUN_ID,
                        "run_timestamp_utc": CREATED_AT,
                        "translator_role": G2_ROLE,
                        "actual_model": ACTUAL_MODEL,
                        "configured_role_model": CONFIGURED_ROLE_MODEL,
                        "classification": classification,
                        "exact_source_text_en": english,
                        "source_kind": kind,
                        "source_role": provenance["source_role"],
                        "document_part": provenance["document_part"],
                        "source_location": provenance["source_location"],
                        "final_inclusion_status": provenance["final_inclusion_status"],
                        "eligible_for_document_insertion": provenance[
                            "eligible_for_document_insertion"
                        ],
                        "same_family_limitation": SAME_FAMILY_LIMITATION,
                    }
                },
            }
        )
        decisions.append(
            {
                "unit_id": unit_id,
                "source_text_sha256": digest,
                "source_text_en": english,
                "agent_a_candidate_fi": a_row["candidate_fi"],
                "agent_a_artifact": AGENT_A_ARTIFACT,
                "agent_a_artifact_sha256": FROZEN_INPUT_HASHES[AGENT_A_ARTIFACT],
                "agent_b_r2_candidate_fi": b_row["candidate_fi"],
                "agent_b_r2_artifact": AGENT_B_R2_ARTIFACT,
                "agent_b_r2_artifact_sha256": FROZEN_INPUT_HASHES[AGENT_B_R2_ARTIFACT],
                "classification": classification,
                "candidate_fi": candidate_fi,
                "source_fidelity_rationale": item["source_fidelity_rationale"],
                "meaningful_difference": item["meaningful_difference"],
                "remaining": remaining,
                "human_decision_refs": item["human_decision_refs"],
                "actual_model": ACTUAL_MODEL,
                "run_id": G2_RUN_ID,
            }
        )
    counts = classification_counts(decisions)
    if counts["A_B_AGREE"] != EXPECTED_AGREE:
        raise ArtifactValidationError(f"A_B_AGREE count is {counts['A_B_AGREE']}")
    if sum(counts[key] for key in CLASSIFICATIONS if key != "A_B_AGREE") != EXPECTED_DISAGREE:
        raise ArtifactValidationError("disagreement classifications do not sum to 37")
    schema_failures = candidate_schema_failures(
        candidates, ROOT / "schemas/translation_candidate.schema.json"
    )
    if schema_failures:
        raise ArtifactValidationError("G2 candidate schema failed: " + "; ".join(schema_failures))
    failures = g2_failures(candidates, decisions, expected, agent_a, agent_b)
    if failures:
        raise ArtifactValidationError("G2 validation failed: " + "; ".join(failures))
    return candidates, decisions, counts


def main() -> None:
    candidates, decisions, counts = build_records()
    inputs = [
        ROOT / AGENT_A_ARTIFACT,
        ROOT / AGENT_B_R2_ARTIFACT,
        ROOT / "data/source_units.jsonl",
        ROOT / "data/source_requirements.jsonl",
        ROOT / "terminology/adjudication/human_terminology_decisions.tsv",
        ROOT / "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
        ROOT / "deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip",
    ]
    metadata = build_run_metadata(
        G2_RUN_ID,
        RUN_METADATA_ROLE,
        inputs,
        created_at_utc=CREATED_AT,
    )
    metadata["actual_model"] = ACTUAL_MODEL
    metadata["configured_role_model"] = CONFIGURED_ROLE_MODEL
    metadata["same_family_limitation"] = SAME_FAMILY_LIMITATION
    metadata["agent_a_model"] = AGENT_A_MODEL
    metadata["agent_b_model"] = AGENT_B_MODEL
    metadata["authoritative_b_run"] = AGENT_B_R2_ARTIFACT
    metadata["work_package"] = "WP-G2-SYNTHESIS-001"
    try:
        run_dir = create_immutable_run(ROOT / "work/synthesis", metadata)
    except ImmutableRunError:
        raise
    write_jsonl(run_dir / "candidates.jsonl", candidates)
    write_jsonl(run_dir / "synthesis_decisions.jsonl", decisions)
    candidate_sha = sha256_file(run_dir / "candidates.jsonl")
    decision_sha = sha256_file(run_dir / "synthesis_decisions.jsonl")
    (run_dir / "G2_SYNTHESIS_REPORT.md").write_text(
        report_text(counts, candidate_sha, decision_sha),
        encoding="utf-8",
        newline="\n",
    )
    validation = {
        "run_id": G2_RUN_ID,
        "actual_model": ACTUAL_MODEL,
        "tests_note": "Repository tests and validators are recorded in the G2 audit package.",
        "candidate_count": EXPECTED_COUNT,
        "decision_count": EXPECTED_COUNT,
        "canonical_count": 53,
        "source_requirement_count": 1,
        "classifications": counts,
        "exact_ab_agreements": EXPECTED_AGREE,
        "exact_ab_disagreements": EXPECTED_DISAGREE,
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "g3_started": False,
        "title_authority_unresolved": True,
        "requirement_noncanonical_unresolved": True,
        "candidate_sha256": candidate_sha,
        "synthesis_decisions_sha256": decision_sha,
        "frozen_input_hashes": FROZEN_INPUT_HASHES,
        "mechanical_checks": "PASS",
        "semantic_correctness": "Not claimed. Mechanical checks are not clinical validation.",
    }
    (run_dir / "validation_results.json").write_text(encode_json(validation), encoding="utf-8")
    print(
        json.dumps(
            {
                "run_dir": str(run_dir.relative_to(ROOT).as_posix()),
                "classifications": counts,
                "candidate_sha256": candidate_sha,
                "synthesis_decisions_sha256": decision_sha,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
