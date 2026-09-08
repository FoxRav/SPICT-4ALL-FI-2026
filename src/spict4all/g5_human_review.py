"""G5 human-review preparation. This module does not adjudicate wording."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .errors import ArtifactValidationError
from .g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_RELATIVE,
    CRITIC_B_RELATIVE,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    FRAILTY_ID,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    HUMAN_DECISION_CONFLICTS,
    MEDIUM_PLUS,
    REQUIREMENT_ID,
    REVIEW_INPUT_RELATIVE,
    SOURCE_AUTHORITY_BLOCKERS,
    TITLE_ID,
)
from .hashing import sha256_file
from .jsonl import load_jsonl
from .runs import build_run_metadata

G5_RUN_ID = "G5-20260908-001"
G5_WORK_PACKAGE = "WP-G5-HUMAN-REVIEW-PREPARATION-001"
G5_ROLE = "G5 human-review preparation (not the human adjudicator)"
ACTUAL_MODEL = "Cursor Grok 4.6"
G5_STATUS = "PREPARATION_COMPLETE_AWAITING_HUMAN_DISPOSITION"
G5_RUN_DIR = Path("work") / "human-review" / G5_RUN_ID
COMBINED_SHA256 = "29d8ec2a0f8588de7a331088be0181eb169c84337e390d273957f2b86e1e5f19"
HUMAN_DECISIONS_RELATIVE = "terminology/adjudication/human_terminology_decisions.tsv"
T1_2_REPORT_RELATIVE = (
    "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md"
)
SOURCE_UNITS_RELATIVE = "data/source_units.jsonl"
SOURCE_REQUIREMENTS_RELATIVE = "data/source_requirements.jsonl"

ReviewTier = Literal["TIER_1", "TIER_2", "TIER_3"]
DISPOSITION_OPTIONS = (
    "ACCEPT_CURRENT",
    "ACCEPT_WITH_EDIT",
    "REJECT_AND_REWRITE",
    "ESCALATE_DOMAIN_EXPERT",
    "DEFER_SOURCE_AUTHORITY",
)
BLANK_HUMAN_FIELDS = (
    "human_disposition",
    "final_finnish",
    "reviewer",
    "reviewer_role",
    "decision_rationale",
    "decision_date",
)
TSV_COLUMNS = (
    "unit_id",
    "review_tier",
    "source_text_en",
    "current_candidate_fi",
    "combined_review_priority",
    "finding_status",
    "existing_human_decision",
    "domain_expert_review_recommended",
    "source_authority_status",
    *BLANK_HUMAN_FIELDS,
)
REQUIRED_OUTPUTS = (
    "G5_HUMAN_REVIEW_PACKET.md",
    "human_dispositions.tsv",
    "G5_PRIORITY_REVIEW.md",
    "G5_CLEAN_UNITS.md",
    "G5_REVIEW_SUMMARY.json",
)
FORBIDDEN_CLAIM_PHRASES = (
    "G5 PASS",
    "G5 gate passed",
    "clinically validated",
)
CHECKED_BOX = re.compile(r"\[[xX]\]")
EXPECTED_TIER_1 = (
    "S4A-2026-001",
    "S4A-2026-008",
    "S4A-2026-009",
    "S4A-2026-017",
    "S4A-2026-021",
    "S4A-2026-025",
    "S4A-2026-026",
    "S4A-2026-036",
    "S4A-2026-042",
    "S4A-2026-045",
    "S4A-2026-049",
)
EXPECTED_TIER_2 = (
    "S4A-2026-000",
    "S4A-2026-003",
    "S4A-2026-004",
    "S4A-2026-014",
    "S4A-2026-018",
    "S4A-2026-033",
    "S4A-2026-034",
    "S4A-2026-040",
    "S4A-2026-043",
    "S4A-2026-047",
)
DOMAIN_EXPERT_REASONS: dict[str, str] = {
    "S4A-2026-017": (
        "Possible hyväkuntoinen / physical-fitness reading versus clinical "
        "well-enough for cancer treatment. Not a wording-style preference."
    ),
    "S4A-2026-021": (
        "Frailty / hauraus is a healthcare concept with no final recorded "
        "human wording. Not a stylistic Finnish choice."
    ),
    "S4A-2026-025": (
        "Literal rendering of 'when the chest is at its best' raises a "
        "clinical-referent question about baseline respiratory status."
    ),
    "S4A-2026-026": (
        "Complications of liver disease versus extra problems is a clinical "
        "terminology/referent question, not a fluency preference."
    ),
    "S4A-2026-045": (
        "Chest infections versus rintakehän infektiot raises a clinical "
        "referent question (respiratory/lung infection versus chest wall)."
    ),
    "S4A-2026-049": (
        "Spiritual versus henkinen/hengellinen is a healthcare-domain "
        "referent question. T-016 records holistic care wording only."
    ),
}
EXISTING_HUMAN_DECISIONS: dict[str, str] = {
    "S4A-2026-001": (
        "Project Owner: less well -> terveydentila on heikentynyt. "
        "T-002: elinikää lyhentävät terveydentilat. Critics raised "
        "source-fidelity (current poorer state versus recorded "
        "deterioration). EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. "
        "Do not auto-retain or overwrite."
    ),
    "S4A-2026-004": (
        "Project Owner: less able to manage usual activities -> "
        "toimintakyky on heikentynyt."
    ),
    "S4A-2026-014": (
        "Project Owner: less able to manage usual activities -> "
        "toimintakyky on heikentynyt."
    ),
    "S4A-2026-017": (
        "Project Owner: not well enough for cancer treatment -> "
        "ei ole riittävän hyväkuntoinen syöpähoitoon. Critic B raised a "
        "possible hyväkuntoinen / physical-fitness ambiguity. "
        "EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. Do not decide."
    ),
    "S4A-2026-021": (
        "NO_FINAL_RECORDED_HUMAN_WORDING_DECISION. Frailty/hauraus was "
        "discussed before G1; no final recorded human term is preserved."
    ),
    "S4A-2026-035": "T-013 Project Owner: breathing machine -> hengityskone.",
    "S4A-2026-042": (
        "Project Owner: less well -> terveydentila on heikentynyt. "
        "T-002: elinikää lyhentävät terveydentilat. Critics raised "
        "source-fidelity (current poorer state versus recorded "
        "deterioration). EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. "
        "Do not auto-retain or overwrite."
    ),
    "S4A-2026-049": (
        "T-016 Sami / domain expert: holistic care -> kokonaisvaltainen hoito. "
        "This records the holistic-care term only; it does not decide the "
        "spiritual/henkinen question."
    ),
}
PRIORITY_HIGHLIGHTS = frozenset({"S4A-2026-025", "S4A-2026-045"})
HUMAN_DECISION_BLOCK = (
    "HUMAN DECISION (human adjudicator only; leave blank in this package)\n\n"
    + "\n".join(f"[ ] {option}" for option in DISPOSITION_OPTIONS)
    + """

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:
"""
)


@dataclass(frozen=True)
class PacketUnit:
    unit_id: str
    review_tier: ReviewTier
    source_text_en: str
    source_text_sha256: str
    current_candidate_fi: str
    back_translation_en: str
    combined_review_priority: str
    finding_status: str
    critic_a_verdict: str
    critic_a_severity: str
    critic_a_categories: tuple[str, ...]
    critic_a_rationale: str
    critic_a_proposed_fi: str
    critic_b_verdict: str
    critic_b_severity: str
    critic_b_categories: tuple[str, ...]
    critic_b_rationale: str
    critic_b_proposed_fi: str
    existing_human_decision: str
    domain_expert_review_recommended: bool
    domain_expert_reason: str
    source_authority_status: str
    source_authority_publication_blocking: bool
    source_authority_note: str
    frailty_human_wording_status: str
    human_decision_conflict: str


def input_hash_map(root: Path) -> dict[str, str]:
    relatives = {
        **EXPECTED_HASHES,
        COMBINED_RELATIVE: COMBINED_SHA256,
    }
    return {relative: sha256_file(root / relative) for relative in relatives}


def review_tier_for(a_severity: str, b_severity: str) -> ReviewTier:
    if a_severity in MEDIUM_PLUS or b_severity in MEDIUM_PLUS:
        return "TIER_1"
    if a_severity == "LOW" or b_severity == "LOW":
        return "TIER_2"
    return "TIER_3"


def categories_of(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ArtifactValidationError("critic categories must be a list of strings")
    return tuple(value)


def packet_unit_from_combined(row: dict[str, Any]) -> PacketUnit:
    unit_id = str(row["unit_id"])
    a_severity = str(row["critic_a_severity"])
    b_severity = str(row["critic_b_severity"])
    return PacketUnit(
        unit_id=unit_id,
        review_tier=review_tier_for(a_severity, b_severity),
        source_text_en=str(row["source_text_en"]),
        source_text_sha256=str(row["source_text_sha256"]),
        current_candidate_fi=str(row["candidate_fi"]),
        back_translation_en=str(row["back_translation_en"]),
        combined_review_priority=str(row["combined_review_priority"]),
        finding_status=str(row["finding_status"]),
        critic_a_verdict=str(row["critic_a_verdict"]),
        critic_a_severity=a_severity,
        critic_a_categories=categories_of(row["critic_a_categories"]),
        critic_a_rationale=str(row["critic_a_rationale"]),
        critic_a_proposed_fi=str(row["critic_a_proposed_fi"]),
        critic_b_verdict=str(row["critic_b_verdict"]),
        critic_b_severity=b_severity,
        critic_b_categories=categories_of(row["critic_b_categories"]),
        critic_b_rationale=str(row["critic_b_rationale"]),
        critic_b_proposed_fi=str(row["critic_b_proposed_fi"]),
        existing_human_decision=EXISTING_HUMAN_DECISIONS.get(unit_id, ""),
        domain_expert_review_recommended=unit_id in DOMAIN_EXPERT_REASONS,
        domain_expert_reason=DOMAIN_EXPERT_REASONS.get(unit_id, ""),
        source_authority_status=str(row["source_authority_status"]),
        source_authority_publication_blocking=bool(
            row["source_authority_publication_blocking"]
        ),
        source_authority_note=str(row["source_authority_note"]),
        frailty_human_wording_status=str(row["frailty_human_wording_status"]),
        human_decision_conflict=str(row["human_decision_conflict"]),
    )


def load_packet_units(root: Path) -> list[PacketUnit]:
    combined = load_jsonl(root / COMBINED_RELATIVE)
    if len(combined) != EXPECTED_COUNT:
        raise ArtifactValidationError(
            f"combined findings count is {len(combined)}, expected {EXPECTED_COUNT}"
        )
    return [packet_unit_from_combined(row) for row in combined]


def ids_of(units: list[PacketUnit]) -> list[str]:
    return [unit.unit_id for unit in units]


def tier_ids(units: list[PacketUnit], tier: ReviewTier) -> tuple[str, ...]:
    return tuple(unit.unit_id for unit in units if unit.review_tier == tier)


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def fence(text: str) -> str:
    return f"```\n{text}\n```"


def critic_lines(
    label: str,
    verdict: str,
    severity: str,
    categories: tuple[str, ...],
    rationale: str,
    proposed_fi: str,
) -> str:
    if verdict == "OK" and severity == "NONE":
        return (
            f"**{label}:** no issue recorded (OK / NONE). Absence of a critic "
            "finding is not acceptance."
        )
    joined = ", ".join(categories) if categories else "uncategorised"
    lines = [
        f"**{label}:** ISSUE · {severity} · {joined}",
        rationale,
    ]
    if proposed_fi:
        lines.append("Proposed Finnish (review evidence only; not applied):")
        lines.append(fence(proposed_fi))
    return "\n".join(lines)


def source_authority_lines(unit: PacketUnit) -> str:
    blocking = "yes" if unit.source_authority_publication_blocking else "no"
    lines = [
        f"**Source-authority status:** {unit.source_authority_status}",
        f"**Publication-blocking:** {blocking}",
    ]
    if unit.source_authority_note:
        lines.append(unit.source_authority_note)
    if unit.unit_id in SOURCE_AUTHORITY_BLOCKERS:
        lines.append(
            "The translation reviewer may review Finnish wording but must not "
            "resolve the source-authority question."
        )
    return "\n".join(lines)


def unit_banner(unit: PacketUnit) -> str:
    flags: list[str] = []
    if unit.unit_id in PRIORITY_HIGHLIGHTS:
        if unit.unit_id == "S4A-2026-025":
            flags.append(
                "PRIORITY HIGHLIGHT: Critic A HIGH and Critic B HIGH. "
                "Literal Finnish rendering of 'when the chest is at its best'."
            )
        else:
            flags.append(
                "PRIORITY HIGHLIGHT: Critic A BLOCKER and Critic B HIGH. "
                "Literal Finnish rendering of 'chest infections'."
            )
    if unit.human_decision_conflict:
        flags.append(
            "EXISTING HUMAN DECISION CONFLICT: present both the earlier human "
            "decision and the critic evidence. Do not overwrite or automatically "
            "retain the old decision."
        )
    if unit.unit_id == FRAILTY_ID:
        flags.append(
            "Frailty/hauraus: no final recorded human wording decision. "
            "Preserve that fact. Do not invent a term."
        )
    if unit.unit_id in SOURCE_AUTHORITY_BLOCKERS:
        flags.append(
            "SOURCE AUTHORITY — SEPARATE TRACK. Publication-blocking. "
            "Not insertable. Finnish wording review does not resolve authority."
        )
    if not flags:
        return ""
    return "\n".join(f"> {line}" for line in flags) + "\n\n"


def packet_unit_section(unit: PacketUnit) -> str:
    existing = unit.existing_human_decision or "None recorded for this unit."
    expert = yes_no(unit.domain_expert_review_recommended)
    if unit.domain_expert_reason:
        expert = f"{expert}. {unit.domain_expert_reason}"
    return "\n".join(
        [
            f"## {unit.unit_id}",
            "",
            unit_banner(unit) + f"- **Review tier:** {unit.review_tier}",
            f"- **Finding status:** {unit.finding_status}",
            f"- **Combined review priority:** {unit.combined_review_priority}",
            f"- **source_text_sha256:** `{unit.source_text_sha256}`",
            f"- **Preparation model/run:** {ACTUAL_MODEL} / {G5_RUN_ID}",
            "",
            "**Exact English source**",
            fence(unit.source_text_en),
            "",
            "**Current Finnish G2 candidate**",
            fence(unit.current_candidate_fi),
            "",
            "**Blind back-translation**",
            fence(unit.back_translation_en),
            "",
            critic_lines(
                "Critic A",
                unit.critic_a_verdict,
                unit.critic_a_severity,
                unit.critic_a_categories,
                unit.critic_a_rationale,
                unit.critic_a_proposed_fi,
            ),
            "",
            critic_lines(
                "Critic B",
                unit.critic_b_verdict,
                unit.critic_b_severity,
                unit.critic_b_categories,
                unit.critic_b_rationale,
                unit.critic_b_proposed_fi,
            ),
            "",
            f"**Existing human decision:** {existing}",
            f"**Domain expert review recommended:** {expert}",
            source_authority_lines(unit),
            "",
            HUMAN_DECISION_BLOCK,
        ]
    )


def packet_markdown(units: list[PacketUnit]) -> str:
    tier1 = ", ".join(f"`{unit_id}`" for unit_id in tier_ids(units, "TIER_1"))
    tier2 = ", ".join(f"`{unit_id}`" for unit_id in tier_ids(units, "TIER_2"))
    tier3 = ", ".join(f"`{unit_id}`" for unit_id in tier_ids(units, "TIER_3"))
    expert = ", ".join(f"`{unit_id}`" for unit_id in DOMAIN_EXPERT_REASONS)
    conflicts = ", ".join(f"`{unit_id}`" for unit_id in HUMAN_DECISION_CONFLICTS)
    sections = "\n".join(packet_unit_section(unit) for unit in units)
    return f"""# SPICT-4ALL FI — G5 human review packet

