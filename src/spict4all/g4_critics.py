"""Mechanical G4 independent-critic consolidation checks.

These checks do not adjudicate Finnish wording, do not revise G2 candidates,
and carry no human-approval or clinical-validation authority.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from .errors import ArtifactValidationError
from .hashing import sha256_bytes
from .jsonl import load_jsonl

G4_RUN_ID = "G4-20260908-001"
G4_ROLE = "G4 critic consolidation"
WORK_PACKAGE = "WP-G4-CONSOLIDATION-AUDIT-001"
G4_RUN_DIR = Path("work") / "critics" / G4_RUN_ID
G4_STATUS = "INDEPENDENT_CRITICS_COMPLETE_AWAITING_G5"
EXPECTED_COUNT = 54
TITLE_ID = "S4A-2026-000"
REQUIREMENT_ID = "S4A-REQ-2026-001"
FRAILTY_ID = "S4A-2026-021"

REVIEW_INPUT_RELATIVE = f"{G4_RUN_DIR.as_posix()}/review_input.jsonl"
CRITIC_A_RELATIVE = f"{G4_RUN_DIR.as_posix()}/critic-a.jsonl"
CRITIC_B_RELATIVE = f"{G4_RUN_DIR.as_posix()}/critic-b.jsonl"
COMBINED_RELATIVE = f"{G4_RUN_DIR.as_posix()}/combined_findings.jsonl"
REPORT_RELATIVE = f"{G4_RUN_DIR.as_posix()}/G4_REVIEW_REPORT.md"
G2_CANDIDATES_RELATIVE = "work/synthesis/G2-20260908-001/candidates.jsonl"
G3_BACK_RELATIVE = "work/backtranslation/G3-20260908-001/back_translation.jsonl"

CRITIC_A_ACTUAL_MODEL = "NOT_INDEPENDENTLY_RECORDED"
CRITIC_B_ACTUAL_MODEL = "Cursor Grok 4.6"
G2_ACTUAL_MODEL = "Cursor Grok 4.6"
CONFIGURED_ADVERSARIAL_MODEL = "Cursor Grok 4.6 Medium"
CRITIC_A_PROVENANCE_LIMITATION = (
    "No operator-stated actual model for Critic A is recorded in "
    f"{WORK_PACKAGE}. This package does not infer Critic A's model from "
    "config/model_roles.yaml or from critic prompt files."
)
CRITIC_B_PROVENANCE_BASIS = (
    "Recorded from the operator Critic B review prompt for G4-20260908-001 "
    "(ACTUAL MODEL: Cursor Grok 4.6). No independent API request log is packaged."
)
SAME_FAMILY_LIMITATION = (
    "Critic B and G2 synthesis both used Cursor Grok 4.6. This same-family "
    "limitation does not invalidate Critic B. Independent cross-family review "
    "evidence cannot be claimed from Critic A in this package because Critic A's "
    "actual model is not independently recorded."
)
INDEPENDENCE_STATEMENT = (
    "Critic A and Critic B were run independently. Neither critic saw the other "
    "critic's findings. This consolidation does not alter either critic output, "
    "does not reconcile proposed Finnish wording into a new candidate, and is "
    "not human adjudication."
)

Severity = Literal["NONE", "LOW", "MEDIUM", "HIGH", "BLOCKER"]
FindingStatus = Literal[
    "NO_CRITIC_ISSUE",
    "CORROBORATED",
    "CRITIC_A_ONLY",
    "CRITIC_B_ONLY",
]

SEVERITY_RANK: dict[str, int] = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "BLOCKER": 4,
}
VERDICTS = frozenset({"OK", "ISSUE"})
FINDING_STATUSES = frozenset(
    {"NO_CRITIC_ISSUE", "CORROBORATED", "CRITIC_A_ONLY", "CRITIC_B_ONLY"}
)
REQUIRED_CRITIC_FIELDS = (
    "unit_id",
    "verdict",
    "severity",
    "categories",
    "rationale",
    "proposed_fi_if_needed",
    "human_review_needed",
)
COMBINED_KEYS = (
    "unit_id",
    "source_text_en",
    "source_text_sha256",
    "candidate_fi",
    "back_translation_en",
    "critic_a_verdict",
    "critic_a_severity",
    "critic_a_categories",
    "critic_a_rationale",
    "critic_a_proposed_fi",
    "critic_b_verdict",
    "critic_b_severity",
    "critic_b_categories",
    "critic_b_rationale",
    "critic_b_proposed_fi",
    "finding_status",
    "combined_review_priority",
    "requires_G5_human_disposition",
    "human_decision_conflict",
    "human_decision_conflict_detail",
    "source_authority_status",
    "source_authority_publication_blocking",
    "source_authority_note",
    "frailty_human_wording_status",
)
EXPECTED_HASHES: dict[str, str] = {
    CRITIC_A_RELATIVE: (
        "e527f6b999d3e06aeaa883de26264a9b29dc3e394c2f9f8d5437797dbba72daf"
    ),
    CRITIC_B_RELATIVE: (
        "ba0bb2822a4cb711d51388e025deb73ea25980f22a435e81e7bc9864d1ace52e"
    ),
    G2_CANDIDATES_RELATIVE: (
        "76462191d3ad2a83c878982a1460443f322437e547b747f6267f4a29d887c619"
    ),
    G3_BACK_RELATIVE: (
        "e674a7f0a69ed05c554eaade38e4dbd8025c1f34df0499a8fc4cc9a15c99f00f"
    ),
    REVIEW_INPUT_RELATIVE: (
        "5a07c32c9680032eaa69f268b8160c3460f1b2ebdf7c9a6b547688b81d4f526f"
    ),
}
EXPECTED_A_SEVERITY = {"NONE": 47, "LOW": 3, "MEDIUM": 2, "HIGH": 1, "BLOCKER": 1}
EXPECTED_B_SEVERITY = {"NONE": 33, "LOW": 12, "MEDIUM": 7, "HIGH": 2, "BLOCKER": 0}
EXPECTED_A_ISSUE = 7
EXPECTED_B_ISSUE = 21
EXPECTED_CORROBORATED = (
    "S4A-2026-001",
    "S4A-2026-009",
    "S4A-2026-025",
    "S4A-2026-026",
    "S4A-2026-042",
    "S4A-2026-045",
    "S4A-2026-049",
)
EXPECTED_B_ONLY = (
    "S4A-2026-000",
    "S4A-2026-003",
    "S4A-2026-004",
    "S4A-2026-008",
    "S4A-2026-014",
    "S4A-2026-017",
    "S4A-2026-018",
    "S4A-2026-021",
    "S4A-2026-033",
    "S4A-2026-034",
    "S4A-2026-036",
    "S4A-2026-040",
    "S4A-2026-043",
    "S4A-2026-047",
)
EXPECTED_B_ONLY_MEDIUM = (
    "S4A-2026-008",
    "S4A-2026-017",
    "S4A-2026-021",
    "S4A-2026-036",
)
HUMAN_DECISION_CONFLICTS: dict[str, tuple[str, str]] = {
    "S4A-2026-001": ("less well", "terveydentila on heikentynyt"),
    "S4A-2026-042": ("less well", "terveydentila on heikentynyt"),
    "S4A-2026-017": (
        "not well enough for cancer treatment",
        "ei ole riittävän hyväkuntoinen syöpähoitoon",
    ),
}
SOURCE_AUTHORITY_BLOCKERS = frozenset({TITLE_ID, REQUIREMENT_ID})
G5_ONLY_PREFIXES = ("work/final/", "work/human-review/")
MEDIUM_PLUS = frozenset({"MEDIUM", "HIGH", "BLOCKER"})


def load_jsonl_records(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ArtifactValidationError(f"JSONL record {line_number} is not an object")
        records.append(value)
    return records


def identity_failures(rows: list[dict[str, Any]], label: str) -> list[str]:
    failures: list[str] = []
    ids = [str(row.get("unit_id")) for row in rows]
    if len(ids) != EXPECTED_COUNT:
        failures.append(f"{label} count is {len(ids)}")
    if len(set(ids)) != len(ids):
        failures.append(f"{label} IDs are not unique")
    if TITLE_ID not in ids:
        failures.append(f"{label} missing {TITLE_ID}")
    if REQUIREMENT_ID not in ids:
        failures.append(f"{label} missing {REQUIREMENT_ID}")
    return failures


def ids_of(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["unit_id"]) for row in rows]


def issue_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["unit_id"]) for row in rows if str(row.get("verdict")) == "ISSUE"]


def severity_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("severity")) for row in rows)
    return {name: int(counts.get(name, 0)) for name in SEVERITY_RANK}


def max_severity(left: str, right: str) -> Severity:
    mapping: dict[str, Severity] = {
        "NONE": "NONE",
        "LOW": "LOW",
        "MEDIUM": "MEDIUM",
        "HIGH": "HIGH",
        "BLOCKER": "BLOCKER",
    }
    if left not in mapping or right not in mapping:
        raise ArtifactValidationError(f"unknown severity {left!r} or {right!r}")
    chosen = left if SEVERITY_RANK[left] >= SEVERITY_RANK[right] else right
    return mapping[chosen]


def critic_row_failures(rows: list[dict[str, Any]], label: str) -> list[str]:
    failures = identity_failures(rows, label)
    for index, row in enumerate(rows, 1):
        missing = [name for name in REQUIRED_CRITIC_FIELDS if name not in row]
        if missing:
            failures.append(f"{label} line {index}: missing fields {missing}")
            continue
        verdict = str(row["verdict"])
        severity = str(row["severity"])
        if verdict not in VERDICTS:
            failures.append(f"{label} line {index}: verdict {verdict!r}")
        if severity not in SEVERITY_RANK:
            failures.append(f"{label} line {index}: severity {severity!r}")
        if verdict == "OK" and severity != "NONE":
            failures.append(f"{label} line {index}: OK requires NONE")
        if verdict == "ISSUE" and severity == "NONE":
            failures.append(f"{label} line {index}: ISSUE requires non-NONE severity")
        if severity in MEDIUM_PLUS and row.get("human_review_needed") is not True:
            failures.append(f"{label} line {index}: MEDIUM+ requires human_review_needed")
        categories = row.get("categories")
        if not isinstance(categories, list) or any(
            not isinstance(item, str) for item in categories
        ):
            failures.append(f"{label} line {index}: categories must be a list of strings")
        proposed = row.get("proposed_fi_if_needed")
        if not isinstance(proposed, str):
            failures.append(f"{label} line {index}: proposed_fi_if_needed is not a string")
        elif verdict == "OK" and proposed != "":
            failures.append(f"{label} line {index}: OK proposed Finnish must be blank")
    return failures


def finding_status(a_issue: bool, b_issue: bool) -> FindingStatus:
    if a_issue and b_issue:
        return "CORROBORATED"
    if a_issue:
        return "CRITIC_A_ONLY"
    if b_issue:
        return "CRITIC_B_ONLY"
    return "NO_CRITIC_ISSUE"


def g2_source_map(
    candidates: list[dict[str, Any]],
) -> dict[str, tuple[str, str, str]]:
    mapping: dict[str, tuple[str, str, str]] = {}
    for row in candidates:
        unit_id = str(row["unit_id"])
        extensions = row.get("extensions")
        if not isinstance(extensions, dict):
            raise ArtifactValidationError(f"{unit_id}: G2 extensions missing")
        g2 = extensions.get("g2_synthesis")
        if not isinstance(g2, dict):
            raise ArtifactValidationError(f"{unit_id}: G2 synthesis extension missing")
        source = str(g2["exact_source_text_en"])
        sha = str(row["source_text_sha256"])
        finnish = str(row["candidate_fi"])
        if unit_id in mapping:
            raise ArtifactValidationError(f"duplicate G2 unit_id {unit_id}")
        mapping[unit_id] = (source, sha, finnish)
    return mapping


def later_gate_failures(root: Path, prefixes: tuple[str, ...]) -> list[str]:
    failures: list[str] = []
    for prefix in prefixes:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                failures.append(
                    f"later-gate file present: {path.relative_to(root).as_posix()}"
                )
    return failures


def source_authority_fields(unit_id: str, inclusion: str) -> dict[str, Any]:
    if unit_id == TITLE_ID:
        return {
            "source_authority_status": "UNRESOLVED",
            "source_authority_publication_blocking": True,
            "source_authority_note": (
                "Source-authority status remains UNRESOLVED. Not eligible for "
                "document insertion. Publication-blocking. Critic findings do "
                "not resolve this. Separate from critic severity."
            ),
        }
    if unit_id == REQUIREMENT_ID:
        return {
            "source_authority_status": "NONCANONICAL",
            "source_authority_publication_blocking": True,
            "source_authority_note": (
                "Remains NONCANONICAL. Canonical omission remains unresolved. "
                "Publication-blocking. Critic findings do not resolve this. "
                "Separate from critic severity."
            ),
        }
    return {
        "source_authority_status": inclusion,
        "source_authority_publication_blocking": False,
        "source_authority_note": "",
    }


def human_conflict_fields(unit_id: str, a_issue: bool, b_issue: bool) -> dict[str, str]:
    binding = HUMAN_DECISION_CONFLICTS.get(unit_id)
    if binding is None or not (a_issue or b_issue):
        return {
            "human_decision_conflict": "",
            "human_decision_conflict_detail": "",
        }
    concept, wording = binding
    return {
        "human_decision_conflict": (
            "EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5"
        ),
        "human_decision_conflict_detail": (
            f"Critic findings intersect the recorded Project Owner wording for "
            f"{concept!r} ({wording!r}). The human decision is not overridden "
            "and the critic findings are not suppressed."
        ),
    }


def requires_g5(
    status: FindingStatus,
    priority: str,
    unit_id: str,
    a_issue: bool,
    b_issue: bool,
) -> bool:
    if priority in MEDIUM_PLUS:
        return True
    if status == "CORROBORATED":
        return True
    if unit_id in SOURCE_AUTHORITY_BLOCKERS:
        return True
    if unit_id in HUMAN_DECISION_CONFLICTS and (a_issue or b_issue):
        return True
    return False


def consolidate_unit(
    review: dict[str, Any],
    critic_a: dict[str, Any],
    critic_b: dict[str, Any],
    g2: tuple[str, str, str],
    back_en: str,
) -> dict[str, Any]:
    unit_id = str(review["unit_id"])
    source_en = str(review["source_text_en"])
    source_sha = str(review["source_text_sha256"])
    candidate_fi = str(review["candidate_fi"])
    back = str(review["back_translation_en"])
    g2_source, g2_sha, g2_fi = g2
    if source_en != g2_source:
        raise ArtifactValidationError(f"{unit_id}: review English differs from G2 source")
    if source_sha != g2_sha:
        raise ArtifactValidationError(f"{unit_id}: review source SHA differs from G2")
    if candidate_fi != g2_fi:
        raise ArtifactValidationError(f"{unit_id}: review Finnish differs from G2 candidate")
    if back != back_en:
        raise ArtifactValidationError(
            f"{unit_id}: review back-translation differs from G3"
        )
    a_issue = str(critic_a["verdict"]) == "ISSUE"
    b_issue = str(critic_b["verdict"]) == "ISSUE"
    status = finding_status(a_issue, b_issue)
    priority = max_severity(str(critic_a["severity"]), str(critic_b["severity"]))
    inclusion = str(review.get("final_inclusion_status", ""))
    frailty = (
        "NO_FINAL_RECORDED_HUMAN_WORDING_DECISION" if unit_id == FRAILTY_ID else ""
    )
    row: dict[str, Any] = {
        "unit_id": unit_id,
        "source_text_en": source_en,
        "source_text_sha256": source_sha,
        "candidate_fi": candidate_fi,
        "back_translation_en": back,
        "critic_a_verdict": str(critic_a["verdict"]),
        "critic_a_severity": str(critic_a["severity"]),
        "critic_a_categories": list(critic_a["categories"]),
        "critic_a_rationale": str(critic_a["rationale"]),
        "critic_a_proposed_fi": str(critic_a["proposed_fi_if_needed"]),
        "critic_b_verdict": str(critic_b["verdict"]),
        "critic_b_severity": str(critic_b["severity"]),
        "critic_b_categories": list(critic_b["categories"]),
        "critic_b_rationale": str(critic_b["rationale"]),
        "critic_b_proposed_fi": str(critic_b["proposed_fi_if_needed"]),
        "finding_status": status,
        "combined_review_priority": priority,
        "requires_G5_human_disposition": requires_g5(
            status, priority, unit_id, a_issue, b_issue
        ),
        **human_conflict_fields(unit_id, a_issue, b_issue),
        **source_authority_fields(unit_id, inclusion),
        "frailty_human_wording_status": frailty,
    }
    return {key: row[key] for key in COMBINED_KEYS}


def encode_combined_row(row: dict[str, Any]) -> str:
    ordered = {key: row[key] for key in COMBINED_KEYS}
    return json.dumps(ordered, ensure_ascii=False) + "\n"


def build_combined_findings(
    review: list[dict[str, Any]],
    critic_a: list[dict[str, Any]],
    critic_b: list[dict[str, Any]],
    g2: list[dict[str, Any]],
    back: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failures: list[str] = []
    failures.extend(identity_failures(review, "review_input"))
    failures.extend(critic_row_failures(critic_a, "critic-a"))
    failures.extend(critic_row_failures(critic_b, "critic-b"))
    failures.extend(identity_failures(g2, "g2_candidates"))
    failures.extend(identity_failures(back, "g3_back_translation"))
    review_ids = ids_of(review)
    if review_ids != ids_of(critic_a):
        failures.append("critic-a unit_id order differs from review_input")
    if review_ids != ids_of(critic_b):
        failures.append("critic-b unit_id order differs from review_input")
    if review_ids != ids_of(g2):
        failures.append("G2 unit_id order differs from review_input")
    if review_ids != ids_of(back):
        failures.append("G3 unit_id order differs from review_input")
    if failures:
        raise ArtifactValidationError("G4 input validation failed: " + "; ".join(failures))
    g2_map = g2_source_map(g2)
    back_map = {str(row["unit_id"]): str(row["back_translation_en"]) for row in back}
    combined: list[dict[str, Any]] = []
    for index, item in enumerate(review):
        unit_id = str(item["unit_id"])
        combined.append(
            consolidate_unit(
                item,
                critic_a[index],
                critic_b[index],
                g2_map[unit_id],
                back_map[unit_id],
            )
        )
    return combined


def status_groups(combined: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {name: [] for name in FINDING_STATUSES}
    for row in combined:
        status = str(row["finding_status"])
        groups.setdefault(status, []).append(str(row["unit_id"]))
    return groups


def medium_plus_units(combined: list[dict[str, Any]]) -> list[str]:
    return [
        str(row["unit_id"])
        for row in combined
        if str(row["combined_review_priority"]) in MEDIUM_PLUS
        or str(row["critic_a_severity"]) in MEDIUM_PLUS
        or str(row["critic_b_severity"]) in MEDIUM_PLUS
    ]


def expected_cross_critic_failures(combined: list[dict[str, Any]]) -> list[str]:
    groups = status_groups(combined)
    failures: list[str] = []
    if tuple(groups.get("CORROBORATED", [])) != EXPECTED_CORROBORATED:
        failures.append(f"corroborated IDs are {groups.get('CORROBORATED')}")
    if groups.get("CRITIC_A_ONLY"):
        failures.append(f"critic-A-only IDs are {groups.get('CRITIC_A_ONLY')}")
    if tuple(groups.get("CRITIC_B_ONLY", [])) != EXPECTED_B_ONLY:
        failures.append(f"critic-B-only IDs are {groups.get('CRITIC_B_ONLY')}")
    b_only_medium = [
        str(row["unit_id"])
        for row in combined
        if row["finding_status"] == "CRITIC_B_ONLY"
        and str(row["critic_b_severity"]) == "MEDIUM"
    ]
    if tuple(b_only_medium) != EXPECTED_B_ONLY_MEDIUM:
        failures.append(f"critic-B-only MEDIUM IDs are {b_only_medium}")
    return failures


def verify_frozen_g4_bytes(named: dict[str, bytes]) -> None:
    for relative, expected in EXPECTED_HASHES.items():
        data = named.get(relative)
        if data is None:
            raise ArtifactValidationError(f"Required G4 artifact missing: {relative}")
        if sha256_bytes(data) != expected:
            raise ArtifactValidationError(
                f"Required G4 artifact hash mismatch: {relative}"
            )


def g4_run_failures(root: Path) -> list[str]:
    failures: list[str] = []
    named = {
        relative: (root / relative).read_bytes()
        for relative in EXPECTED_HASHES
        if (root / relative).is_file()
    }
    try:
        verify_frozen_g4_bytes(named)
    except ArtifactValidationError as exc:
        failures.append(str(exc))
        return failures
    review = load_jsonl(root / REVIEW_INPUT_RELATIVE)
    critic_a = load_jsonl(root / CRITIC_A_RELATIVE)
    critic_b = load_jsonl(root / CRITIC_B_RELATIVE)
    g2 = load_jsonl(root / G2_CANDIDATES_RELATIVE)
    back = load_jsonl(root / G3_BACK_RELATIVE)
    try:
        combined = build_combined_findings(review, critic_a, critic_b, g2, back)
    except ArtifactValidationError as exc:
        failures.append(str(exc))
        return failures
    if severity_counts(critic_a) != EXPECTED_A_SEVERITY:
        failures.append(f"critic-a severity {severity_counts(critic_a)}")
    if severity_counts(critic_b) != EXPECTED_B_SEVERITY:
        failures.append(f"critic-b severity {severity_counts(critic_b)}")
    if len(issue_ids(critic_a)) != EXPECTED_A_ISSUE:
        failures.append(f"critic-a ISSUE count is {len(issue_ids(critic_a))}")
    if len(issue_ids(critic_b)) != EXPECTED_B_ISSUE:
        failures.append(f"critic-b ISSUE count is {len(issue_ids(critic_b))}")
    failures.extend(expected_cross_critic_failures(combined))
    run_dir = root / G4_RUN_DIR
    for name in (
        "combined_findings.jsonl",
        "G4_REVIEW_REPORT.md",
        "run_metadata.json",
        "validation_results.json",
    ):
        if not (run_dir / name).is_file():
            failures.append(f"missing G4 metadata file: {name}")
            return failures
    written = load_jsonl(run_dir / "combined_findings.jsonl")
    expected_text = "".join(encode_combined_row(row) for row in combined)
    if (run_dir / "combined_findings.jsonl").read_text(encoding="utf-8") != expected_text:
        failures.append("combined_findings.jsonl is not the deterministic consolidation")
    if ids_of(written) != ids_of(review):
        failures.append("combined_findings unit_id order differs from review_input")
    failures.extend(later_gate_failures(root, G5_ONLY_PREFIXES))
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        return ["run_metadata.json is not an object"]
    if metadata.get("run_id") != G4_RUN_ID:
        failures.append("run metadata run_id mismatch")
    if metadata.get("critic_a_actual_model") != CRITIC_A_ACTUAL_MODEL:
        failures.append("run metadata critic_a_actual_model mismatch")
    if metadata.get("critic_b_actual_model") != CRITIC_B_ACTUAL_MODEL:
        failures.append("run metadata critic_b_actual_model mismatch")
    if metadata.get("human_adjudication_performed") is not False:
        failures.append("run metadata claims human adjudication")
    if metadata.get("finnish_revised") is not False:
        failures.append("run metadata claims Finnish revision")
    if metadata.get("g5_created") is not False:
        failures.append("run metadata claims G5 created")
    report = (run_dir / "G4_REVIEW_REPORT.md").read_text(encoding="utf-8")
    required_report = (
        "54/54",
        INDEPENDENCE_STATEMENT,
        "corroborated by both critics: 7",
        "Critic-A-only issues: 0",
        "Critic-B-only issues: 14",
        "EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5",
        "does not adjudicate",
        "does not revise Finnish wording",
        CRITIC_A_PROVENANCE_LIMITATION,
        SAME_FAMILY_LIMITATION,
        "S4A-2026-025",
        "S4A-2026-045",
        "BLOCKER",
        "G5 was not created",
        "not clinical validation",
    )
    for snippet in required_report:
        if snippet not in report:
            failures.append(f"report missing {snippet!r}")
    if "HUMAN_APPROVED" in report:
        failures.append("report claims HUMAN_APPROVED")
    if "G4 PASS" in report:
        failures.append("report claims G4 PASS")
    validation = json.loads((run_dir / "validation_results.json").read_text(encoding="utf-8"))
    if not isinstance(validation, dict):
        return ["validation_results.json is not an object"]
    if validation.get("critic_a_sha256") != EXPECTED_HASHES[CRITIC_A_RELATIVE]:
        failures.append("validation_results critic-a SHA mismatch")
    if validation.get("critic_b_sha256") != EXPECTED_HASHES[CRITIC_B_RELATIVE]:
        failures.append("validation_results critic-b SHA mismatch")
    if validation.get("g2_candidates_sha256") != EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]:
        failures.append("validation_results G2 SHA mismatch")
    if validation.get("g3_back_translation_sha256") != EXPECTED_HASHES[G3_BACK_RELATIVE]:
        failures.append("validation_results G3 SHA mismatch")
    if validation.get("human_approval_present") is not False:
        failures.append("validation_results claims human approval")
    if validation.get("clinical_validation_claimed") is not False:
        failures.append("validation_results claims clinical validation")
    if validation.get("finnish_revised") is not False:
        failures.append("validation_results claims Finnish revision")
    if validation.get("g5_created") is not False:
        failures.append("validation_results claims G5 created")
    if validation.get("critic_outputs_unchanged") is not True:
        failures.append("validation_results does not confirm critic outputs unchanged")
    return failures
