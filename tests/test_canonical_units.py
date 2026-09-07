from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from spict4all.errors import GateError, IntegrityError
from spict4all.evidence import FinalInclusionStatus
from spict4all.gates import (
    assert_publication_allowed,
    assert_source_reconciliation_resolved,
)
from spict4all.hashing import sha256_file, sha256_text
from spict4all.requirements import (
    build_translation_evidence_sources,
    load_canonical_unit_exceptions,
    verify_canonical_units_against_source,
    verify_source_requirements,
)
from spict4all.units import load_source_units, validate_source_units

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "sources/manifests/source_manifest.json"
OFFICIAL = ROOT / "sources/official"
UNITS_PATH = ROOT / "data/source_units.jsonl"
EXCEPTIONS = ROOT / "data/canonical_unit_exceptions.jsonl"
EXCEPTION_SCHEMA = ROOT / "schemas/canonical_unit_exception.schema.json"
REQUIREMENTS = ROOT / "data/source_requirements.jsonl"
REQUIREMENT_SCHEMA = ROOT / "schemas/source_requirement.schema.json"
SOURCE_UNITS_SHA256 = "f4751a7e67ff42338fc5c23a842cc7af07c03f2c6a394dea1819f26546c127a5"
LIVER_TEXT = "A liver transplant is not possible."


