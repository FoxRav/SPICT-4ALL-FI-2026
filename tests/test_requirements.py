from __future__ import annotations

import copy
import html
import json
import shutil
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from spict4all.errors import GateError, IntegrityError
from spict4all.evidence import (
    EvidenceSourceKind,
    FinalInclusionStatus,
    document_insertion_sources,
)
from spict4all.gates import (
    assert_publication_allowed,
    assert_source_reconciliation_resolved,
)
from spict4all.hashing import sha256_file, sha256_text
from spict4all.requirements import (
    CanonicalUnitVerification,
    VerifiedOfficialSource,
    build_translation_evidence_sources,
    derive_marked_change_census,
    extract_visible_paragraphs,
    load_source_requirements,
    verify_canonical_units_against_source,
    verify_change_spec_completeness,
    verify_source_requirements,
)
from spict4all.units import load_source_units

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/source_requirement.schema.json"
MANIFEST = ROOT / "sources/manifests/source_manifest.json"
OFFICIAL = ROOT / "sources/official"
REQUIREMENTS = ROOT / "data/source_requirements.jsonl"
EXCEPTIONS = ROOT / "data/canonical_unit_exceptions.jsonl"
EXCEPTION_SCHEMA = ROOT / "schemas/canonical_unit_exception.schema.json"
UNITS_PATH = ROOT / "data/source_units.jsonl"
CANONICAL = OFFICIAL / "20260521-Word-template-SPICT-4ALL-translations-2026.docx"
CHANGE_SPEC = (
    OFFICIAL / "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx"
)
CANONICAL_SHA256 = "aea5e489ffc93f57ab3666572f65044fba8375aa5dda897d0ef2988c3a9f8581"
CHANGE_SPEC_SHA256 = "0fff175b57c66f0dd45cd18c58b599758122e5285892c07da52ddf8a9130a27d"


