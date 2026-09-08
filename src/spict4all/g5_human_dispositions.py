"""Explicit Project Owner G5 dispositions. Do not reinterpret these records."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Literal, TypedDict

DispositionName = Literal["ACCEPT_CURRENT", "ACCEPT_WITH_EDIT"]
SUPERSEDED_AT_G5 = "EXISTING_HUMAN_DECISION_RECONSIDERED_AND_SUPERSEDED_AT_G5"
NONE_RECORDED = "NONE_RECORDED"
DECISION_SOURCE = "explicit Project Owner decision in ChatGPT project session"
REVIEWER = "Project Owner"
REVIEWER_ROLE = "Project Owner / human adjudicator"
DECISION_DATE = "2026-09-08"
DISPOSITION_BATCH_ID = "WP-G5-HUMAN-DISPOSITION-BATCH-001"
PARTIAL_STATUS = "PARTIAL_HUMAN_ADJUDICATION_5_OF_54"
EVENT_KEYS = (
    "unit_id",
    "run_id",
    "human_disposition",
    "final_finnish",
    "reviewer",
    "reviewer_role",
    "decision_rationale",
    "decision_date",
    "decision_source",
    "prior_human_decision_status",
    "critic_evidence_considered",
    "source_authority_resolved",
)
SAMI_REVIEW_IDS = (
    "S4A-2026-017",
    "S4A-2026-021",
    "S4A-2026-025",
    "S4A-2026-026",
    "S4A-2026-045",
    "S4A-2026-049",
)
DOMAIN_EXPERT_OPTIONS = (
    "ACCEPT_CURRENT",
    "ACCEPT_WITH_EDIT",
    "REJECT_AND_REWRITE",
    "NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW",
)


class HumanDisposition(TypedDict):
    unit_id: str
    human_disposition: DispositionName
    final_finnish: str
    reviewer: str
    reviewer_role: str
    decision_rationale: str
    decision_date: str
    decision_source: str
    prior_human_decision_status: str
    critic_evidence_considered: str
    source_authority_resolved: bool


BATCH_DECISIONS: tuple[HumanDisposition, ...] = (
    {
        "unit_id": "S4A-2026-001",
        "human_disposition": "ACCEPT_WITH_EDIT",
        "final_finnish": (
            "SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä "
            "terveydentiloja ja jotka voivat huonommin. Nämä ihmiset tarvitsevat "
            "nyt enemmän apua ja hoitoa sekä suunnitelman tulevasta hoidosta."
        ),
        "reviewer": REVIEWER,
        "reviewer_role": REVIEWER_ROLE,
        "decision_rationale": (
            'The previously recorded Project Owner wording "terveydentila on '
            'heikentynyt" was explicitly reconsidered at G5 after independent '
            'critic review. The source "are less well" describes a poorer current '
            "state and does not necessarily require an identifiable deterioration "
            'event. "jotka voivat huonommin" was selected for closer source '
            f"fidelity and plain-language intent. {SUPERSEDED_AT_G5}"
        ),
        "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "prior_human_decision_status": SUPERSEDED_AT_G5,
        "critic_evidence_considered": (
            "G4 Critic A MEDIUM and Critic B LOW independently flagged the "
            "recorded wording terveydentila on heikentynyt against source "
            '"are less well". Critic proposed Finnish was not applied by this '
            "recording step; the Project Owner selected the final Finnish."
        ),
        "source_authority_resolved": False,
    },
    {
        "unit_id": "S4A-2026-008",
        "human_disposition": "ACCEPT_CURRENT",
        "final_finnish": (
            "Hänellä on hankalia oireita suurimman osan ajasta, vaikka hänen "
            "terveysongelmiaan hoidetaan hyvin."
        ),
        "reviewer": REVIEWER,
        "reviewer_role": REVIEWER_ROLE,
        "decision_rationale": (
            'The Project Owner reviewed Critic B\'s concern about "hoidetaan '
            'hyvin". In this context the Finnish is understood as the health '
            "problems being treated well/appropriately, preserving the source "
            'meaning "despite good treatment of their health problems". No edit '
            "was considered necessary."
        ),
        "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "prior_human_decision_status": NONE_RECORDED,
        "critic_evidence_considered": (
            "G4 Critic B MEDIUM flagged a possible shift from adequate treatment "
            "of the problems to being treated well. Critic A recorded OK/NONE. "
            "The Project Owner accepted the current Finnish without edit."
        ),
        "source_authority_resolved": False,
    },
    {
        "unit_id": "S4A-2026-009",
        "human_disposition": "ACCEPT_WITH_EDIT",
        "final_finnish": (
            "Henkilö (tai perhe) pyytää palliatiivista hoitoa; valitsee hoidon "
            "vähentämisen, lopettamisen tai sen, ettei ota hoitoa vastaan; tai "
            "haluaa keskittyä elämänlaatuun."
        ),
        "reviewer": REVIEWER,
        "reviewer_role": REVIEWER_ROLE,
        "decision_rationale": (
            'The edit removes the ambiguity of "ottamatta jättäminen", which '
            "could be read as merely skipping or not taking treatment, and makes "
            'the treatment-receipt choice explicit. "haluaa keskittyä" preserves '
            'the agency in "wishes to focus" more directly.'
        ),
        "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "prior_human_decision_status": NONE_RECORDED,
        "critic_evidence_considered": (
            "G4 Critic A LOW and Critic B MEDIUM flagged ottamatta jättäminen / "
            "not have treatment and weakened agency on wishes to focus. Critic "
            "proposed Finnish was not applied by this recording step; the "
            "Project Owner selected the final Finnish."
        ),
        "source_authority_resolved": False,
    },
    {
        "unit_id": "S4A-2026-036",
        "human_disposition": "ACCEPT_WITH_EDIT",
        "final_finnish": (
            "Ei pysty viestimään puhumalla; ei juuri reagoi muihin ihmisiin."
        ),
        "reviewer": REVIEWER,
        "reviewer_role": REVIEWER_ROLE,
        "decision_rationale": (
            'The previous wording "ei vastaa juurikaan muihin ihmisiin" is '
            'unnatural and semantically unstable Finnish. "ei juuri reagoi muihin '
            'ihmisiin" preserves the source meaning of limited responsiveness '
            "without introducing a diagnosis."
        ),
        "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "prior_human_decision_status": NONE_RECORDED,
        "critic_evidence_considered": (
            "G4 Critic B MEDIUM flagged semantically odd Finnish in the second "
            "clause. Critic A recorded OK/NONE. Critic proposed Finnish was not "
            "applied by this recording step; the Project Owner selected the "
            "final Finnish."
        ),
        "source_authority_resolved": False,
    },
    {
        "unit_id": "S4A-2026-042",
        "human_disposition": "ACCEPT_WITH_EDIT",
        "final_finnish": (
            "Ihmiset, jotka voivat huonommin ja joilla on muita elinikää "
            "lyhentäviä fyysisiä sairauksia, mielenterveyden sairauksia tai "
            "terveydentiloja. Hoitoa ei ole saatavilla tai se ei tehoa hyvin."
        ),
        "reviewer": REVIEWER,
        "reviewer_role": REVIEWER_ROLE,
        "decision_rationale": (
            'The previously recorded Project Owner wording "terveydentila on '
            'heikentynyt" was explicitly reconsidered at G5 after independent '
            'critic review. The source "are less well" describes poorer current '
            "health without necessarily asserting a deterioration event. "
            '"jotka voivat huonommin" was selected for closer source fidelity. '
            f'The existing "ei tehoa hyvin" wording is retained. {SUPERSEDED_AT_G5}'
        ),
        "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "prior_human_decision_status": SUPERSEDED_AT_G5,
        "critic_evidence_considered": (
            "G4 Critic A MEDIUM and Critic B LOW independently flagged the "
            "recorded wording terveydentila on heikentynyt against source "
            '"are less well". Critic proposed Finnish was not applied by this '
            "recording step; the Project Owner selected the final Finnish."
        ),
        "source_authority_resolved": False,
    },
)
BATCH_IDS = tuple(row["unit_id"] for row in BATCH_DECISIONS)
BATCH_BY_ID: dict[str, HumanDisposition] = {
    row["unit_id"]: row for row in BATCH_DECISIONS
}
COMPLETED_DISPOSITIONS = 5
REMAINING_DISPOSITIONS = 49
HUMAN_TSV_FIELDS = (
    "human_disposition",
    "final_finnish",
    "reviewer",
    "reviewer_role",
    "decision_rationale",
    "decision_date",
)
FROZEN_TSV_FIELDS = (
    "unit_id",
    "review_tier",
    "source_text_en",
    "current_candidate_fi",
    "combined_review_priority",
    "finding_status",
    "existing_human_decision",
    "domain_expert_review_recommended",
    "source_authority_status",
)


def overlay_disposition_row(row: dict[str, str]) -> dict[str, str]:
    updated = dict(row)
    decision = BATCH_BY_ID.get(row["unit_id"])
    if decision is None:
        for field in HUMAN_TSV_FIELDS:
            updated[field] = ""
        return updated
    updated["human_disposition"] = decision["human_disposition"]
    updated["final_finnish"] = decision["final_finnish"]
    updated["reviewer"] = decision["reviewer"]
    updated["reviewer_role"] = decision["reviewer_role"]
    updated["decision_rationale"] = decision["decision_rationale"]
    updated["decision_date"] = decision["decision_date"]
    return updated


def dispositions_with_batch(blank_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [overlay_disposition_row(row) for row in blank_rows]


def encode_dispositions_tsv(
    rows: list[dict[str, str]],
    columns: tuple[str, ...],
) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(columns),
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row[column] for column in columns})
    return buffer.getvalue()


def event_record(run_id: str, decision: HumanDisposition) -> dict[str, Any]:
    return {
        "unit_id": decision["unit_id"],
        "run_id": run_id,
        "human_disposition": decision["human_disposition"],
        "final_finnish": decision["final_finnish"],
        "reviewer": decision["reviewer"],
        "reviewer_role": decision["reviewer_role"],
        "decision_rationale": decision["decision_rationale"],
        "decision_date": decision["decision_date"],
        "decision_source": decision["decision_source"],
        "prior_human_decision_status": decision["prior_human_decision_status"],
        "critic_evidence_considered": decision["critic_evidence_considered"],
        "source_authority_resolved": decision["source_authority_resolved"],
    }


def encode_decision_events(run_id: str) -> str:
    lines: list[str] = []
    for decision in BATCH_DECISIONS:
        ordered = {key: event_record(run_id, decision)[key] for key in EVENT_KEYS}
        lines.append(json.dumps(ordered, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def overlay_summary(summary: dict[str, Any]) -> dict[str, Any]:
    updated = dict(summary)
    updated["status"] = PARTIAL_STATUS
    updated["work_package_disposition_batch"] = DISPOSITION_BATCH_ID
    updated["completed_human_dispositions"] = COMPLETED_DISPOSITIONS
    updated["remaining_human_dispositions"] = REMAINING_DISPOSITIONS
    updated["populated_human_disposition_ids"] = list(BATCH_IDS)
    updated["human_adjudication_complete"] = False
    updated["human_adjudication_performed"] = False
    updated["human_disposition_prepopulated"] = False
    updated["final_finnish_prepopulated"] = False
    updated["g5_gate_passed"] = False
    updated["g5_audit_zip_created"] = False
    updated["g6_started"] = False
    updated["document_generation_started"] = False
    updated["source_authority_resolved"] = False
    updated["clinical_validation_claimed"] = False
    updated["human_decision_authority"] = (
        "Project Owner explicit disposition. AI output is not human approval."
    )
    return updated


def overlay_run_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    updated = dict(metadata)
    updated["g5_status"] = PARTIAL_STATUS
    updated["work_package_disposition_batch"] = DISPOSITION_BATCH_ID
    updated["completed_human_dispositions"] = COMPLETED_DISPOSITIONS
    updated["remaining_human_dispositions"] = REMAINING_DISPOSITIONS
    updated["populated_human_disposition_ids"] = list(BATCH_IDS)
    updated["human_adjudication_complete"] = False
    updated["human_adjudication_performed"] = False
    updated["g5_gate_passed"] = False
    updated["g5_audit_zip_created"] = False
    updated["g6_started"] = False
    updated["source_authority_resolved"] = False
    updated["clinical_validation_claimed"] = False
    updated["finnish_revised"] = False
    updated["g2_changed"] = False
    updated["g3_changed"] = False
    updated["g4_changed"] = False
    return updated