Work package: **{G5_WORK_PACKAGE}**
Run: **{G5_RUN_ID}**
Role: **{G5_ROLE}**
Preparation model: **{ACTUAL_MODEL}**
Coverage: **{EXPECTED_COUNT}/{EXPECTED_COUNT}**
Status: **{G5_STATUS}**

This package prepares decision material. It is not human adjudication, not
human approval, and not clinical validation. No option below is pre-checked.
No Finnish G2 candidate was changed. No G3 back-translation was changed. No
G4 critic output was changed. Source-authority conflicts remain unresolved.

## Human authority

Every one of the {EXPECTED_COUNT} units requires an explicit human disposition
at G5. Do not interpret absence of a critic finding as acceptance. Do not treat
AI agreement as acceptance. Do not mark anything HUMAN_APPROVED in this
preparation package.

A reviewer may inspect critic-clean units as a batch, but the resulting
evidence must still create an explicit disposition record for each unit.

## Review tiers

- **Tier 1 — priority human review** ({len(EXPECTED_TIER_1)}): {tier1}
- **Tier 2 — low-severity review** ({len(EXPECTED_TIER_2)}): {tier2}
- **Tier 3 — no-critic-issue review** ({EXPECTED_COUNT - len(EXPECTED_TIER_1) - len(EXPECTED_TIER_2)}): {tier3}

