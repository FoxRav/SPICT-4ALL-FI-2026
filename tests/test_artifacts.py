from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.artifacts import validate_jsonl_artifact
from spict4all.errors import ArtifactValidationError


def _schema() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas/translation_candidate.schema.json"


def test_valid_candidate_passes(tmp_path, make_unit, make_candidate, write_jsonl) -> None:
    unit = make_unit()
    units = write_jsonl(tmp_path / "units.jsonl", [unit])
    artifact = write_jsonl(tmp_path / "candidate.jsonl", [make_candidate(unit)])
    assert len(validate_jsonl_artifact(artifact, _schema(), units)) == 1


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


def test_duplicate_candidate_unit_id_fails(
    tmp_path, make_unit, make_candidate, write_jsonl
) -> None:
    unit = make_unit()
    artifact = write_jsonl(
        tmp_path / "candidate.jsonl", [make_candidate(unit), make_candidate(unit)]
    )
    with pytest.raises(ArtifactValidationError, match="duplicate unit_id"):
        validate_jsonl_artifact(artifact, _schema())
