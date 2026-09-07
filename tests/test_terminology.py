from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from spict4all.errors import IntegrityError
from spict4all.hashing import sha256_file
from spict4all.requirements import verify_canonical_units_against_source
from spict4all.sources import require_verified_sources
from spict4all.terminology import (
    DetectedFileType,
    ExtractedTerm,
    MetadataField,
    ProvenanceStatus,
    _csv_terms,
    build_relevance_rows,
    derive_conflicts,
    extract_terminology,
    load_glossary,
    load_terminology_sources,
    validate_extracted_terms,
    validate_glossary,
    validate_terminology_evidence,
    verify_terminology_sources,
)
from spict4all.units import load_source_units

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "terminology/sources/terminology_source_manifest.json"
MANIFEST_SCHEMA = ROOT / "schemas/terminology_source_manifest.schema.json"
RULES = ROOT / "terminology/sources/pdf_extraction_rules.json"
RULE_SCHEMA = ROOT / "schemas/terminology_pdf_extraction_rule.schema.json"
EXTRACTED_SCHEMA = ROOT / "schemas/terminology_extracted_entry.schema.json"


def _sources_and_records():
    sources = verify_terminology_sources(ROOT, MANIFEST, MANIFEST_SCHEMA)
    records = extract_terminology(ROOT, sources, RULES, RULE_SCHEMA)
    return sources, records


def test_terminology_source_hashes_are_deterministic() -> None:
    sources = verify_terminology_sources(ROOT, MANIFEST, MANIFEST_SCHEMA)
    assert len(sources) == 5
    for source in sources:
        path = ROOT / "data/Sanasto" / source.filename
        assert sha256_file(path) == source.sha256
        assert path.stat().st_size == source.byte_count


def test_duplicate_terminology_source_record_fails(tmp_path: Path) -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    value["sources"].append(copy.deepcopy(value["sources"][0]))
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="duplicate source IDs"):
        load_terminology_sources(path, MANIFEST_SCHEMA)


def test_terminology_source_verified_metadata_object_is_required(
    tmp_path: Path,
) -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    del value["sources"][0]["source_verified_metadata"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="source_verified_metadata"):
        load_terminology_sources(path, MANIFEST_SCHEMA)


def test_terminology_source_cannot_claim_canonical_role(tmp_path: Path) -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    value["sources"][0]["terminology_role"] = "CANONICAL_SOURCE"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(IntegrityError, match="TERMINOLOGY_REFERENCE"):
        load_terminology_sources(path, MANIFEST_SCHEMA)


def test_extracted_term_cannot_claim_inferred_english_as_source_text() -> None:
    _, records = _sources_and_records()
    record = copy.deepcopy(records[0])
    record["term_en"] = "fabricated English equivalent"
    record["term_en_origin"] = "SOURCE_EXPLICIT"
    record["source_provided_fields"].append("term_en")
    with pytest.raises(IntegrityError, match="absent from source fragment"):
        validate_extracted_terms([record], EXTRACTED_SCHEMA)


def test_unapproved_term_cannot_enter_mandatory_glossary() -> None:
    rows = load_glossary(ROOT / "terminology/terms.csv")
    rows[0]["approved_fi"] = "fixture-only"
    with pytest.raises(IntegrityError, match="unapproved terminology"):
        validate_glossary(rows)


def test_terminology_conflict_is_preserved() -> None:
    _, records = _sources_and_records()
    first = copy.deepcopy(records[0])
    second = copy.deepcopy(records[1])
    first["term_en"] = second["term_en"] = "shared explicit concept"
    first["term_en_origin"] = second["term_en_origin"] = "SOURCE_EXPLICIT"
    first["term_fi"] = "source candidate one"
    second["term_fi"] = "source candidate two"
    conflicts = derive_conflicts([first, second])
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "HUMAN_REVIEW_REQUIRED"