Highlight especially `{next(iter(sorted(PRIORITY_HIGHLIGHTS)))}` and
`S4A-2026-045`.

## Existing human-decision conflicts

{conflicts}

Present both the earlier Project Owner wording and the critic evidence.
Do not overwrite or automatically retain the old decision.

`{FRAILTY_ID}` has no final recorded human wording for frailty/hauraus.
Preserve that fact.

## Domain-expert review recommended

Recommended IDs: {expert}

This field is true only where there is a genuine clinical / healthcare
terminology / referent question. This list itself is not clinical review.

## Source authority — separate track

- `{TITLE_ID}`: UNRESOLVED, publication-blocking, not insertable.
- `{REQUIREMENT_ID}`: NONCANONICAL, canonical omission unresolved,
  publication-blocking.

The human translation reviewer may review Finnish wording for these units,
but must not resolve the source-authority question.

## Units in canonical order

{sections}
"""


def priority_markdown(units: list[PacketUnit]) -> str:
    selected = [unit for unit in units if unit.review_tier == "TIER_1"]
    blocks: list[str] = []
    for unit in selected:
        alternatives: list[str] = []
        if unit.critic_a_proposed_fi:
            alternatives.append("Critic A proposed Finnish (not authoritative):")
            alternatives.append(fence(unit.critic_a_proposed_fi))
        if unit.critic_b_proposed_fi:
            alternatives.append("Critic B proposed Finnish (not authoritative):")
            alternatives.append(fence(unit.critic_b_proposed_fi))
        if not alternatives:
            alternatives.append("No alternative Finnish wording was proposed.")
        existing = unit.existing_human_decision or "None recorded."
        blocks.append(
            "\n".join(
                [
                    f"## {unit.unit_id}",
                    "",
                    unit_banner(unit)
                    + f"- **Combined review priority:** {unit.combined_review_priority}",
                    f"- **Finding status:** {unit.finding_status}",
                    f"- **Critic A:** {unit.critic_a_verdict} / {unit.critic_a_severity}",
                    f"- **Critic B:** {unit.critic_b_verdict} / {unit.critic_b_severity}",
                    "",
                    "**Exact English**",
                    fence(unit.source_text_en),
                    "",
                    "**Current Finnish**",
                    fence(unit.current_candidate_fi),
                    "",
                    critic_lines(
                        "Critic A",
                        unit.critic_a_verdict,
                        unit.critic_a_severity,
                        unit.critic_a_categories,
                        unit.critic_a_rationale,
                        "",
                    ),
                    "",
                    critic_lines(
                        "Critic B",
                        unit.critic_b_verdict,
                        unit.critic_b_severity,
                        unit.critic_b_categories,
                        unit.critic_b_rationale,
                        "",
                    ),
                    "",
                    f"**Previous human decision:** {existing}",
                    "",
                    "**Alternative Finnish wording proposed by critics**",
                    "\n".join(alternatives),
                    "",
                    "No option is recommended as authoritative.",
                ]
            )
        )
    body = "\n\n".join(blocks)
    return f"""# SPICT-4ALL FI — G5 priority review (Tier 1)

