"""Non-blank authority attribution for requirements and canonical exceptions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from spict4all.authority import (
    CanonicalAuthorityDecision,
    CanonicalAuthorityDisposition,
    RequirementAuthorityDecision,
    RequirementAuthorityDisposition,
)
from spict4all.errors import GateError, IntegrityError
from spict4all.evidence import FinalInclusionStatus
from spict4all.gates import assert_publication_allowed
from spict4all.requirements import (
    CanonicalUnitException,
    SourceRequirement,
    build_translation_evidence_sources,
    load_canonical_unit_exceptions,
    load_source_requirements,
    requirement_identity_summary,
    verify_canonical_units_against_source,
    verify_source_requirements,
)
from spict4all.units import load_source_units

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "data/source_requirements.jsonl"
REQUIREMENT_SCHEMA = ROOT / "schemas/source_requirement.schema.json"
EXCEPTIONS = ROOT / "data/canonical_unit_exceptions.jsonl"
EXCEPTION_SCHEMA = ROOT / "schemas/canonical_unit_exception.schema.json"
UNITS_PATH = ROOT / "data/source_units.jsonl"
MANIFEST = ROOT / "sources/manifests/source_manifest.json"
OFFICIAL = ROOT / "sources/official"

BLANK_ATTRIBUTION_CASES = (
    ("decision_maker", "", "decision_maker"),
    ("decision_maker", " ", "decision_maker"),
    ("evidence_reference", "", "evidence_reference"),
    ("evidence_reference", "\t", "evidence_reference"),
    ("evidence_reference", "\n", "evidence_reference"),
    ("decision_date", "", "decision_date"),
)


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def _requirement_record() -> dict[str, Any]:
    return json.loads(REQUIREMENTS.read_text(encoding="utf-8"))


def _exception_record() -> dict[str, Any]:
    return json.loads(EXCEPTIONS.read_text(encoding="utf-8"))


def _resolved_requirement(decision: str) -> dict[str, Any]:
    record = _requirement_record()
    inclusion = "INCLUDE" if decision == "INCLUDE_IN_FINAL_SOURCE" else "EXCLUDE"
    record.update(
        {
            "conflict_status": "AUTHORITY_RESOLVED",
            "final_inclusion_status": inclusion,
            "publication_blocking": False,
            "source_authority_confirmation_required": False,
            "authority_disposition": {
                "requirement_id": record["requirement_id"],
                "decision": decision,
                "status": "FINAL",
                "decision_maker": "Source authority fixture",
                "decision_date": "2026-09-07",
                "evidence_reference": "fixture-only authority evidence",
            },
        }
    )
    return record


def _resolved_exception(decision: str) -> dict[str, Any]:
    record = _exception_record()
    record.update(
        {
            "authority_status": "AUTHORITY_RESOLVED",
            "source_authority_decision_required": False,
            "publication_blocking": False,
            "evidence_status": "AUTHORITY_RESOLVED",
            "authority_disposition": {
                "unit_id": record["unit_id"],
                "decision": decision,
                "decision_maker": "Canonical authority fixture",
                "decision_date": "2026-09-07",
                "evidence_reference": "fixture-only authority evidence",
                "status": "FINAL",
            },
        }
    )
    return record


def _repository_state():
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    requirements = verify_source_requirements(
        REQUIREMENTS, REQUIREMENT_SCHEMA, MANIFEST, OFFICIAL, canonical
    )
    return units, canonical, requirements


@pytest.mark.parametrize("decision", ["INCLUDE_IN_FINAL_SOURCE", "EXCLUDE_FROM_FINAL_SOURCE"])
@pytest.mark.parametrize("field,value,match", BLANK_ATTRIBUTION_CASES)
def test_requirement_disposition_rejects_blank_attribution_fields(
    tmp_path: Path,
    decision: str,
    field: str,
    value: str,
    match: str,
) -> None:
    record = _resolved_requirement(decision)
    record["authority_disposition"][field] = value
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match=match):
        load_source_requirements(path, REQUIREMENT_SCHEMA)


@pytest.mark.parametrize("decision", ["INCLUDE_IN_FINAL_SOURCE", "EXCLUDE_FROM_FINAL_SOURCE"])
@pytest.mark.parametrize("field,value,match", BLANK_ATTRIBUTION_CASES)
def test_requirement_disposition_domain_model_rejects_blank_attribution(
    decision: str,
    field: str,
    value: str,
    match: str,
) -> None:
    kwargs = {
        "requirement_id": "S4A-REQ-2026-001",
        "decision": RequirementAuthorityDecision(decision),
        "status": "FINAL",
        "decision_maker": "Source authority fixture",
        "decision_date": "2026-09-07",
        "evidence_reference": "fixture-only authority evidence",
        field: value,
    }
    with pytest.raises(IntegrityError, match=match):
        RequirementAuthorityDisposition(**kwargs)


@pytest.mark.parametrize("decision", ["INCLUDE_IN_FINAL_SOURCE", "EXCLUDE_FROM_FINAL_SOURCE"])
def test_valid_requirement_authority_disposition_passes(
    tmp_path: Path,
    decision: str,
) -> None:
    _, canonical, _live = _repository_state()
    record = _resolved_requirement(decision)
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    verification = verify_source_requirements(
        path, REQUIREMENT_SCHEMA, MANIFEST, OFFICIAL, canonical
    )
    requirement = verification.requirements[0]
    assert requirement.authority_disposition is not None
    evidence = build_translation_evidence_sources(canonical, verification.requirements)
    requirement_source = evidence[-1]
    if decision == "INCLUDE_IN_FINAL_SOURCE":
        assert requirement.final_inclusion_status is FinalInclusionStatus.INCLUDE
        assert requirement_source.eligible_for_document_insertion
    else:
        assert requirement.final_inclusion_status is FinalInclusionStatus.EXCLUDE
        assert not requirement_source.eligible_for_document_insertion


def test_whitespace_requirement_disposition_cannot_clear_publication_blocker(
    tmp_path: Path,
) -> None:
    record = _resolved_requirement("INCLUDE_IN_FINAL_SOURCE")
    record["authority_disposition"]["decision_maker"] = " "
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="decision_maker"):
        load_source_requirements(path, REQUIREMENT_SCHEMA)
    _, canonical, verification = _repository_state()
    with pytest.raises(GateError, match=verification.requirements[0].requirement_id):
        assert_publication_allowed(canonical, list(verification.requirements))


def test_whitespace_requirement_disposition_cannot_make_requirement_insertable(
    tmp_path: Path,
) -> None:
    record = _resolved_requirement("INCLUDE_IN_FINAL_SOURCE")
    record["authority_disposition"]["evidence_reference"] = "\t"
    with pytest.raises(IntegrityError, match="evidence_reference"):
        SourceRequirement.from_record(record)
    _, canonical, verification = _repository_state()
    evidence = build_translation_evidence_sources(canonical, verification.requirements)
    assert not evidence[-1].eligible_for_document_insertion


def test_whitespace_requirement_disposition_cannot_exclude_requirement() -> None:
    record = _resolved_requirement("EXCLUDE_FROM_FINAL_SOURCE")
    record["authority_disposition"]["decision_maker"] = "\n"
    with pytest.raises(IntegrityError, match="decision_maker"):
        SourceRequirement.from_record(record)
    _, _, verification = _repository_state()
    assert verification.requirements[0].final_inclusion_status is (
        FinalInclusionStatus.UNRESOLVED
    )


@pytest.mark.parametrize(
    "decision",
    ["APPROVE_CANONICAL_EXCEPTION", "REJECT_CANONICAL_EXCEPTION"],
)
@pytest.mark.parametrize("field,value,match", BLANK_ATTRIBUTION_CASES)
def test_canonical_disposition_rejects_blank_attribution_fields(
    tmp_path: Path,
    decision: str,
    field: str,
    value: str,
    match: str,
) -> None:
    record = _resolved_exception(decision)
    record["authority_disposition"][field] = value
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match=match):
        load_canonical_unit_exceptions(path, EXCEPTION_SCHEMA)


@pytest.mark.parametrize(
    "decision",
    ["APPROVE_CANONICAL_EXCEPTION", "REJECT_CANONICAL_EXCEPTION"],
)
@pytest.mark.parametrize("field,value,match", BLANK_ATTRIBUTION_CASES)
def test_canonical_disposition_domain_model_rejects_blank_attribution(
    decision: str,
    field: str,
    value: str,
    match: str,
) -> None:
    kwargs = {
        "unit_id": "S4A-2026-000",
        "decision": CanonicalAuthorityDecision(decision),
        "decision_maker": "Canonical authority fixture",
        "decision_date": "2026-09-07",
        "evidence_reference": "fixture-only authority evidence",
        "status": "FINAL",
        field: value,
    }
    with pytest.raises(IntegrityError, match=match):
        CanonicalAuthorityDisposition(**kwargs)


@pytest.mark.parametrize(
    "decision",
    ["APPROVE_CANONICAL_EXCEPTION", "REJECT_CANONICAL_EXCEPTION"],
)
def test_valid_canonical_authority_disposition_passes(
    tmp_path: Path,
    decision: str,
) -> None:
    units = load_source_units(UNITS_PATH)
    units[0]["translation_status"] = "AUTHORITY_RESOLVED"
    record = _resolved_exception(decision)
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    verification = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, path, EXCEPTION_SCHEMA
    )
    resolution = verification.resolutions[0]
    assert resolution.exception is not None
    assert resolution.exception.authority_disposition is not None
    if decision == "APPROVE_CANONICAL_EXCEPTION":
        assert resolution.eligible_for_document_insertion
        assert resolution.final_inclusion_status is FinalInclusionStatus.INCLUDE
    else:
        assert not resolution.eligible_for_document_insertion
        assert resolution.final_inclusion_status is FinalInclusionStatus.EXCLUDE


def test_whitespace_canonical_disposition_cannot_clear_publication_blocker(
    tmp_path: Path,
) -> None:
    record = _resolved_exception("APPROVE_CANONICAL_EXCEPTION")
    record["authority_disposition"]["decision_maker"] = " "
    path = _write_jsonl(tmp_path / "exceptions.jsonl", [record])
    with pytest.raises(IntegrityError, match="decision_maker"):
        load_canonical_unit_exceptions(path, EXCEPTION_SCHEMA)
    _, canonical, verification = _repository_state()
    with pytest.raises(GateError, match="S4A-2026-000"):
        assert_publication_allowed(canonical, list(verification.requirements))


def test_whitespace_canonical_disposition_cannot_make_unit_insertable() -> None:
    record = _resolved_exception("APPROVE_CANONICAL_EXCEPTION")
    record["authority_disposition"]["evidence_reference"] = "\t\n"
    with pytest.raises(IntegrityError, match="evidence_reference"):
        CanonicalUnitException.from_record(record)
    _, canonical, _ = _repository_state()
    evidence = build_translation_evidence_sources(canonical, [])
    assert evidence[0].evidence_id == "S4A-2026-000"
    assert not evidence[0].eligible_for_document_insertion


def test_whitespace_canonical_disposition_cannot_exclude_exception() -> None:
    record = _resolved_exception("REJECT_CANONICAL_EXCEPTION")
    record["authority_disposition"]["decision_date"] = ""
    with pytest.raises(IntegrityError, match="decision_date"):
        CanonicalUnitException.from_record(record)
    _, canonical, _ = _repository_state()
    assert canonical.resolutions[0].final_inclusion_status is (
        FinalInclusionStatus.UNRESOLVED
    )


def test_requirement_identity_summary_is_derived_from_loaded_data() -> None:
    requirements = load_source_requirements(REQUIREMENTS, REQUIREMENT_SCHEMA)
    derived = ",".join(item.requirement_id for item in requirements)
    assert requirement_identity_summary(requirements) == f"requirement_ids={derived}"
    assert requirement_identity_summary(()) == "requirement_ids=(none; derived from data)"