def test_relevance_map_allows_zero_and_flags_ambiguous_matches(make_unit) -> None:
    unit = make_unit(text="A shared explicit concept appears here.")
    _, records = _sources_and_records()
    no_match = copy.deepcopy(records[0])
    no_match["term_en"] = None
    assert build_relevance_rows([unit], [no_match], []) == []

    candidates: list[ExtractedTerm] = []
    for index, term_fi in enumerate(("candidate one", "candidate two")):
        candidate = copy.deepcopy(records[index])
        candidate["term_en"] = "shared explicit concept"
        candidate["term_en_origin"] = "SOURCE_EXPLICIT"
        candidate["term_fi"] = term_fi
        candidates.append(candidate)
    conflicts = derive_conflicts(candidates)
    rows = build_relevance_rows([unit], candidates, conflicts)
    assert len(rows) == 2
    assert {row["confidence"] for row in rows} == {"AMBIGUOUS"}
    assert {row["human_review_required"] for row in rows} == {"true"}


def test_terminology_validation_cannot_expand_canonical_english_corpus() -> None:
    units = load_source_units(ROOT / "data/source_units.jsonl")
    before = verify_canonical_units_against_source(
        ROOT / "sources/manifests/source_manifest.json",
        ROOT / "sources/official",
        units,
        ROOT / "data/canonical_unit_exceptions.jsonl",
        ROOT / "schemas/canonical_unit_exception.schema.json",
    ).canonical_docx_texts
    result = validate_terminology_evidence(ROOT)
    after = verify_canonical_units_against_source(
        ROOT / "sources/manifests/source_manifest.json",
        ROOT / "sources/official",
        units,
        ROOT / "data/canonical_unit_exceptions.jsonl",
        ROOT / "schemas/canonical_unit_exception.schema.json",
    ).canonical_docx_texts
    assert before == after
    assert result.source_count == 5
    assert result.extracted_count == 136
    assert result.source_provided_english_count == 41
    assert result.approved_count == 0
    assert result.relevance_count == 0


def _write_mutated_manifest(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
) -> Path:
    loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise AssertionError("terminology source manifest must be an object")
    value = cast(dict[str, object], loaded)
    mutate(value)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def test_fabricated_publisher_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        first = sources[0]
        assert isinstance(first, dict)
        metadata = first["source_verified_metadata"]
        assert isinstance(metadata, dict)
        publisher = metadata["publisher_organisation"]
        assert isinstance(publisher, dict)
        publisher["value"] = "Fabricated Publisher Ltd"

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="publisher_organisation"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_fabricated_publication_date_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        first = sources[0]
        assert isinstance(first, dict)
        metadata = first["source_verified_metadata"]
        assert isinstance(metadata, dict)
        date_value = metadata["publication_version_date"]
        assert isinstance(date_value, dict)
        date_value["value"] = "2099-01-01"

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="publication_version_date"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_fabricated_title_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        first = sources[0]
        assert isinstance(first, dict)
        metadata = first["source_verified_metadata"]
        assert isinstance(metadata, dict)
        title = metadata["title"]
        assert isinstance(title, dict)
        title["value"] = "Fabricated Title"

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="title"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_fabricated_url_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        first = sources[0]
        assert isinstance(first, dict)
        metadata = first["source_verified_metadata"]
        assert isinstance(metadata, dict)
        url = metadata["source_url"]
        assert isinstance(url, dict)
        url["value"] = "https://example.invalid/fabricated"

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="source_url"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_fabricated_licence_status_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        csv_source = sources[3]
        assert isinstance(csv_source, dict)
        inferred = csv_source["project_inferred_metadata"]
        assert isinstance(inferred, dict)
        inferred["licence_reuse_status"] = (
            "COPYRIGHT_NOTICE_NO_REUSE_TERMS_IDENTIFIED"
        )

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="copyright-based licence status"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_metadata_populated_while_unresolved_says_absent_fails(
    tmp_path: Path,
) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        first = sources[0]
        assert isinstance(first, dict)
        unresolved = first["unresolved_metadata"]
        assert isinstance(unresolved, list)
        unresolved.append(
            {
                "field": "publisher_organisation",
                "reason": "claimed absent while also populated",
            }
        )

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="both source-verified and unresolved"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_upgraded_provenance_status_without_evidence_fails(tmp_path: Path) -> None:
    def mutate(value: dict[str, object]) -> None:
        sources = value["sources"]
        assert isinstance(sources, list)
        csv_source = sources[3]
        assert isinstance(csv_source, dict)
        inferred = csv_source["project_inferred_metadata"]
        assert isinstance(inferred, dict)
        inferred["provenance_status"] = "CONTENT_AND_FILE_VERIFIED_METADATA_PARTIAL"

    path = _write_mutated_manifest(tmp_path, mutate)
    with pytest.raises(IntegrityError, match="content-verified provenance"):
        verify_terminology_sources(ROOT, path, MANIFEST_SCHEMA)


