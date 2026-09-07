from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.artifacts import _completed_candidate_failures, validate_jsonl_artifact
from spict4all.errors import ArtifactValidationError


def _schema() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas/translation_candidate.schema.json"


def test_valid_candidate_passes(tmp_path, make_unit, make_candidate, write_jsonl) -> None:
    unit = make_unit()
    units = write_jsonl(tmp_path / "units.jsonl", [unit])
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [make_candidate(unit)])
    assert len(validate_jsonl_artifact(artifact, _schema(), units)) == 1


def test_source_requirement_candidate_namespace_passes_schema(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    requirement_source = make_unit()
    requirement_source["unit_id"] = "S4A-REQ-2026-001"
    artifact = write_jsonl(
        tmp_path / "candidate.jsonl", [make_candidate(requirement_source)]
    )
    assert len(
        validate_jsonl_artifact(
            artifact, _schema(), source_records=[requirement_source]
        )
    ) == 1


def test_candidate_source_hash_mismatch_fails(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    unit = make_unit()
    units = write_jsonl(tmp_path / "units.jsonl", [unit])
    artifact = write_jsonl(
        tmp_path / "candidate.jsonl", [make_candidate(unit, source_text_sha256="0" * 64)]
    )
    with pytest.raises(ArtifactValidationError, match="source hash mismatch"):
        validate_jsonl_artifact(artifact, _schema(), units)


def test_malformed_jsonl_fails(tmp_path: Path) -> None:
    artifact = tmp_path / "broken.jsonl"
    artifact.write_text('{"unit_id":\n', encoding="utf-8")
    with pytest.raises(ArtifactValidationError, match="Malformed JSONL"):
        validate_jsonl_artifact(artifact, _schema())


def test_schema_missing_required_field_fails(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    candidate = make_candidate(make_unit())
    del candidate["model"]
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    with pytest.raises(ArtifactValidationError, match="model"):
        validate_jsonl_artifact(artifact, _schema())


def test_empty_completed_candidate_fails(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    candidate = make_candidate(
        make_unit(),
        candidate_fi="",
        status="READY_FOR_SYNTHESIS",
    )
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    with pytest.raises(ArtifactValidationError, match="candidate_fi"):
        validate_jsonl_artifact(artifact, _schema())


def test_empty_draft_represents_not_yet_generated_candidate(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    candidate = make_candidate(make_unit(), candidate_fi="", status="DRAFT")
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    assert len(validate_jsonl_artifact(artifact, _schema())) == 1


def test_nonempty_completed_test_fixture_passes(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    candidate = make_candidate(make_unit(), status="READY_FOR_SYNTHESIS")
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    assert len(validate_jsonl_artifact(artifact, _schema())) == 1


@pytest.mark.parametrize(
    "status",
    [
        "READY_FOR_SYNTHESIS",
        "READY_FOR_HUMAN_REVIEW",
        "HUMAN_APPROVED",
        "HUMAN_REJECTED",
    ],
)
@pytest.mark.parametrize("candidate_fi", ["", "   ", "\t\n"])
def test_whitespace_completed_candidate_fails(
    tmp_path,
    make_unit,
    make_candidate,
    write_jsonl,
    status: str,
    candidate_fi: str,
) -> None:
    candidate = make_candidate(
        make_unit(),
        candidate_fi=candidate_fi,
        status=status,
    )
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    with pytest.raises(ArtifactValidationError, match="candidate_fi"):
        validate_jsonl_artifact(artifact, _schema())


@pytest.mark.parametrize(
    "status",
    [
        "READY_FOR_SYNTHESIS",
        "READY_FOR_HUMAN_REVIEW",
        "HUMAN_APPROVED",
        "HUMAN_REJECTED",
    ],
)
def test_missing_completed_candidate_fails(
    tmp_path,
    make_unit,
    make_candidate,
    write_jsonl,
    status: str,
) -> None:
    candidate = make_candidate(make_unit(), status=status)
    del candidate["candidate_fi"]
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    with pytest.raises(ArtifactValidationError, match="candidate_fi"):
        validate_jsonl_artifact(artifact, _schema())


def test_completed_candidate_domain_check_rejects_whitespace_without_schema() -> None:
    failures = _completed_candidate_failures(
        1,
        {"status": "HUMAN_APPROVED", "candidate_fi": "   "},
    )
    assert failures
    assert "non-whitespace" in failures[0]


@pytest.mark.parametrize(
    "field",
    ["human_signoff", "gates_passed", "eligible_for_document_insertion"],
)
def test_candidate_rejects_approval_shaped_additional_properties(
    tmp_path,
    make_unit,
    make_candidate,
    write_jsonl,
    field: str,
) -> None:
    candidate = make_candidate(make_unit())
    candidate[field] = True
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    with pytest.raises(ArtifactValidationError, match="Additional properties"):
        validate_jsonl_artifact(artifact, _schema())


def test_candidate_namespaced_extensions_are_accepted(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    candidate = make_candidate(
        make_unit(),
        extensions={"vendor.example": {"session_note": "non-authoritative"}},
    )
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [candidate])
    assert len(validate_jsonl_artifact(artifact, _schema())) == 1


def test_duplicate_candidate_unit_id_fails(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    unit = make_unit()
    artifact = write_jsonl(
        tmp_path / "candidate.jsonl", [make_candidate(unit), make_candidate(unit)]
    )
    with pytest.raises(ArtifactValidationError, match="duplicate unit_id"):
        validate_jsonl_artifact(artifact, _schema())
