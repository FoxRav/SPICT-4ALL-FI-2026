"""Mechanical G2 synthesis coverage and provenance checks.

These checks do not prove semantic or clinical correctness and carry no
approval authority.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .artifacts import load_schema
from .errors import ArtifactValidationError
from .hashing import sha256_bytes, sha256_file, sha256_text
from .jsonl import load_jsonl

G2_RUN_ID = "G2-20260908-001"
G2_ROLE = "G2 synthesis reviewer"
ACTUAL_MODEL = "Cursor Grok 4.6"
RUN_METADATA_ROLE = f"{G2_ROLE} (actual model: {ACTUAL_MODEL})"
G2_RUN_DIR = Path("work") / "synthesis" / G2_RUN_ID
CONFIGURED_ROLE_MODEL = "Claude Opus 5 High"
AGENT_A_MODEL = "GPT-6"
AGENT_B_MODEL = "Cursor Grok 4.6"
STATUS = "READY_FOR_HUMAN_REVIEW"
EXPECTED_COUNT = 54
CANONICAL_COUNT = 53
REQUIREMENT_ID = "S4A-REQ-2026-001"
TITLE_ID = "S4A-2026-000"
EXPECTED_AGREE = 17
EXPECTED_DISAGREE = 37
CLASSIFICATIONS = (
    "A_B_AGREE",
    "SELECT_A",
    "SELECT_B",
    "COMBINE_A_B",
    "NEW_SYNTHESIS",
)
FROZEN_INPUT_HASHES: dict[str, str] = {
    "work/agent-a/candidates.jsonl": (
        "82d06571c855c87d04e015bf905b1943c5fcd31e68827695fd4cfceb52f4c2cd"
    ),
    "work/agent-b/runs/G1-B-20260908-002/candidates.jsonl": (
        "6033c9970d0b61fd64dfc5c0350b6c97a9ba3cf35725d2f8db7aee79752a25a1"
    ),
    "work/agent-b/candidates.jsonl": (
        "0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640"
    ),
    "deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip": (
        "6e8846bc233070f3b18f7a3fbba81cb2bd4c04090afa5fbfe9be5aa0fc4fd0ef"
    ),
}
AGENT_A_ARTIFACT = "work/agent-a/candidates.jsonl"
AGENT_B_R2_ARTIFACT = "work/agent-b/runs/G1-B-20260908-002/candidates.jsonl"
SAME_FAMILY_LIMITATION = (
    "Forward Translator B and the G2 synthesis reviewer both used Cursor "
    "Grok 4.6. B wording has no preferential authority. Both A and B were "
    "judged independently against the exact frozen English source."
)
HUMAN_TERMINOLOGY_IDS: dict[str, str] = {
    "S4A-2026-001": "T-002",
    "S4A-2026-035": "T-013",
    "S4A-2026-042": "T-002",
    "S4A-2026-049": "T-016",
}
HUMAN_WORDINGS: dict[str, tuple[str, ...]] = {
    "S4A-2026-001": ("elinikää lyhentäv", "terveydentila on heikentynyt"),
    "S4A-2026-004": ("toimintakyky on heikentynyt", "tavanomaisissa"),
    "S4A-2026-014": ("toimintakyky on heikentynyt", "tavanomaisissa"),
    "S4A-2026-017": ("ei ole riittävän hyväkuntoinen syöpähoitoon",),
    "S4A-2026-035": ("hengityskone",),
    "S4A-2026-042": ("elinikää lyhentäv", "terveydentila on heikentynyt"),
    "S4A-2026-049": ("kokonaisvaltainen hoito",),
}


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


def expected_source_index(
    units: list[dict[str, Any]], requirements: list[dict[str, Any]]
) -> dict[str, tuple[str, str, str]]:
    expected: dict[str, tuple[str, str, str]] = {}
    for row in units:
        unit_id = str(row["unit_id"])
        expected[unit_id] = (
            str(row["source_text_en"]),
            str(row["source_text_sha256"]),
            "canonical_source_unit",
        )
    for row in requirements:
        if row.get("translation_evidence_required") is True:
            req_id = str(row["requirement_id"])
            if req_id in expected:
                raise ArtifactValidationError(f"duplicate source identifier {req_id}")
            expected[req_id] = (
                str(row["exact_source_text_en"]),
                str(row["exact_text_sha256"]),
                "official_change_requirement",
            )
    return expected


def g2_failures(
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    expected: dict[str, tuple[str, str, str]],
    agent_a: list[dict[str, Any]],
    agent_b: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    if len(expected) != EXPECTED_COUNT:
        failures.append(f"frozen source universe is {len(expected)}")
    canonical = sum(1 for _english, _digest, kind in expected.values() if kind == "canonical_source_unit")
    if canonical != CANONICAL_COUNT:
        failures.append(f"canonical unit count is {canonical}")
    for label, rows in (
        ("candidates", candidates),
        ("decisions", decisions),
        ("agent_a", agent_a),
        ("agent_b", agent_b),
    ):
        ids = [str(row.get("unit_id")) for row in rows]
        if len(ids) != EXPECTED_COUNT or len(set(ids)) != EXPECTED_COUNT:
            failures.append(f"{label} count/uniqueness is {len(ids)}/{len(set(ids))}")
        if set(ids) != set(expected):
            failures.append(f"{label} IDs differ from frozen source universe")
    a_by_id = {str(row["unit_id"]): row for row in agent_a}
    b_by_id = {str(row["unit_id"]): row for row in agent_b}
    d_by_id = {str(row["unit_id"]): row for row in decisions}
    c_by_id = {str(row["unit_id"]): row for row in candidates}
    agree = 0
    classified_agree = 0
    for unit_id, (english, digest, kind) in expected.items():
        a_row = a_by_id.get(unit_id)
        b_row = b_by_id.get(unit_id)
        d_row = d_by_id.get(unit_id)
        c_row = c_by_id.get(unit_id)
        if a_row is None or b_row is None or d_row is None or c_row is None:
            continue
        a_fi = str(a_row.get("candidate_fi") or "")
        b_fi = str(b_row.get("candidate_fi") or "")
        if a_fi == b_fi:
            agree += 1
        classification = d_row.get("classification")
        if classification not in CLASSIFICATIONS:
            failures.append(f"{unit_id}: invalid classification {classification!r}")
        if classification == "A_B_AGREE":
            classified_agree += 1
            if a_fi != b_fi:
                failures.append(f"{unit_id}: A_B_AGREE but A and B differ")
            if str(d_row.get("candidate_fi")) != a_fi:
                failures.append(f"{unit_id}: A_B_AGREE wording is not the agreed text")
        elif a_fi == b_fi:
            failures.append(f"{unit_id}: A and B identical but classification is {classification}")
        else:
            if not str(d_row.get("meaningful_difference") or "").strip():
                failures.append(f"{unit_id}: disagreement lacks meaningful_difference")
            if not str(d_row.get("source_fidelity_rationale") or "").strip():
                failures.append(f"{unit_id}: disagreement lacks source_fidelity_rationale")
        final_fi = str(c_row.get("candidate_fi") or "")
        if not final_fi.strip():
            failures.append(f"{unit_id}: blank Finnish candidate")
        if str(d_row.get("candidate_fi")) != final_fi:
            failures.append(f"{unit_id}: candidate/decision Finnish mismatch")
        if c_row.get("model") != ACTUAL_MODEL:
            failures.append(f"{unit_id}: model is {c_row.get('model')!r}")
        if c_row.get("status") == "HUMAN_APPROVED" or d_row.get("status") == "HUMAN_APPROVED":
            failures.append(f"{unit_id}: HUMAN_APPROVED claimed")
        if c_row.get("status") != STATUS:
            failures.append(f"{unit_id}: status is {c_row.get('status')!r}")
        if c_row.get("source_text_sha256") != digest:
            failures.append(f"{unit_id}: candidate source SHA mismatch")
        if d_row.get("source_text_sha256") != digest:
            failures.append(f"{unit_id}: decision source SHA mismatch")
        if sha256_text(english) != digest:
            failures.append(f"{unit_id}: frozen English does not hash to source SHA")
        ext = c_row.get("extensions")
        g2 = ext.get("g2_synthesis") if isinstance(ext, dict) else None
        if not isinstance(g2, dict):
            failures.append(f"{unit_id}: missing g2_synthesis extension")
            continue
        if g2.get("exact_source_text_en") != english:
            failures.append(f"{unit_id}: exact English mismatch")
        if g2.get("source_kind") != kind:
            failures.append(f"{unit_id}: source_kind mismatch")
        if g2.get("run_id") != G2_RUN_ID:
            failures.append(f"{unit_id}: run_id mismatch")
        if g2.get("classification") != classification:
            failures.append(f"{unit_id}: extension classification mismatch")
        if unit_id in {TITLE_ID, REQUIREMENT_ID}:
            if g2.get("final_inclusion_status") != "UNRESOLVED":
                failures.append(f"{unit_id}: authority is not UNRESOLVED")
            if g2.get("eligible_for_document_insertion") is not False:
                failures.append(f"{unit_id}: marked insertable")
        if kind == "official_change_requirement" and unit_id != REQUIREMENT_ID:
            failures.append(f"{unit_id}: unexpected requirement")
        if str(d_row.get("agent_a_artifact")) != AGENT_A_ARTIFACT:
            failures.append(f"{unit_id}: Agent A artifact path mismatch")
        if str(d_row.get("agent_b_r2_artifact")) != AGENT_B_R2_ARTIFACT:
            failures.append(f"{unit_id}: Agent B-R2 artifact path mismatch")
        if d_row.get("agent_a_artifact_sha256") != FROZEN_INPUT_HASHES[AGENT_A_ARTIFACT]:
            failures.append(f"{unit_id}: Agent A artifact hash mismatch")
        if d_row.get("agent_b_r2_artifact_sha256") != FROZEN_INPUT_HASHES[AGENT_B_R2_ARTIFACT]:
            failures.append(f"{unit_id}: Agent B-R2 artifact hash mismatch")
        if str(d_row.get("agent_a_candidate_fi") or "") != a_fi:
            failures.append(f"{unit_id}: recorded A candidate mismatch")
        if str(d_row.get("agent_b_r2_candidate_fi") or "") != b_fi:
            failures.append(f"{unit_id}: recorded B-R2 candidate mismatch")
        if d_row.get("actual_model") != ACTUAL_MODEL:
            failures.append(f"{unit_id}: decision model is {d_row.get('actual_model')!r}")
        refs = d_row.get("human_decision_refs")
        if not isinstance(refs, list):
            failures.append(f"{unit_id}: human_decision_refs is not a list")
            refs = []
        term_id = HUMAN_TERMINOLOGY_IDS.get(unit_id)
        if term_id is not None and term_id not in {str(item) for item in refs}:
            failures.append(f"{unit_id}: missing human terminology id {term_id}")
        for fragment in HUMAN_WORDINGS.get(unit_id, ()):
            if fragment.casefold() not in final_fi.casefold():
                failures.append(f"{unit_id}: missing recorded human wording {fragment!r}")
    if agree != EXPECTED_AGREE:
        failures.append(f"exact A/B agreements are {agree}, expected {EXPECTED_AGREE}")
    if classified_agree != EXPECTED_AGREE:
        failures.append(f"A_B_AGREE classifications are {classified_agree}")
    if EXPECTED_COUNT - agree != EXPECTED_DISAGREE:
        failures.append("A/B disagreement count is not 37")
    return failures


def verify_frozen_input_bytes(named: dict[str, bytes]) -> None:
    for relative, expected in FROZEN_INPUT_HASHES.items():
        data = named.get(relative)
        if data is None:
            raise ArtifactValidationError(f"Required G2 input missing: {relative}")
        if sha256_bytes(data) != expected:
            raise ArtifactValidationError(f"Required G2 input hash mismatch: {relative}")


def verify_frozen_inputs(root: Path) -> None:
    named = {relative: (root / relative).read_bytes() for relative in FROZEN_INPUT_HASHES}
    verify_frozen_input_bytes(named)


def classification_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("classification")) for row in decisions)
    return {key: int(counts.get(key, 0)) for key in CLASSIFICATIONS}


def candidate_schema_failures(
    candidates: list[dict[str, Any]], schema_path: Path
) -> list[str]:
    validator = Draft202012Validator(load_schema(schema_path))
    failures: list[str] = []
    for index, record in enumerate(candidates, 1):
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        failures.extend(
            f"line {index} {'.'.join(map(str, error.path)) or '<record>'}: {error.message}"
            for error in errors
        )
    return failures


def load_g2_run(run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        load_jsonl(run_dir / "candidates.jsonl"),
        load_jsonl(run_dir / "synthesis_decisions.jsonl"),
    )


def g2_run_failures(root: Path) -> list[str]:
    verify_frozen_inputs(root)
    run_dir = root / G2_RUN_DIR
    required = (
        "candidates.jsonl",
        "synthesis_decisions.jsonl",
        "run_metadata.json",
        "G2_SYNTHESIS_REPORT.md",
        "validation_results.json",
    )
    failures: list[str] = []
    for name in required:
        if not (run_dir / name).is_file():
            failures.append(f"missing G2 run file: {name}")
    if failures:
        return failures
    candidates, decisions = load_g2_run(run_dir)
    units = load_jsonl(root / "data/source_units.jsonl")
    requirements = load_jsonl(root / "data/source_requirements.jsonl")
    expected = expected_source_index(units, requirements)
    agent_a = load_jsonl(root / AGENT_A_ARTIFACT)
    agent_b = load_jsonl(root / AGENT_B_R2_ARTIFACT)
    failures.extend(g2_failures(candidates, decisions, expected, agent_a, agent_b))
    failures.extend(
        candidate_schema_failures(
            candidates, root / "schemas/translation_candidate.schema.json"
        )
    )
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        failures.append("run_metadata.json is not an object")
        return failures
    if ACTUAL_MODEL not in str(metadata.get("role", "")):
        failures.append("run metadata role does not record Cursor Grok 4.6")
    if metadata.get("actual_model") != ACTUAL_MODEL:
        failures.append(f"run metadata actual_model is {metadata.get('actual_model')!r}")
    report = (run_dir / "G2_SYNTHESIS_REPORT.md").read_text(encoding="utf-8")
    if ACTUAL_MODEL not in report:
        failures.append("synthesis report does not record Cursor Grok 4.6")
    if SAME_FAMILY_LIMITATION not in report:
        failures.append("synthesis report omits same-family limitation")
    if "HUMAN_APPROVED" in report:
        failures.append("synthesis report claims HUMAN_APPROVED")
    if "not clinical validation" not in report.lower():
        failures.append("synthesis report does not disclaim clinical validation")
    if "G3 was not started" not in report:
        failures.append("synthesis report does not record that G3 was not started")
    if "Actual model used: Cursor Grok 4.6" not in report:
        failures.append("synthesis report does not record the actual G2 model identity")
    if metadata.get("agent_b_model") != AGENT_B_MODEL:
        failures.append("run metadata does not record Agent B model")
    if metadata.get("same_family_limitation") != SAME_FAMILY_LIMITATION:
        failures.append("run metadata omits same-family limitation")
    if metadata.get("run_id") != G2_RUN_ID:
        failures.append("run metadata run_id mismatch")
    if metadata.get("status") != "DRAFT":
        failures.append("run metadata status is not DRAFT")
    if sha256_file(root / AGENT_A_ARTIFACT) != FROZEN_INPUT_HASHES[AGENT_A_ARTIFACT]:
        failures.append("live Agent A evidence hash changed")
    if sha256_file(root / AGENT_B_R2_ARTIFACT) != FROZEN_INPUT_HASHES[AGENT_B_R2_ARTIFACT]:
        failures.append("live Agent B-R2 evidence hash changed")
    if (
        sha256_file(root / "work/agent-b/candidates.jsonl")
        != FROZEN_INPUT_HASHES["work/agent-b/candidates.jsonl"]
    ):
        failures.append("live historical Agent B evidence hash changed")
    if (
        sha256_file(
            root / "deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip"
        )
        != FROZEN_INPUT_HASHES[
            "deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip"
        ]
    ):
        failures.append("live G1 gate ZIP hash changed")
    later_gate_prefixes = (
        "work/final/",
        "work/human-review/",
    )
    for prefix in later_gate_prefixes:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                failures.append(
                    f"G5/later-gate file present: {path.relative_to(root).as_posix()}"
                )
    other_g2 = [
        path
        for path in (root / "work/synthesis").rglob("*")
        if path.is_file()
        and path.name != ".gitkeep"
        and G2_RUN_ID not in path.relative_to(root / "work/synthesis").parts
    ]
    if other_g2:
        failures.append(
            "unexpected synthesis files: "
            + ", ".join(path.relative_to(root).as_posix() for path in other_g2)
        )
    counts = classification_counts(decisions)
    if counts["A_B_AGREE"] != EXPECTED_AGREE:
        failures.append(f"A_B_AGREE count is {counts['A_B_AGREE']}")
    if sum(counts[key] for key in CLASSIFICATIONS if key != "A_B_AGREE") != EXPECTED_DISAGREE:
        failures.append("disagreement classifications do not sum to 37")
    candidate_sha = sha256_file(run_dir / "candidates.jsonl")
    decision_sha = sha256_file(run_dir / "synthesis_decisions.jsonl")
    validation = json.loads((run_dir / "validation_results.json").read_text(encoding="utf-8"))
    if not isinstance(validation, dict):
        failures.append("validation_results.json is not an object")
        return failures
    if validation.get("candidate_sha256") != candidate_sha:
        failures.append("validation_results candidate SHA mismatch")
    if validation.get("synthesis_decisions_sha256") != decision_sha:
        failures.append("validation_results decisions SHA mismatch")
    if validation.get("human_approval_present") is not False:
        failures.append("validation_results claims human approval")
    if validation.get("clinical_validation_claimed") is not False:
        failures.append("validation_results claims clinical validation")
    if validation.get("g3_started") is not False:
        failures.append("validation_results claims G3 started")
    return failures