Work package: **{G5_WORK_PACKAGE}**
Run: **{G5_RUN_ID}**
Units: **{len(EXPECTED_TIER_1)}**

This document contains only the Tier-1 units. It does not decide Finnish
wording and does not recommend one critic alternative as authoritative.

Especially:

- `S4A-2026-025` — Critic A HIGH, Critic B HIGH
- `S4A-2026-045` — Critic A BLOCKER, Critic B HIGH

{body}
"""


def clean_units_markdown(units: list[PacketUnit]) -> str:
    selected = [unit for unit in units if unit.review_tier == "TIER_3"]
    rows = [
        "\n".join(
            [
                f"## {unit.unit_id}",
                "",
                "**English**",
                fence(unit.source_text_en),
                "",
                "**Current Finnish**",
                fence(unit.current_candidate_fi),
            ]
        )
        for unit in selected
    ]
    ids = ", ".join(f"`{unit.unit_id}`" for unit in selected)
    body = "\n\n".join(rows)
    return f"""# SPICT-4ALL FI — G5 critic-clean units (Tier 3)

Work package: **{G5_WORK_PACKAGE}**
Run: **{G5_RUN_ID}**
Units: **{len(selected)}**

These units had no critic ISSUE from Critic A or Critic B. That is not
acceptance. Each unit still requires an explicit human disposition record.
A reviewer may inspect this list efficiently and then record a disposition
for every listed unit.