def _exception_record() -> dict[str, Any]:
    return json.loads(EXCEPTIONS.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def _repository_canonical_verification():
    units = load_source_units(UNITS_PATH)
    verification = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    return units, verification


def _fabricated_liver_unit(units: list[dict[str, Any]]) -> dict[str, Any]:
    unit = copy.deepcopy(units[-1])
    unit.update(
        {
            "unit_id": "S4A-2026-053",
            "section": "fabricated",
            "source_text_en": LIVER_TEXT,
            "source_text_sha256": sha256_text(LIVER_TEXT),
            "source_location": {
                "table_index": 0,
                "row": 31,
                "column": 2,
                "paragraph": 0,
            },
        }
    )
    return unit


def _exception_for_unit(
    unit: dict[str, Any],
    *,
    approved: bool,
) -> dict[str, Any]:
    record = _exception_record()
    record.update(
        {
            "unit_id": unit["unit_id"],
            "unit_text": unit["source_text_en"],
            "unit_source_text_sha256": unit["source_text_sha256"],
        }
    )
    if approved:
        record.update(
            {
                "authority_status": "AUTHORITY_RESOLVED",
                "source_authority_decision_required": False,
                "publication_blocking": False,
                "evidence_status": "AUTHORITY_RESOLVED",
                "authority_disposition": {
                    "unit_id": unit["unit_id"],
                    "decision": "APPROVE_CANONICAL_EXCEPTION",
                    "decision_maker": "Adversarial test fixture",
                    "decision_date": "2026-09-07",
                    "evidence_reference": "fixture-only",
                    "status": "FINAL",
                },
            }
        )
    return record


def test_all_existing_canonical_units_resolve_or_have_exception() -> None:
    units, verification = _repository_canonical_verification()
    direct = [item for item in verification.resolutions if item.direct_location]
    normalized = [item for item in verification.resolutions if item.normalized_location]
    excepted = [item for item in verification.resolutions if item.exception]
    assert len(units) == len(verification.resolutions) == 53
    assert len(direct) == 52
    assert [item.unit["unit_id"] for item in normalized] == ["S4A-2026-000"]
    assert [item.unit["unit_id"] for item in excepted] == ["S4A-2026-000"]
    assert len(verification.exceptions) == 1


def test_fabricated_canonical_unit_absent_from_docx_fails() -> None:
    units = load_source_units(UNITS_PATH)
    units.append(_fabricated_liver_unit(units))
    validate_source_units(units)
    with pytest.raises(IntegrityError, match="has no canonical-unit exception"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
        )


def test_liver_requirement_cannot_be_laundered_into_canonical_namespace() -> None:
    units = load_source_units(UNITS_PATH)
    units.append(_fabricated_liver_unit(units))
    with pytest.raises(IntegrityError, match="S4A-2026-053"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
        )


def test_liver_canonical_unit_with_unresolved_exception_fails(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    liver_unit = _fabricated_liver_unit(units)
    liver_unit["translation_status"] = "AUTHORITY_DECISION_REQUIRED"
    units.append(liver_unit)
    exceptions = _write_jsonl(
        tmp_path / "exceptions.jsonl",
        [_exception_record(), _exception_for_unit(liver_unit, approved=False)],
    )
    with pytest.raises(IntegrityError, match="normalized canonical text does not equal"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_liver_canonical_unit_with_approved_exception_fails(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    liver_unit = _fabricated_liver_unit(units)
    liver_unit["translation_status"] = "AUTHORITY_RESOLVED"
    units.append(liver_unit)
    exceptions = _write_jsonl(
        tmp_path / "exceptions.jsonl",
        [_exception_record(), _exception_for_unit(liver_unit, approved=True)],
    )
    with pytest.raises(IntegrityError, match="normalized canonical text does not equal"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_arbitrary_fabricated_text_with_approved_exception_fails(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    fabricated = _fabricated_liver_unit(units)
    fabricated["source_text_en"] = "Fabricated canonical assertion."
    fabricated["source_text_sha256"] = sha256_text(fabricated["source_text_en"])
    fabricated["translation_status"] = "AUTHORITY_RESOLVED"
    units.append(fabricated)
    exceptions = _write_jsonl(
        tmp_path / "exceptions.jsonl",
        [_exception_record(), _exception_for_unit(fabricated, approved=True)],
    )
    with pytest.raises(IntegrityError, match="normalized canonical text does not equal"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_source_unit_text_cannot_expand_canonical_corpus() -> None:
    units, verification = _repository_canonical_verification()
    assert LIVER_TEXT not in verification.canonical_docx_texts
    assert all(
        str(unit["source_text_en"]) in verification.canonical_docx_texts
        for unit in units[1:]
    )


def test_unmatched_canonical_unit_without_exception_fails(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    empty_exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [])
    with pytest.raises(IntegrityError, match="S4A-2026-000"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, empty_exceptions, EXCEPTION_SCHEMA
        )


def test_canonical_exception_missing_provenance_fails(tmp_path: Path) -> None:
    record = _exception_record()
    del record["source_provenance"]
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="source_provenance"):
        load_canonical_unit_exceptions(path, EXCEPTION_SCHEMA)


def test_duplicate_canonical_exception_id_fails(tmp_path: Path) -> None:
    record = _exception_record()
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record, record])
    with pytest.raises(IntegrityError, match="duplicate exception unit_id"):
        load_canonical_unit_exceptions(path, EXCEPTION_SCHEMA)


def test_s4a_000_explicit_exception_is_unresolved_and_not_insertable() -> None:
    _, verification = _repository_canonical_verification()
    resolution = verification.resolutions[0]
    assert resolution.unit["unit_id"] == "S4A-2026-000"
    assert resolution.exception is not None
    assert resolution.normalized_location is not None
    assert resolution.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
    assert not resolution.eligible_for_document_insertion
    evidence = build_translation_evidence_sources(verification, [])
    assert not evidence[0].eligible_for_document_insertion


def test_s4a_000_authority_blocker_remains() -> None:
    _, verification = _repository_canonical_verification()
    with pytest.raises(GateError, match="S4A-2026-000"):
        assert_publication_allowed(verification, [])


def test_clearing_authority_blocker_without_disposition_fails() -> None:
    units = load_source_units(UNITS_PATH)
    units[0]["translation_status"] = "AUTHORITY_RESOLVED"
    with pytest.raises(IntegrityError, match="translation_status does not match"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
        )


def test_resolved_exception_without_disposition_fails(tmp_path: Path) -> None:
    record = _exception_record()
    record.update(
        {
            "authority_status": "AUTHORITY_RESOLVED",
            "source_authority_decision_required": False,
            "evidence_status": "AUTHORITY_RESOLVED",
        }
    )
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="authority_disposition"):
        load_canonical_unit_exceptions(path, EXCEPTION_SCHEMA)


def test_valid_typed_authority_disposition_passes(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    units[0]["translation_status"] = "AUTHORITY_RESOLVED"
    record = _exception_record()
    record.update(
        {
            "authority_status": "AUTHORITY_RESOLVED",
            "source_authority_decision_required": False,
            "publication_blocking": False,
            "evidence_status": "AUTHORITY_RESOLVED",
            "authority_disposition": {
                "unit_id": "S4A-2026-000",
                "decision": "APPROVE_CANONICAL_EXCEPTION",
                "decision_maker": "Authority fixture",
                "decision_date": "2026-09-07",
                "evidence_reference": "fixture-only",
                "status": "FINAL",
            },
        }
    )
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    verification = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
    )
    assert verification.resolutions[0].eligible_for_document_insertion
    assert_publication_allowed(verification, [])


def test_exception_text_must_exist_at_verified_canonical_location(
    tmp_path: Path,
) -> None:
    record = _exception_record()
    record["source_provenance"]["paragraph_index"] = 999
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    units = load_source_units(UNITS_PATH)
    with pytest.raises(IntegrityError, match="resolve exactly one canonical DOCX"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_only_declared_normalization_methods_are_accepted(tmp_path: Path) -> None:
    record = _exception_record()
    record["source_provenance"]["normalization_method"] = "ARBITRARY_EQUIVALENCE"
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="normalization_method"):
        load_canonical_unit_exceptions(exceptions, EXCEPTION_SCHEMA)


def test_s4a_000_line_break_normalization_path_passes() -> None:
    units, verification = _repository_canonical_verification()
    resolution = verification.resolutions[0]
    assert resolution.unit == units[0]
    assert resolution.normalized_location is not None
    assert resolution.normalized_location.document_part == "word/header1.xml"
    assert resolution.normalized_location.paragraph_index == 1


def test_semantic_text_difference_cannot_be_normalized(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    units[0]["source_text_en"] += " Additional meaning."
    units[0]["source_text_sha256"] = sha256_text(units[0]["source_text_en"])
    record = _exception_for_unit(units[0], approved=False)
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="normalized canonical text does not equal"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_laundering_attack_cannot_clear_final_source_gates(tmp_path: Path) -> None:
    units, canonical = _repository_canonical_verification()
    requirements = verify_source_requirements(
        REQUIREMENTS, REQUIREMENT_SCHEMA, MANIFEST, OFFICIAL, canonical
    )
    with pytest.raises(GateError):
        assert_publication_allowed(canonical, list(requirements.requirements))
    with pytest.raises(GateError):
        assert_source_reconciliation_resolved(
            canonical, list(requirements.requirements)
        )

    liver_unit = _fabricated_liver_unit(units)
    liver_unit["translation_status"] = "AUTHORITY_RESOLVED"
    units.append(liver_unit)
    exceptions = _write_jsonl(
        tmp_path / "exceptions.jsonl",
        [_exception_record(), _exception_for_unit(liver_unit, approved=True)],
    )
    with pytest.raises(IntegrityError):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_authority_disposition_must_be_unit_linked(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    units[0]["translation_status"] = "AUTHORITY_RESOLVED"
    record = _exception_record()
    record.update(
        {
            "authority_status": "AUTHORITY_RESOLVED",
            "source_authority_decision_required": False,
            "publication_blocking": False,
            "evidence_status": "AUTHORITY_RESOLVED",
            "authority_disposition": {
                "unit_id": "S4A-2026-999",
                "decision": "APPROVE_CANONICAL_EXCEPTION",
                "decision_maker": "Authority fixture",
                "decision_date": "2026-09-07",
                "evidence_reference": "fixture-only",
                "status": "FINAL",
            },
        }
    )
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="not unit-linked"):
        verify_canonical_units_against_source(
            MANIFEST, OFFICIAL, units, exceptions, EXCEPTION_SCHEMA
        )


def test_original_source_unit_ids_and_hashes_are_unchanged() -> None:
    units = load_source_units(UNITS_PATH)
    assert sha256_file(UNITS_PATH) == SOURCE_UNITS_SHA256
    assert [unit["unit_id"] for unit in units] == [
        f"S4A-2026-{index:03d}" for index in range(53)
    ]