def _record() -> dict[str, Any]:
    return json.loads(REQUIREMENTS.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def _paragraph(
    text: str,
    *,
    highlight: str | None = None,
    paragraph_mark_highlight: str | None = None,
) -> str:
    paragraph_properties = ""
    if paragraph_mark_highlight is not None:
        paragraph_properties = (
            "<w:pPr><w:rPr><w:highlight "
            f'w:val="{paragraph_mark_highlight}"/></w:rPr></w:pPr>'
        )
    run_properties = (
        f'<w:rPr><w:highlight w:val="{highlight}"/></w:rPr>'
        if highlight is not None
        else ""
    )
    return (
        f"<w:p>{paragraph_properties}<w:r>{run_properties}"
        f"<w:t>{html.escape(text)}</w:t></w:r></w:p>"
    )


def _write_docx(
    path: Path,
    document_paragraphs: list[str],
    *,
    extra_parts: dict[str, list[str]] | None = None,
) -> Path:
    namespace = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    document_xml = (
        f"<w:document {namespace}><w:body>"
        + "".join(document_paragraphs)
        + "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as document:
        document.writestr("word/document.xml", document_xml)
        for name, paragraphs in (extra_parts or {}).items():
            root_name = "hdr" if "header" in name else "ftr"
            xml = (
                f"<w:{root_name} {namespace}>"
                + "".join(paragraphs)
                + f"</w:{root_name}>"
            )
            document.writestr(name, xml)
    return path


def _write_manifest(path: Path, canonical: Path, change_spec: Path) -> Path:
    entries = [
        {
            "filename": canonical.name,
            "sha256": sha256_file(canonical),
            "bytes": canonical.stat().st_size,
            "role": "canonical_source",
            "source_url": "test fixture",
            "immutable": True,
        },
        {
            "filename": change_spec.name,
            "sha256": sha256_file(change_spec),
            "bytes": change_spec.stat().st_size,
            "role": "official_change_spec",
            "source_url": "test fixture",
            "immutable": True,
        },
    ]
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _synthetic_requirement(
    requirement_id: str,
    text: str,
    change_spec: Path,
    paragraph_index: int,
) -> dict[str, Any]:
    record = _record()
    record.update(
        {
            "requirement_id": requirement_id,
            "exact_source_text_en": text,
            "exact_text_sha256": sha256_text(text),
            "official_source_filename": change_spec.name,
            "official_source_file_sha256": sha256_file(change_spec),
            "change_year": 2025,
            "source_provenance": {
                "document_part": "word/document.xml",
                "paragraph_index": paragraph_index,
                "marking": {"type": "highlight", "value": "yellow"},
            },
        }
    )
    return record


def _repository_verification():
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    requirements = verify_source_requirements(
        REQUIREMENTS, SCHEMA, MANIFEST, OFFICIAL, canonical
    )
    return units, canonical, requirements


def _synthetic_canonical_verification(
    tmp_path: Path,
    manifest: Path,
    official: Path,
    units: list[dict[str, Any]] | None = None,
) -> CanonicalUnitVerification:
    if not units:
        canonical = official / "20260521-Word-template-SPICT-4ALL-translations-2026.docx"
        return CanonicalUnitVerification(
            canonical_source=VerifiedOfficialSource(
                filename=canonical.name,
                role="canonical_source",
                path=canonical,
                sha256=sha256_file(canonical),
                byte_count=canonical.stat().st_size,
            ),
            canonical_docx_texts=frozenset(
                text for _, text in extract_visible_paragraphs(canonical) if text
            ),
            resolutions=(),
            exceptions=(),
        )
    exceptions = _write_jsonl(tmp_path / "exceptions.jsonl", [])
    return verify_canonical_units_against_source(
        manifest,
        official,
        units or [],
        exceptions,
        EXCEPTION_SCHEMA,
    )


def test_nested_textbox_paragraphs_are_attributed_to_leaf_elements(
    tmp_path: Path,
) -> None:
    namespace = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    nested_container = (
        "<w:p>"
        "<w:r><w:drawing><w:txbxContent>"
        "<w:p><w:r><w:t>nested leaf</w:t></w:r></w:p>"
        "</w:txbxContent></w:drawing></w:r>"
        "<w:r><w:t>container own</w:t></w:r>"
        "</w:p>"
    )
    title = (
        "<w:p><w:r><w:t>Supportive and Palliative Care </w:t></w:r>"
        "<w:r><w:br/></w:r>"
        "<w:r><w:t>Indicators Tool (SPICT-4ALL-……)</w:t></w:r></w:p>"
    )
    path = tmp_path / "nested.docx"
    with zipfile.ZipFile(path, "w") as document:
        document.writestr(
            "word/document.xml",
            f"<w:document {namespace}><w:body>{nested_container}</w:body></w:document>",
        )
        document.writestr("word/header1.xml", f"<w:hdr {namespace}>{title}</w:hdr>")
    paragraphs = extract_visible_paragraphs(path)
    texts = [text for _, text in paragraphs]
    assert "nested leaf" in texts
    assert "container own" in texts
    assert all("nested leafcontainer own" not in text for text in texts)
    assert all("nested leaf container own" not in text for text in texts)
    header_texts = [
        text
        for location, text in paragraphs
        if location.document_part == "word/header1.xml"
    ]
    assert header_texts == [
        "Supportive and Palliative Care \nIndicators Tool (SPICT-4ALL-……)"
    ]


def test_current_change_spec_marker_census_passes() -> None:
    units, _, verification = _repository_verification()
    census = verification.completeness.census
    assert len(units) == 53
    assert census.yellow_highlighted_runs == 32
    assert census.green_highlighted_runs == 4
    assert census.accent6_font_runs == 1
    assert len(census.marked_paragraphs) == 18
    assert verification.completeness.absent_from_canonical == (
        "A liver transplant is not possible.",
    )


def test_valid_source_requirement_passes() -> None:
    _, _, verification = _repository_verification()
    assert [item.requirement_id for item in verification.requirements] == [
        "S4A-REQ-2026-001"
    ]


def test_duplicate_requirement_id_fails(tmp_path: Path) -> None:
    record = _record()
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record, record])
    with pytest.raises(IntegrityError, match="duplicate requirement_id"):
        load_source_requirements(path, SCHEMA)


