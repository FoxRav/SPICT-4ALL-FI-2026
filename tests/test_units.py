from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.errors import IntegrityError
from spict4all.units import load_source_units


def test_repository_source_units_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    assert len(load_source_units(root / "data/source_units.jsonl")) == 53


def test_duplicate_unit_id_fails(tmp_path, make_unit, write_jsonl) -> None:
    path = write_jsonl(tmp_path / "units.jsonl", [make_unit(0), make_unit(0)])
    with pytest.raises(IntegrityError, match="Duplicate unit_id"):
        load_source_units(path)


def test_missing_unit_id_fails(tmp_path, make_unit, write_jsonl) -> None:
    path = write_jsonl(tmp_path / "units.jsonl", [make_unit(0), make_unit(2)])
    with pytest.raises(IntegrityError, match="S4A-2026-001"):
        load_source_units(path)


def test_source_unit_hash_mismatch_fails(tmp_path, make_unit, write_jsonl) -> None:
    unit = make_unit(0)
    unit["source_text_sha256"] = "0" * 64
    path = write_jsonl(tmp_path / "units.jsonl", [unit])
    with pytest.raises(IntegrityError, match="Source-text hash mismatch"):
        load_source_units(path)


def test_source_index_translation_fails(tmp_path, make_unit, write_jsonl) -> None:
    unit = make_unit(0)
    unit["target_fi"] = "must remain empty"
    path = write_jsonl(tmp_path / "units.jsonl", [unit])
    with pytest.raises(IntegrityError, match="contains target translation"):
        load_source_units(path)


def test_source_unit_must_require_human_signoff(tmp_path, make_unit, write_jsonl) -> None:
    unit = make_unit(0)
    unit["requires_human_signoff"] = False
    path = write_jsonl(tmp_path / "units.jsonl", [unit])
    with pytest.raises(IntegrityError, match="does not require human sign-off"):
        load_source_units(path)


@pytest.mark.parametrize("status", ["AUTHORITY_DECISON_REQUIRED", "ARBITRARY"])
def test_unknown_translation_status_fails(
    tmp_path, make_unit, write_jsonl, status: str
) -> None:
    unit = make_unit(0)
    unit["translation_status"] = status
    path = write_jsonl(tmp_path / "units.jsonl", [unit])
    with pytest.raises(IntegrityError, match="Invalid translation_status"):
        load_source_units(path)
