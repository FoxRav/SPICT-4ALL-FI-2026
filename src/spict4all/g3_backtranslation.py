"""Mechanical G3 blind back-translation coverage and provenance checks.

These checks do not compare Finnish or English meaning with the frozen SPICT
source and carry no approval or clinical-validation authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError
from .hashing import sha256_bytes
from .jsonl import load_jsonl

G3_RUN_ID = "G3-20260908-001"
G3_ROLE = "Blind back-translator"
ACTUAL_MODEL = "GPT-5.6 Sol"
REASONING_EFFORT = "High"
ENVIRONMENT = "ChatGPT Temporary Chat"
CONFIGURED_ROLE_MODEL = "GPT-5.6 Sol Medium"
MODEL_PROVENANCE_BASIS = (
    "Recorded from WP-G3-BLIND-BACKTRANSLATION-AUDIT-001 as the operator-stated "
    "ChatGPT Temporary Chat session that produced back_translation.jsonl. "
    "No independent API request log is packaged."
)
G3_RUN_DIR = Path("work") / "backtranslation" / G3_RUN_ID
BLIND_INPUT_RELATIVE = f"{G3_RUN_DIR.as_posix()}/blind_input.jsonl"
BACK_TRANSLATION_RELATIVE = f"{G3_RUN_DIR.as_posix()}/back_translation.jsonl"
G2_CANDIDATES_RELATIVE = "work/synthesis/G2-20260908-001/candidates.jsonl"
EXPECTED_COUNT = 54
TITLE_ID = "S4A-2026-000"
REQUIREMENT_ID = "S4A-REQ-2026-001"
BLIND_FIELDS = ("unit_id", "text_fi")
BACK_FIELDS = ("unit_id", "back_translation_en", "uncertainty")
FORBIDDEN_BLIND_TOKENS = (
    "source_text_en",
    "source_text_sha256",
    "exact_source_text_en",
    "candidate_fi",
    "agent_a",
    "agent_b",
    "source_fidelity_rationale",
    "classification",
)
EXPECTED_HASHES: dict[str, str] = {
    BACK_TRANSLATION_RELATIVE: (
        "e674a7f0a69ed05c554eaade38e4dbd8025c1f34df0499a8fc4cc9a15c99f00f"
    ),
    BLIND_INPUT_RELATIVE: (
        "bbe32669ae4d0f25c3013f24573f14c2823021a96cbffc1ced4fe3f0f456f634"
    ),
    G2_CANDIDATES_RELATIVE: (
        "76462191d3ad2a83c878982a1460443f322437e547b747f6267f4a29d887c619"
    ),
}
BLINDING_CLAIM = (
    "The back-translator received only the Finnish-only blind input "
    f"({BLIND_INPUT_RELATIVE}: unit_id and text_fi). This G3 audit does not "
    "claim independent observation of the Temporary Chat session beyond the "
    "operator-recorded method and the on-disk artifacts."
)


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


def extra_field_failures(
    rows: list[dict[str, Any]], allowed: tuple[str, ...], label: str
) -> list[str]:
    allowed_set = set(allowed)
    failures: list[str] = []
    for index, row in enumerate(rows, 1):
        extra = sorted(set(row) - allowed_set)
        missing = [name for name in allowed if name not in row]
        if extra:
            failures.append(f"{label} line {index}: extra fields {extra}")
        if missing:
            failures.append(f"{label} line {index}: missing fields {missing}")
    return failures


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


def g3_pair_failures(
    blind: list[dict[str, Any]], back: list[dict[str, Any]]
) -> list[str]:
    failures: list[str] = []
    failures.extend(extra_field_failures(blind, BLIND_FIELDS, "blind_input"))
    failures.extend(extra_field_failures(back, BACK_FIELDS, "back_translation"))
    failures.extend(identity_failures(blind, "blind_input"))
    failures.extend(identity_failures(back, "back_translation"))
    blind_ids = [str(row.get("unit_id")) for row in blind]
    back_ids = [str(row.get("unit_id")) for row in back]
    if blind_ids != back_ids:
        failures.append("back_translation unit_id order differs from blind_input")
    for row in blind:
        unit_id = str(row.get("unit_id"))
        finnish = row.get("text_fi")
        if not isinstance(finnish, str) or not finnish.strip():
            failures.append(f"{unit_id}: blank text_fi")
        blob = json.dumps(row, ensure_ascii=False)
        for token in FORBIDDEN_BLIND_TOKENS:
            if token in row:
                failures.append(f"{unit_id}: forbidden blind field {token}")
            elif token in blob and token not in str(finnish):
                failures.append(f"{unit_id}: forbidden token {token} in blind input")
    for row in back:
        unit_id = str(row.get("unit_id"))
        english = row.get("back_translation_en")
        if not isinstance(english, str) or not english.strip():
            failures.append(f"{unit_id}: blank back_translation_en")
        uncertainty = row.get("uncertainty")
        if not isinstance(uncertainty, str):
            failures.append(f"{unit_id}: uncertainty is not a string")
    return failures


def derivation_failures(
    blind: list[dict[str, Any]], g2_fi_by_id: dict[str, str]
) -> list[str]:
    failures: list[str] = []
    blind_ids = [str(row.get("unit_id")) for row in blind]
    if set(blind_ids) != set(g2_fi_by_id):
        missing = sorted(set(g2_fi_by_id) - set(blind_ids))
        extra = sorted(set(blind_ids) - set(g2_fi_by_id))
        if missing:
            failures.append(f"blind input missing G2 IDs {missing}")
        if extra:
            failures.append(f"blind input extra IDs {extra}")
        return failures
    for row in blind:
        unit_id = str(row["unit_id"])
        if str(row.get("text_fi")) != g2_fi_by_id[unit_id]:
            failures.append(f"{unit_id}: blind text_fi differs from G2 candidate_fi")
    return failures


def g2_fi_by_id(candidates: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in candidates:
        unit_id = str(row["unit_id"])
        if unit_id in mapping:
            raise ArtifactValidationError(f"duplicate G2 unit_id {unit_id}")
        mapping[unit_id] = str(row["candidate_fi"])
    return mapping


def finnish_only_extract(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"unit_id": str(row["unit_id"]), "candidate_fi": str(row["candidate_fi"])}
        for row in candidates
    ]


def verify_frozen_g3_bytes(named: dict[str, bytes]) -> None:
    for relative, expected in EXPECTED_HASHES.items():
        data = named.get(relative)
        if data is None:
            raise ArtifactValidationError(f"Required G3 artifact missing: {relative}")
        if sha256_bytes(data) != expected:
            raise ArtifactValidationError(f"Required G3 artifact hash mismatch: {relative}")


def g3_run_failures(root: Path) -> list[str]:
    failures: list[str] = []
    named = {
        relative: (root / relative).read_bytes()
        for relative in EXPECTED_HASHES
        if (root / relative).is_file()
    }
    try:
        verify_frozen_g3_bytes(named)
    except ArtifactValidationError as exc:
        failures.append(str(exc))
        return failures
    blind = load_jsonl(root / BLIND_INPUT_RELATIVE)
    back = load_jsonl(root / BACK_TRANSLATION_RELATIVE)
    g2 = load_jsonl(root / G2_CANDIDATES_RELATIVE)
    failures.extend(g3_pair_failures(blind, back))
    failures.extend(derivation_failures(blind, g2_fi_by_id(g2)))
    run_dir = root / G3_RUN_DIR
    for name in ("run_metadata.json", "G3_BACKTRANSLATION_REPORT.md", "validation_results.json"):
        if not (run_dir / name).is_file():
            failures.append(f"missing G3 metadata file: {name}")
    if failures:
        return failures
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        return ["run_metadata.json is not an object"]
    if metadata.get("actual_model") != ACTUAL_MODEL:
        failures.append(f"run metadata actual_model is {metadata.get('actual_model')!r}")
    if metadata.get("reasoning_effort") != REASONING_EFFORT:
        failures.append("run metadata reasoning_effort mismatch")
    if metadata.get("environment") != ENVIRONMENT:
        failures.append("run metadata environment mismatch")
    if ACTUAL_MODEL not in str(metadata.get("role", "")):
        failures.append("run metadata role omits GPT-5.6 Sol")
    report = (run_dir / "G3_BACKTRANSLATION_REPORT.md").read_text(encoding="utf-8")
    if "54/54" not in report:
        failures.append("report does not record 54/54")
    if ACTUAL_MODEL not in report:
        failures.append("report omits actual model")
    if "no semantic comparison" not in report.lower():
        failures.append("report does not state that no semantic comparison was performed")
    if "HUMAN_APPROVED" in report:
        failures.append("report claims HUMAN_APPROVED")
    if "not clinical validation" not in report.lower():
        failures.append("report does not disclaim clinical validation")
    if "G4 was not started" not in report:
        failures.append("report does not record that G4 was not started")
    validation = json.loads((run_dir / "validation_results.json").read_text(encoding="utf-8"))
    if not isinstance(validation, dict):
        return ["validation_results.json is not an object"]
    if validation.get("back_translation_sha256") != EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE]:
        failures.append("validation_results back-translation SHA mismatch")
    if validation.get("human_approval_present") is not False:
        failures.append("validation_results claims human approval")
    if validation.get("clinical_validation_claimed") is not False:
        failures.append("validation_results claims clinical validation")
    if validation.get("semantic_comparison_with_source_performed") is not False:
        failures.append("validation_results claims source semantic comparison")
    if validation.get("g4_started") is not False:
        failures.append("validation_results claims G4 started")
    later = (
        "work/critics/",
        "work/final/",
        "work/human-review/",
    )
    for prefix in later:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                failures.append(f"G4/later-gate file present: {path.relative_to(root).as_posix()}")
    return failures