def test_mutated_requirement_source_text_fails(tmp_path: Path) -> None:
    record = _record()
    record["exact_source_text_en"] = "Mutated source text."
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="exact-text hash mismatch"):
        load_source_requirements(path, SCHEMA)


def test_mutated_source_text_with_matching_hash_fails_official_verification(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    record = _record()
    record["exact_source_text_en"] = "Mutated source text."
    record["exact_text_sha256"] = sha256_text(record["exact_source_text_en"])
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="exact requirement text not found"):
        verify_source_requirements(path, SCHEMA, MANIFEST, OFFICIAL, canonical)


def test_mutated_requirement_text_hash_fails(tmp_path: Path) -> None:
    record = _record()
    record["exact_text_sha256"] = "0" * 64
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="exact-text hash mismatch"):
        load_source_requirements(path, SCHEMA)


def test_missing_official_source_linkage_fails(tmp_path: Path) -> None:
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    record = _record()
    record["official_source_filename"] = "missing-official-source.docx"
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="official_change_spec"):
        verify_source_requirements(path, SCHEMA, MANIFEST, OFFICIAL, canonical)


def test_missing_required_provenance_fails(tmp_path: Path) -> None:
    record = _record()
    del record["source_provenance"]
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="source_provenance"):
        load_source_requirements(path, SCHEMA)


def test_invalid_source_file_sha256_fails(tmp_path: Path) -> None:
    record = _record()
    record["official_source_file_sha256"] = "invalid"
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="official_source_file_sha256"):
        load_source_requirements(path, SCHEMA)


def test_invalid_final_inclusion_state_fails(tmp_path: Path) -> None:
    record = _record()
    record["final_inclusion_status"] = "SILENTLY_INCLUDED"
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="final_inclusion_status"):
        load_source_requirements(path, SCHEMA)


