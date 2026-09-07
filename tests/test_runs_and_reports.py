from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.errors import ArtifactValidationError, ImmutableRunError
from spict4all.hashing import sha256_file
from spict4all.reports import generate_discrepancy_report
from spict4all.runs import build_run_metadata, create_immutable_run


def test_run_metadata_records_input_hash(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    input_path.write_text("{}\n", encoding="utf-8")
    metadata = build_run_metadata(
        "run-001", "forward_translation_A", [input_path],
        created_at_utc="2026-09-07T00:00:00Z",
    )
    assert metadata["status"] == "DRAFT"
    assert metadata["inputs"][0]["sha256"] == sha256_file(input_path)


def test_immutable_run_refuses_overwrite(tmp_path: Path) -> None:
    metadata = {
        "run_id": "run-001", "role": "test", "status": "DRAFT",
        "created_at_utc": "2026-09-07T00:00:00Z", "tool_version": "test", "inputs": [],
    }
    create_immutable_run(tmp_path, metadata)
    with pytest.raises(ImmutableRunError, match="refusing overwrite"):
        create_immutable_run(tmp_path, metadata)


def test_discrepancy_report_is_deterministic_tsv(
    tmp_path, make_unit, make_candidate
) -> None:
    unit = make_unit()
    a = make_candidate(unit, candidate_fi="A")
    b = make_candidate(unit, candidate_fi="B", issues=[{"severity": "MINOR"}])
    output = tmp_path / "report.tsv"
    generate_discrepancy_report([unit], [a], [b], output)
    text = output.read_text(encoding="utf-8")
    assert "candidate_text_equal" in text
    assert "false" in text
    assert text.endswith("\n")


def test_discrepancy_report_refuses_overwrite(
    tmp_path, make_unit, make_candidate
) -> None:
    unit = make_unit()
    candidate = make_candidate(unit)
    output = tmp_path / "report.tsv"
    output.write_text("existing", encoding="utf-8")
    with pytest.raises(ArtifactValidationError, match="refusing overwrite"):
        generate_discrepancy_report([unit], [candidate], [candidate], output)