def test_current_honest_terminology_metadata_passes() -> None:
    sources = verify_terminology_sources(ROOT, MANIFEST, MANIFEST_SCHEMA)
    assert len(sources) == 5
    pdf_sources = [
        source
        for source in sources
        if source.detected_file_type is DetectedFileType.PDF
    ]
    csv_sources = [
        source
        for source in sources
        if source.detected_file_type is DetectedFileType.CSV_SEMICOLON_UTF8
    ]
    assert len(pdf_sources) == 3
    assert len(csv_sources) == 2
    assert all(source.title for source in pdf_sources)
    assert all(source.publisher_organisation for source in pdf_sources)
    assert all(
        source.project_inferred_metadata.provenance_status
        is ProvenanceStatus.CONTENT_AND_FILE_VERIFIED_METADATA_PARTIAL
        for source in pdf_sources
    )


def test_unknown_terminology_metadata_is_represented_explicitly() -> None:
    sources = verify_terminology_sources(ROOT, MANIFEST, MANIFEST_SCHEMA)
    csv_sources = [
        source
        for source in sources
        if source.detected_file_type is DetectedFileType.CSV_SEMICOLON_UTF8
    ]
    assert csv_sources
    for source in csv_sources:
        assert source.publisher_organisation is None
        assert source.publication_version_date is None
        assert source.source_url is None
        assert MetadataField.PUBLISHER_ORGANISATION in source.unresolved_fields
        assert MetadataField.PUBLICATION_VERSION_DATE in source.unresolved_fields
        assert MetadataField.SOURCE_URL in source.unresolved_fields
        assert MetadataField.LICENCE_REUSE_TERMS in source.unresolved_fields
        assert source.project_inferred_metadata.provenance_status is (
            ProvenanceStatus.FILE_VERIFIED_METADATA_UNRESOLVED
        )


def test_csv_extraction_uses_declared_non_entry_rows_not_magic_numbers() -> None:
    sources, records = _sources_and_records()
    csv_sources = [
        source
        for source in sources
        if source.detected_file_type is DetectedFileType.CSV_SEMICOLON_UTF8
    ]
    assert len(csv_sources) == 2
    for source in csv_sources:
        structure = source.file_facts.csv_structure
        assert structure is not None
        assert 2 in structure.non_entry_row_numbers
        extracted = [record for record in records if record["source_id"] == source.source_id]
        extracted_rows = {
            record["source_location"]["number"] for record in extracted
        }
        assert extracted_rows.isdisjoint(structure.non_entry_row_numbers)
        assert all(record["term_fi"] != "Suositettava termi" for record in extracted)


def test_csv_label_row_is_extracted_only_when_declared_as_an_entry() -> None:
    sources, _ = _sources_and_records()
    source = next(
        item
        for item in sources
        if item.source_id == "TERM-SRC-004"
    )
    structure = source.file_facts.csv_structure
    assert structure is not None
    remaining = tuple(item for item in structure.non_entry_rows if item.row != 2)
    mutated = replace(
        source,
        file_facts=replace(
            source.file_facts,
            csv_structure=replace(structure, non_entry_rows=remaining),
        ),
    )
    terms = _csv_terms(ROOT / "data/Sanasto" / source.filename, mutated)
    label_rows = [
        term for term in terms if term["source_location"]["number"] == 2
    ]
    assert label_rows
    assert label_rows[0]["term_fi"] == "Suositettava termi"


def test_validate_terminology_does_not_own_official_source_integrity(
    tmp_path: Path,
) -> None:
    result = validate_terminology_evidence(ROOT)
    assert result.approved_count == 0
    official = tmp_path / "official"
    shutil.copytree(ROOT / "sources/official", official)
    (official / "rogue-unmanifested.docx").write_bytes(b"rogue")
    with pytest.raises(IntegrityError, match="unmanifested official files"):
        require_verified_sources(
            ROOT / "sources/manifests/source_manifest.json", official
        )