def test_disappearing_known_requirement_fails_source_derived_completeness(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    path = _write_jsonl(tmp_path / "requirements.jsonl", [])
    with pytest.raises(IntegrityError, match="A liver transplant is not possible"):
        verify_source_requirements(path, SCHEMA, MANIFEST, OFFICIAL, canonical)


def test_undiscovered_marked_paragraph_fails(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    canonical = _write_docx(official / "20260521-Word-template-SPICT-4ALL-translations-2026.docx", [])
    change_spec = _write_docx(
        official / "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx",
        [_paragraph("Undiscovered official change", highlight="yellow")],
    )
    manifest = _write_manifest(tmp_path / "manifest.json", canonical, change_spec)
    canonical_verification = _synthetic_canonical_verification(
        tmp_path, manifest, official
    )
    with pytest.raises(IntegrityError, match="Undiscovered official change"):
        verify_change_spec_completeness(
            manifest, official, canonical_verification, []
        )


def test_legitimate_additional_requirements_need_no_python_allow_list(
    tmp_path: Path,
) -> None:
    official = tmp_path / "official"
    official.mkdir()
    canonical = _write_docx(official / "20260521-Word-template-SPICT-4ALL-translations-2026.docx", [])
    change_spec = _write_docx(
        official / "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx",
        [
            _paragraph("First additional requirement", highlight="yellow"),
            _paragraph("Second additional requirement", highlight="yellow"),
        ],
    )
    manifest = _write_manifest(tmp_path / "manifest.json", canonical, change_spec)
    records = [
        _synthetic_requirement(
            "S4A-REQ-2025-101", "First additional requirement", change_spec, 0
        ),
        _synthetic_requirement(
            "S4A-REQ-2025-102", "Second additional requirement", change_spec, 1
        ),
    ]
    requirements = _write_jsonl(tmp_path / "requirements.jsonl", records)
    canonical_verification = _synthetic_canonical_verification(
        tmp_path, manifest, official
    )
    verification = verify_source_requirements(
        requirements, SCHEMA, manifest, official, canonical_verification
    )
    assert len(verification.requirements) == 2


def test_corrupted_canonical_template_fails_before_presence_scan(
    tmp_path: Path,
) -> None:
    official = tmp_path / "official"
    shutil.copytree(OFFICIAL, official)
    canonical = official / CANONICAL.name
    canonical.write_bytes(b"corrupted replacement")
    units = load_source_units(UNITS_PATH)
    with pytest.raises(IntegrityError, match="Official canonical_source verification failed"):
        verify_canonical_units_against_source(
            MANIFEST, official, units, EXCEPTIONS, EXCEPTION_SCHEMA
        )


def test_canonical_text_in_header_is_detected(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    text = "Canonical header source"
    canonical = _write_docx(
        official / "20260521-Word-template-SPICT-4ALL-translations-2026.docx",
        [],
        extra_parts={"word/header1.xml": [_paragraph(text)]},
    )
    change_spec = _write_docx(
        official / "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx", [_paragraph(text, highlight="green")]
    )
    manifest = _write_manifest(tmp_path / "manifest.json", canonical, change_spec)
    canonical_verification = _synthetic_canonical_verification(
        tmp_path, manifest, official
    )
    result = verify_change_spec_completeness(
        manifest, official, canonical_verification, []
    )
    assert result.absent_from_canonical == ()


def test_invisible_paragraph_mark_formatting_cannot_satisfy_marking(
    tmp_path: Path,
) -> None:
    official = tmp_path / "official"
    official.mkdir()
    text = "Not visibly marked"
    canonical = _write_docx(official / "20260521-Word-template-SPICT-4ALL-translations-2026.docx", [])
    change_spec = _write_docx(
        official / "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx",
        [_paragraph(text, paragraph_mark_highlight="yellow")],
    )
    manifest = _write_manifest(tmp_path / "manifest.json", canonical, change_spec)
    assert derive_marked_change_census(change_spec).marked_paragraphs == ()
    record = _synthetic_requirement(
        "S4A-REQ-2025-101", text, change_spec, 0
    )
    requirements = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    canonical_verification = _synthetic_canonical_verification(
        tmp_path, manifest, official
    )
    with pytest.raises(IntegrityError, match="marked official source location not found"):
        verify_source_requirements(
            requirements, SCHEMA, manifest, official, canonical_verification
        )


def test_unresolved_publication_blocking_true_passes() -> None:
    assert len(load_source_requirements(REQUIREMENTS, SCHEMA)) == 1


def test_source_requirement_change_year_2025_passes(tmp_path: Path) -> None:
    record = _record()
    record["change_year"] = 2025
    record["source_provenance"]["marking"] = {
        "type": "highlight",
        "value": "yellow",
    }
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    assert len(load_source_requirements(path, SCHEMA)) == 1


def test_source_requirement_change_year_2026_passes() -> None:
    assert load_source_requirements(REQUIREMENTS, SCHEMA)[0].change_year == 2026


def test_unsupported_source_requirement_change_year_fails(
    tmp_path: Path,
) -> None:
    record = _record()
    record["change_year"] = 2024
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="change_year"):
        load_source_requirements(path, SCHEMA)


def test_unresolved_publication_blocking_false_fails(tmp_path: Path) -> None:
    record = _record()
    record["publication_blocking"] = False
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match="publication_blocking"):
        load_source_requirements(path, SCHEMA)


def test_unresolved_publication_blocker_is_enforced_by_domain_model() -> None:
    requirement = load_source_requirements(REQUIREMENTS, SCHEMA)[0]
    with pytest.raises(IntegrityError, match="publication-blocking"):
        replace(requirement, publication_blocking=False)


def test_resolved_authority_disposition_path_can_downgrade_blocker(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    record = _record()
    record.update(
        {
            "conflict_status": "AUTHORITY_RESOLVED",
            "final_inclusion_status": "INCLUDE",
            "publication_blocking": False,
            "source_authority_confirmation_required": False,
            "authority_disposition": {
                "requirement_id": "S4A-REQ-2026-001",
                "decision": "INCLUDE_IN_FINAL_SOURCE",
                "status": "FINAL",
                "decision_maker": "Source authority fixture",
                "decision_date": "2026-09-07",
                "evidence_reference": "fixture-only",
            },
        }
    )
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    verification = verify_source_requirements(
        path, SCHEMA, MANIFEST, OFFICIAL, canonical
    )
    evidence = build_translation_evidence_sources(
        canonical, verification.requirements
    )
    requirement_source = evidence[-1]
    assert requirement_source.final_inclusion_status is FinalInclusionStatus.INCLUDE
    assert requirement_source.eligible_for_document_insertion


@pytest.mark.parametrize(
    "missing_field",
    [
        "requirement_id",
        "decision",
        "status",
        "decision_maker",
        "decision_date",
        "evidence_reference",
    ],
)
def test_requirement_authority_disposition_requires_typed_fields(
    tmp_path: Path,
    missing_field: str,
) -> None:
    record = _record()
    disposition = {
        "requirement_id": "S4A-REQ-2026-001",
        "decision": "INCLUDE_IN_FINAL_SOURCE",
        "status": "FINAL",
        "decision_maker": "Source authority fixture",
        "decision_date": "2026-09-07",
        "evidence_reference": "fixture-only",
    }
    del disposition[missing_field]
    record.update(
        {
            "conflict_status": "AUTHORITY_RESOLVED",
            "final_inclusion_status": "INCLUDE",
            "publication_blocking": False,
            "source_authority_confirmation_required": False,
            "authority_disposition": disposition,
        }
    )
    path = _write_jsonl(tmp_path / "requirements.jsonl", [record])
    with pytest.raises(IntegrityError, match=missing_field):
        load_source_requirements(path, SCHEMA)


def test_duplicate_requirements_for_same_absent_marked_paragraph_fail(
    tmp_path: Path,
) -> None:
    units = load_source_units(UNITS_PATH)
    canonical = verify_canonical_units_against_source(
        MANIFEST, OFFICIAL, units, EXCEPTIONS, EXCEPTION_SCHEMA
    )
    first = _record()
    second = copy.deepcopy(first)
    second["requirement_id"] = "S4A-REQ-2026-002"
    requirements = _write_jsonl(tmp_path / "requirements.jsonl", [first, second])
    with pytest.raises(IntegrityError, match="expected exactly one"):
        verify_source_requirements(
            requirements, SCHEMA, MANIFEST, OFFICIAL, canonical
        )


def test_exact_change_spec_text_is_found_and_official_sources_unchanged() -> None:
    before_canonical = sha256_file(CANONICAL)
    before_change_spec = sha256_file(CHANGE_SPEC)
    _repository_verification()
    assert sha256_file(CANONICAL) == before_canonical == CANONICAL_SHA256
    assert sha256_file(CHANGE_SPEC) == before_change_spec == CHANGE_SPEC_SHA256


def test_typed_evidence_source_document_eligibility() -> None:
    _, canonical, verification = _repository_verification()
    sources = build_translation_evidence_sources(
        canonical, verification.requirements
    )
    assert len(sources) == 54
    assert sources[0].source_kind is EvidenceSourceKind.CANONICAL_SOURCE_UNIT
    assert not sources[0].eligible_for_document_insertion
    assert sources[1].eligible_for_document_insertion
    assert (
        sources[-1].source_kind
        is EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT
    )
    assert not sources[-1].eligible_for_document_insertion
    assert sources[-1] not in document_insertion_sources(sources)


def test_unresolved_requirement_cannot_be_made_docx_insertable() -> None:
    _, canonical, verification = _repository_verification()
    requirement_source = build_translation_evidence_sources(
        canonical, verification.requirements
    )[-1]
    with pytest.raises(ValueError, match="cannot be document-insertable"):
        replace(requirement_source, eligible_for_document_insertion=True)


def test_invalid_evidence_source_kind_fails() -> None:
    _, canonical, verification = _repository_verification()
    canonical_source = build_translation_evidence_sources(
        canonical, verification.requirements
    )[0]
    with pytest.raises(ValueError, match="Invalid source_kind"):
        replace(canonical_source, source_kind="invalid")  # type: ignore[arg-type]


def test_unresolved_conflict_blocks_reconciliation_and_publication() -> None:
    _, canonical, verification = _repository_verification()
    requirements = list(verification.requirements)
    with pytest.raises(GateError, match="S4A-REQ-2026-001"):
        assert_source_reconciliation_resolved(canonical, requirements)
    with pytest.raises(GateError, match="S4A-REQ-2026-001"):
        assert_publication_allowed(canonical, requirements)