`{REQUIREMENT_ID}` is critic-clean for Finnish review evidence, but remains
NONCANONICAL, publication-blocking, and not insertable. Source authority is
a separate track.

Canonical order: {ids}

{body}
"""


def dispositions_tsv(units: list[PacketUnit]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(TSV_COLUMNS),
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for unit in units:
        writer.writerow(
            {
                "unit_id": unit.unit_id,
                "review_tier": unit.review_tier,
                "source_text_en": unit.source_text_en,
                "current_candidate_fi": unit.current_candidate_fi,
                "combined_review_priority": unit.combined_review_priority,
                "finding_status": unit.finding_status,
                "existing_human_decision": unit.existing_human_decision,
                "domain_expert_review_recommended": (
                    "true" if unit.domain_expert_review_recommended else "false"
                ),
                "source_authority_status": unit.source_authority_status,
                "human_disposition": "",
                "final_finnish": "",
                "reviewer": "",
                "reviewer_role": "",
                "decision_rationale": "",
                "decision_date": "",
            }
        )
    return buffer.getvalue()


def summary_payload(
    units: list[PacketUnit],
    root: Path,
    created_at_utc: str,
) -> dict[str, Any]:
    hashes = input_hash_map(root)
    hashes.update(
        {
            HUMAN_DECISIONS_RELATIVE: sha256_file(root / HUMAN_DECISIONS_RELATIVE),
            T1_2_REPORT_RELATIVE: sha256_file(root / T1_2_REPORT_RELATIVE),
            SOURCE_UNITS_RELATIVE: sha256_file(root / SOURCE_UNITS_RELATIVE),
            SOURCE_REQUIREMENTS_RELATIVE: sha256_file(
                root / SOURCE_REQUIREMENTS_RELATIVE
            ),
        }
    )
    return {
        "run_id": G5_RUN_ID,
        "work_package": G5_WORK_PACKAGE,
        "role": G5_ROLE,
        "actual_model": ACTUAL_MODEL,
        "created_at_utc": created_at_utc,
        "status": G5_STATUS,
        "total_units": EXPECTED_COUNT,
        "tier_1_count": len(EXPECTED_TIER_1),
        "tier_1_ids": list(tier_ids(units, "TIER_1")),
        "tier_2_count": len(EXPECTED_TIER_2),
        "tier_2_ids": list(tier_ids(units, "TIER_2")),
        "tier_3_count": EXPECTED_COUNT - len(EXPECTED_TIER_1) - len(EXPECTED_TIER_2),
        "tier_3_ids": list(tier_ids(units, "TIER_3")),
        "source_authority_blocker_ids": [TITLE_ID, REQUIREMENT_ID],
        "existing_human_decision_conflict_ids": [
            unit.unit_id for unit in units if unit.human_decision_conflict
        ],
        "domain_expert_review_recommended_ids": [
            unit.unit_id
            for unit in units
            if unit.domain_expert_review_recommended
        ],
        "input_hashes": hashes,
        "preparation_provenance": {
            "model": ACTUAL_MODEL,
            "run_id": G5_RUN_ID,
            "work_package": G5_WORK_PACKAGE,
            "role": G5_ROLE,
        },
        "human_adjudication_performed": False,
        "human_disposition_prepopulated": False,
        "final_finnish_prepopulated": False,
        "g2_finnish_unchanged": True,
        "g3_unchanged": True,
        "g4_unchanged": True,
        "source_authority_resolved": False,
        "g5_gate_passed": False,
        "g5_audit_zip_created": False,
        "g6_started": False,
        "document_generation_started": False,
        "clinical_validation_claimed": False,
        "readme_not_modified_by_this_package": True,
    }


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_required_artifacts(
    units: list[PacketUnit],
    root: Path,
    created_at_utc: str,
) -> dict[str, str]:
    return {
        "G5_HUMAN_REVIEW_PACKET.md": packet_markdown(units),
        "human_dispositions.tsv": dispositions_tsv(units),
        "G5_PRIORITY_REVIEW.md": priority_markdown(units),
        "G5_CLEAN_UNITS.md": clean_units_markdown(units),
        "G5_REVIEW_SUMMARY.json": encode_json(
            summary_payload(units, root, created_at_utc)
        ),
    }


def run_metadata_payload(
    root: Path,
    created_at_utc: str,
) -> dict[str, Any]:
    metadata = build_run_metadata(
        G5_RUN_ID,
        f"{G5_ROLE} (actual model: {ACTUAL_MODEL})",
        [
            root / COMBINED_RELATIVE,
            root / CRITIC_A_RELATIVE,
            root / CRITIC_B_RELATIVE,
            root / REVIEW_INPUT_RELATIVE,
            root / G2_CANDIDATES_RELATIVE,
            root / G3_BACK_RELATIVE,
            root / HUMAN_DECISIONS_RELATIVE,
            root / T1_2_REPORT_RELATIVE,
        ],
        created_at_utc=created_at_utc,
    )
    metadata.update(
        {
            "work_package": G5_WORK_PACKAGE,
            "actual_model": ACTUAL_MODEL,
            "g5_status": G5_STATUS,
            "human_adjudication_performed": False,
            "finnish_revised": False,
            "g2_changed": False,
            "g3_changed": False,
            "g4_changed": False,
            "source_authority_resolved": False,
            "g5_gate_passed": False,
            "g5_audit_zip_created": False,
            "g6_started": False,
            "clinical_validation_claimed": False,
        }
    )
    return metadata


def document_generation_files(root: Path) -> list[str]:
    directory = root / "work/final"
    if not directory.is_dir():
        return []
    found: list[str] = []
    for path in directory.rglob("*"):
        if path.is_file() and path.name != ".gitkeep":
            found.append(path.relative_to(root).as_posix())
    return found


def g5_audit_zip_files(root: Path) -> list[str]:
    audit = root / "deliverables/audit"
    if not audit.is_dir():
        return []
    found: list[str] = []
    for path in audit.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.upper()
        if "G5" in name or "G6" in name:
            found.append(path.relative_to(root).as_posix())
    return found


def load_dispositions(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != list(TSV_COLUMNS):
            raise ArtifactValidationError(
                f"human_dispositions.tsv columns are {reader.fieldnames}"
            )
        return list(reader)


def source_index(root: Path) -> dict[str, tuple[str, str]]:
    expected: dict[str, tuple[str, str]] = {}
    for row in load_jsonl(root / SOURCE_UNITS_RELATIVE):
        expected[str(row["unit_id"])] = (
            str(row["source_text_en"]),
            str(row["source_text_sha256"]),
        )
    for row in load_jsonl(root / SOURCE_REQUIREMENTS_RELATIVE):
        if row.get("translation_evidence_required") is True:
            expected[str(row["requirement_id"])] = (
                str(row["exact_source_text_en"]),
                str(row["exact_text_sha256"]),
            )
    return expected


def artifact_claim_failures(texts: dict[str, str]) -> list[str]:
    failures: list[str] = []
    joined = "\n".join(texts.values())
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in joined:
            failures.append(f"G5 preparation claims {phrase!r}")
    if CHECKED_BOX.search(joined):
        failures.append("G5 preparation pre-checks a human decision option")
    return failures


def g5_run_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for relative, expected in {**EXPECTED_HASHES, COMBINED_RELATIVE: COMBINED_SHA256}.items():
        if sha256_file(root / relative) != expected:
            failures.append(f"frozen input hash mismatch: {relative}")
    run_dir = root / G5_RUN_DIR
    for name in REQUIRED_OUTPUTS:
        if not (run_dir / name).is_file():
            failures.append(f"missing G5 output: {name}")
            return failures
    units = load_packet_units(root)
    ids = ids_of(units)
    if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT:
        failures.append("G5 unit coverage is not 54 unique IDs")
    g2 = load_jsonl(root / G2_CANDIDATES_RELATIVE)
    back = load_jsonl(root / G3_BACK_RELATIVE)
    if ids != [str(row["unit_id"]) for row in g2]:
        failures.append("G5 unit order differs from G2 canonical order")
    if ids != [str(row["unit_id"]) for row in back]:
        failures.append("G5 unit order differs from G3")
    if tuple(tier_ids(units, "TIER_1")) != EXPECTED_TIER_1:
        failures.append(f"Tier 1 IDs are {tier_ids(units, 'TIER_1')}")
    if tuple(tier_ids(units, "TIER_2")) != EXPECTED_TIER_2:
        failures.append(f"Tier 2 IDs are {tier_ids(units, 'TIER_2')}")
    sources = source_index(root)
    g2_map = {
        str(row["unit_id"]): str(row["candidate_fi"]) for row in g2
    }
    back_map = {
        str(row["unit_id"]): str(row["back_translation_en"]) for row in back
    }
    for unit in units:
        source = sources.get(unit.unit_id)
        if source is None:
            failures.append(f"{unit.unit_id}: missing from frozen source index")
            continue
        english, digest = source
        if unit.source_text_en != english:
            failures.append(f"{unit.unit_id}: English differs from frozen source")
        if unit.source_text_sha256 != digest:
            failures.append(f"{unit.unit_id}: source hash differs from frozen source")
        if unit.current_candidate_fi != g2_map[unit.unit_id]:
            failures.append(f"{unit.unit_id}: G2 Finnish changed")
        if unit.back_translation_en != back_map[unit.unit_id]:
            failures.append(f"{unit.unit_id}: G3 back-translation changed")
        if unit.unit_id == TITLE_ID and unit.source_authority_status != "UNRESOLVED":
            failures.append("title source authority was resolved")
        if (
            unit.unit_id == REQUIREMENT_ID
            and unit.source_authority_status != "NONCANONICAL"
        ):
            failures.append("requirement source authority was resolved")
        if unit.unit_id == FRAILTY_ID and not unit.frailty_human_wording_status:
            failures.append("frailty missing no-final-wording status")
        expected_expert = unit.unit_id in DOMAIN_EXPERT_REASONS
        if unit.domain_expert_review_recommended is not expected_expert:
            failures.append(f"{unit.unit_id}: domain-expert flag mismatch")
    try:
        rows = load_dispositions(run_dir / "human_dispositions.tsv")
    except ArtifactValidationError as exc:
        failures.append(str(exc))
        return failures
    if [row["unit_id"] for row in rows] != ids:
        failures.append("human_dispositions.tsv order is not canonical")
    if len(rows) != EXPECTED_COUNT:
        failures.append(f"human_dispositions.tsv has {len(rows)} data rows")
    for row in rows:
        for field in BLANK_HUMAN_FIELDS:
            if row.get(field, "") != "":
                failures.append(f"{row['unit_id']}: {field} is pre-populated")
    created_at = json.loads(
        (run_dir / "G5_REVIEW_SUMMARY.json").read_text(encoding="utf-8")
    )["created_at_utc"]
    expected_texts = render_required_artifacts(units, root, str(created_at))
    for name, expected in expected_texts.items():
        actual = (run_dir / name).read_text(encoding="utf-8")
        if actual != expected:
            failures.append(f"{name} is not the deterministic G5 preparation output")
    failures.extend(artifact_claim_failures(expected_texts))
    for path in document_generation_files(root):
        failures.append(f"document-generation file present: {path}")
    for path in g5_audit_zip_files(root):
        failures.append(f"G5/G6 audit artifact present: {path}")
    summary = json.loads((run_dir / "G5_REVIEW_SUMMARY.json").read_text(encoding="utf-8"))
    if summary.get("human_adjudication_performed") is not False:
        failures.append("summary claims human adjudication")
    if summary.get("g5_gate_passed") is not False:
        failures.append("summary claims G5 gate passed")
    if summary.get("g6_started") is not False:
        failures.append("summary claims G6 started")
    if summary.get("source_authority_resolved") is not False:
        failures.append("summary claims source authority resolved")
    if summary.get("clinical_validation_claimed") is not False:
        failures.append("summary claims clinical validation")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if "| **G5** | Human adjudication and final source reconciliation | **IN PROGRESS** |" not in readme:
        failures.append("README G5 status is not IN PROGRESS")
    if "| **G4** | Independent critics and adversarial review | **PASS** |" not in readme:
        failures.append("README G4 status is not PASS")
    if "| **G6** | Target-user testing and external review | **PASS** |" in readme:
        failures.append("README claims G6 PASS")
    return failures
