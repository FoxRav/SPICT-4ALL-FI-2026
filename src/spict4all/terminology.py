"""Provenance-controlled extraction and validation of terminology evidence.

Terminology source metadata is split into four kinds that never blend:
verifiable file facts, source-verified metadata bound to a machine-checkable
location inside the registered file, explicitly unresolved metadata, and
project-inferred assessment. Every source-verified value is re-derived from the
file itself, so a claimed publisher, date, title, URL or copyright notice cannot
be asserted without evidence, and nothing is inferred from a filename.

This module owns terminology evidence only. Official SPICT source integrity,
including rejection of unmanifested files under ``sources/official/``, belongs to
``spict4all.sources`` and the ``verify-sources`` command.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict, cast

import pymupdf
from jsonschema import Draft202012Validator

from .artifacts import load_schema
from .errors import IntegrityError
from .hashing import sha256_file
from .metadata_bindings import METADATA_BINDINGS
from .units import load_source_units, validate_source_units

TERMINOLOGY_ROLE = "TERMINOLOGY_REFERENCE"
# Source-unit JSON objects are strictly validated before this boundary type is used.
SourceUnitRecord = dict[str, Any]
GLOSSARY_COLUMNS = (
    "term_id",
    "concept_en",
    "candidate_fi",
    "approved_fi",
    "definition_context",
    "source_refs",
    "source_evidence_strength",
    "status",
    "clinical_risk",
    "decision_note",
    "decided_by",
    "decision_date",
)


class GlossaryStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    CANDIDATE = "CANDIDATE"
    CONFLICT = "CONFLICT"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    APPROVED = "APPROVED"


class DetectedFileType(str, Enum):
    PDF = "PDF"
    CSV_SEMICOLON_UTF8 = "CSV_SEMICOLON_UTF8"


class MetadataField(str, Enum):
    TITLE = "title"
    PUBLISHER_ORGANISATION = "publisher_organisation"
    PUBLICATION_VERSION_DATE = "publication_version_date"
    SOURCE_URL = "source_url"
    COPYRIGHT_NOTICE = "copyright_notice"
    LICENCE_REUSE_TERMS = "licence_reuse_terms"


class MetadataDerivation(str, Enum):
    EXACT_SOURCE_TEXT = "EXACT_SOURCE_TEXT"
    LINE_BREAK_NORMALIZED = "SOURCE_TEXT_LINE_BREAK_NORMALIZED"
    DATE_NORMALIZED_ISO = "SOURCE_DATE_NORMALIZED_ISO"


class ProvenanceStatus(str, Enum):
    CONTENT_AND_FILE_VERIFIED_METADATA_PARTIAL = (
        "CONTENT_AND_FILE_VERIFIED_METADATA_PARTIAL"
    )
    FILE_VERIFIED_METADATA_UNRESOLVED = "FILE_VERIFIED_METADATA_UNRESOLVED"


class LicenceReuseStatus(str, Enum):
    COPYRIGHT_NOTICE_NO_REUSE_TERMS_IDENTIFIED = (
        "COPYRIGHT_NOTICE_NO_REUSE_TERMS_IDENTIFIED"
    )
    UNKNOWN_NOT_STATED_IN_SOURCE = "UNKNOWN_NOT_STATED_IN_SOURCE"


# Metadata a content-verified provenance claim must actually prove from the file.
CONTENT_VERIFIED_METADATA = (
    MetadataField.TITLE,
    MetadataField.PUBLISHER_ORGANISATION,
    MetadataField.PUBLICATION_VERSION_DATE,
)
# Metadata a file-only provenance claim must leave explicitly unresolved.
FILE_ONLY_UNRESOLVED_METADATA = (
    MetadataField.PUBLISHER_ORGANISATION,
    MetadataField.PUBLICATION_VERSION_DATE,
    MetadataField.SOURCE_URL,
)
SOURCE_DATE_PATTERN = re.compile(r"(?<!\d)(?:(\d{1,2})\.(\d{1,2})\.)?(\d{4})(?!\d)")


@dataclass(frozen=True)
class PdfPageEvidence:
    page: int
    locator: str

    def describe(self) -> str:
        return f"PDF page {self.page}: {self.locator}"


@dataclass(frozen=True)
class CsvCellEvidence:
    row: int
    header: str
    locator: str

    def describe(self) -> str:
        return f"CSV row {self.row} column `{self.header}`: {self.locator}"


MetadataEvidence = PdfPageEvidence | CsvCellEvidence


def _require_nonblank(context: str, field: str, value: object) -> str:
    """Reject blank and whitespace-only metadata strings."""

    if not isinstance(value, str) or not value.strip():
        raise IntegrityError(
            f"{context}: {field} must be non-blank and non-whitespace; got {value!r}"
        )
    return value


@dataclass(frozen=True)
class SourceVerifiedMetadata:
    """One metadata value re-derivable from a declared location in the file."""

    field: MetadataField
    value: str
    derivation: MetadataDerivation
    source_fragment: str | None
    evidence: MetadataEvidence

    def __post_init__(self) -> None:
        _require_nonblank(
            f"source-verified {self.field.value}", "value", self.value
        )
        if self.source_fragment is not None:
            _require_nonblank(
                f"source-verified {self.field.value}",
                "source_fragment",
                self.source_fragment,
            )
        _require_nonblank(
            f"source-verified {self.field.value}",
            "evidence locator",
            self.evidence.locator,
        )


@dataclass(frozen=True)
class UnresolvedMetadata:
    """One metadata field the registered file does not state."""

    field: MetadataField
    reason: str

    def __post_init__(self) -> None:
        _require_nonblank(
            f"unresolved metadata {self.field.value}", "reason", self.reason
        )


@dataclass(frozen=True)
class CsvNonEntryRow:
    row: int
    purpose: str
    expected_primary_term_cell: str


@dataclass(frozen=True)
class CsvStructure:
    """Declared CSV layout semantics; row numbers are physical 1-based records."""

    delimiter: str
    field_name_row: int
    primary_term_header: str
    non_entry_rows: tuple[CsvNonEntryRow, ...]

    @property
    def non_entry_row_numbers(self) -> frozenset[int]:
        return frozenset(item.row for item in self.non_entry_rows)


@dataclass(frozen=True)
class FileFacts:
    filename: str
    byte_count: int
    sha256: str
    detected_file_type: DetectedFileType
    csv_structure: CsvStructure | None


@dataclass(frozen=True)
class ProjectInferredMetadata:
    """Project classifications and observations, never source-provided evidence."""

    provenance_status: ProvenanceStatus
    licence_reuse_status: LicenceReuseStatus
    evidence_level: int
    metadata_confidence: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TerminologySource:
    source_id: str
    terminology_role: str
    file_facts: FileFacts
    source_verified_metadata: tuple[SourceVerifiedMetadata, ...]
    unresolved_metadata: tuple[UnresolvedMetadata, ...]
    project_inferred_metadata: ProjectInferredMetadata

    def __post_init__(self) -> None:
        failures = _metadata_consistency_failures(self)
        if failures:
            raise IntegrityError("; ".join(failures))

    @classmethod
    def from_record(cls, record: dict[str, object]) -> TerminologySource:
        verified = cast(
            dict[str, dict[str, object]], record["source_verified_metadata"]
        )
        return cls(
            source_id=cast(str, record["source_id"]),
            terminology_role=cast(str, record["terminology_role"]),
            file_facts=_file_facts(
                cast(dict[str, object], record["file_facts"])
            ),
            source_verified_metadata=tuple(
                _source_verified_metadata(field, verified[field.value])
                for field in MetadataField
                if field.value in verified
            ),
            unresolved_metadata=tuple(
                UnresolvedMetadata(
                    field=MetadataField(item["field"]),
                    reason=cast(str, item["reason"]),
                )
                for item in cast(
                    list[dict[str, object]], record["unresolved_metadata"]
                )
            ),
            project_inferred_metadata=_project_inferred_metadata(
                cast(dict[str, object], record["project_inferred_metadata"])
            ),
        )

    @property
    def filename(self) -> str:
        return self.file_facts.filename

    @property
    def byte_count(self) -> int:
        return self.file_facts.byte_count

    @property
    def sha256(self) -> str:
        return self.file_facts.sha256

    @property
    def detected_file_type(self) -> DetectedFileType:
        return self.file_facts.detected_file_type

    @property
    def verified_fields(self) -> frozenset[MetadataField]:
        return frozenset(item.field for item in self.source_verified_metadata)

    @property
    def unresolved_fields(self) -> tuple[MetadataField, ...]:
        return tuple(item.field for item in self.unresolved_metadata)

    def verified_value(self, field: MetadataField) -> str | None:
        """Return the source-verified value, never a project inference."""

        for item in self.source_verified_metadata:
            if item.field is field:
                return item.value
        return None

    @property
    def title(self) -> str | None:
        return self.verified_value(MetadataField.TITLE)

    @property
    def publisher_organisation(self) -> str | None:
        return self.verified_value(MetadataField.PUBLISHER_ORGANISATION)

    @property
    def publication_version_date(self) -> str | None:
        return self.verified_value(MetadataField.PUBLICATION_VERSION_DATE)

    @property
    def source_url(self) -> str | None:
        return self.verified_value(MetadataField.SOURCE_URL)

    @property
    def evidence_level(self) -> int:
        return self.project_inferred_metadata.evidence_level

    @property
    def provenance_status(self) -> str:
        return self.project_inferred_metadata.provenance_status.value

    @property
    def metadata_confidence(self) -> str:
        return self.project_inferred_metadata.metadata_confidence

    @property
    def licence_reuse_status(self) -> str:
        return self.project_inferred_metadata.licence_reuse_status.value

    @property
    def unresolved_reasons(self) -> tuple[str, ...]:
        return tuple(item.reason for item in self.unresolved_metadata)


def _metadata_evidence(record: dict[str, object]) -> MetadataEvidence:
    if record["kind"] == "PDF_PAGE":
        return PdfPageEvidence(
            page=cast(int, record["page"]),
            locator=cast(str, record["locator"]),
        )
    return CsvCellEvidence(
        row=cast(int, record["row"]),
        header=cast(str, record["header"]),
        locator=cast(str, record["locator"]),
    )


def _source_verified_metadata(
    field: MetadataField,
    record: dict[str, object],
) -> SourceVerifiedMetadata:
    return SourceVerifiedMetadata(
        field=field,
        value=cast(str, record["value"]),
        derivation=MetadataDerivation(record["derivation"]),
        source_fragment=cast(str | None, record.get("source_fragment")),
        evidence=_metadata_evidence(cast(dict[str, object], record["evidence"])),
    )


def _csv_structure(record: dict[str, object]) -> CsvStructure:
    return CsvStructure(
        delimiter=cast(str, record["delimiter"]),
        field_name_row=cast(int, record["field_name_row"]),
        primary_term_header=cast(str, record["primary_term_header"]),
        non_entry_rows=tuple(
            CsvNonEntryRow(
                row=cast(int, item["row"]),
                purpose=cast(str, item["purpose"]),
                expected_primary_term_cell=cast(
                    str, item["expected_primary_term_cell"]
                ),
            )
            for item in cast(list[dict[str, object]], record["non_entry_rows"])
        ),
    )


def _file_facts(record: dict[str, object]) -> FileFacts:
    structure = record.get("csv_structure")
    return FileFacts(
        filename=cast(str, record["filename"]),
        byte_count=cast(int, record["byte_count"]),
        sha256=cast(str, record["sha256"]),
        detected_file_type=DetectedFileType(record["detected_file_type"]),
        csv_structure=(
            _csv_structure(cast(dict[str, object], structure))
            if structure is not None
            else None
        ),
    )


def _project_inferred_metadata(
    record: dict[str, object],
) -> ProjectInferredMetadata:
    return ProjectInferredMetadata(
        provenance_status=ProvenanceStatus(record["provenance_status"]),
        licence_reuse_status=LicenceReuseStatus(record["licence_reuse_status"]),
        evidence_level=cast(int, record["evidence_level"]),
        metadata_confidence=cast(str, record["metadata_confidence"]),
        notes=tuple(cast(list[str], record["notes"])),
    )


class SourceLocation(TypedDict):
    kind: str
    number: int
    source_record_id: str | None


class ExtractedTerm(TypedDict):
    entry_id: str
    term_fi: str
    term_en: str | None
    term_en_origin: str
    definition: str | None
    context: str | None
    source_id: str
    source_filename: str
    source_sha256: str
    source_location: SourceLocation
    source_organisation: str | None
    source_date_version: str | None
    extraction_method: str
    source_fragment: str
    source_provided_fields: list[str]
    project_interpretation: str | None
    approval_status: str
    notes: list[str]


@dataclass(frozen=True)
class TerminologyValidationResult:
    source_count: int
    extracted_count: int
    source_provided_english_count: int
    conflict_count: int
    approved_count: int
    relevance_count: int


class PdfTextExtractor:
    """Local connector isolating PyMuPDF's partially untyped API."""

    def __init__(self) -> None:
        self._documents: dict[Path, pymupdf.Document] = {}

    def _document(self, path: Path) -> pymupdf.Document:
        document = self._documents.get(path)
        if document is None:
            # PyMuPDF 1.28.2 does not type this constructor for strict callers.
            document = pymupdf.open(path)  # type: ignore[no-untyped-call]
            self._documents[path] = document
        return document

    def page_count(self, path: Path) -> int:
        return int(self._document(path).page_count)

    def page_text(self, path: Path, page_number: int) -> str:
        # PyMuPDF 1.28.2 does not type Page.get_text for strict callers.
        return str(
            self._document(path)[page_number - 1].get_text("text")  # type: ignore[no-untyped-call]
        )

    def close(self) -> None:
        for document in self._documents.values():
            # PyMuPDF 1.28.2 does not type Document.close for strict callers.
            document.close()  # type: ignore[no-untyped-call]
        self._documents.clear()


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"Cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntegrityError(f"Expected a JSON object: {path}")
    return cast(dict[str, object], value)


def _validate_schema(
    value: object,
    schema_path: Path,
    label: str,
) -> None:
    errors = sorted(
        Draft202012Validator(load_schema(schema_path)).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<record>'}: {error.message}"
            for error in errors
        )
        raise IntegrityError(f"{label} schema validation failed: {details}")


def load_terminology_sources(
    manifest_path: Path,
    schema_path: Path,
) -> tuple[TerminologySource, ...]:
    value = _load_json_object(manifest_path)
    _validate_schema(value, schema_path, "Terminology source manifest")
    records = cast(list[dict[str, object]], value["sources"])
    sources = tuple(TerminologySource.from_record(record) for record in records)
    source_ids = [source.source_id for source in sources]
    filenames = [source.filename for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise IntegrityError("Terminology source manifest has duplicate source IDs")
    if len(filenames) != len(set(filenames)):
        raise IntegrityError("Terminology source manifest has duplicate filenames")
    return sources


def _csv_rows(path: Path, delimiter: str) -> dict[int, list[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return {
                number: row
                for number, row in enumerate(
                    csv.reader(handle, delimiter=delimiter), 1
                )
            }
    except (OSError, UnicodeError, csv.Error) as exc:
        raise IntegrityError(f"Cannot read terminology CSV {path}: {exc}") from exc


def _csv_cell(
    rows: dict[int, list[str]],
    field_names: list[str],
    row_number: int,
    header: str,
) -> str | None:
    row = rows.get(row_number)
    if row is None or header not in field_names:
        return None
    index = field_names.index(header)
    return row[index] if index < len(row) else None


def _collapse_layout_whitespace(text: str) -> str:
    return " ".join(text.split())


def _normalized_source_date(fragment: str) -> str | None:
    """Return the ISO date or bare year stated in a source fragment."""

    match = SOURCE_DATE_PATTERN.search(fragment)
    if match is None:
        return None
    day, month, year = match.groups()
    if day is None or month is None:
        return year
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _verify_csv_structure(path: Path, source: TerminologySource) -> list[str]:
    """Prove every declared non-entry CSV row really is the row it claims to be."""

    structure = source.file_facts.csv_structure
    if structure is None:
        return [f"{source.source_id}: CSV source has no declared CSV structure"]
    try:
        rows = _csv_rows(path, structure.delimiter)
    except IntegrityError as exc:
        return [f"{source.source_id}: {exc}"]
    field_names = rows.get(structure.field_name_row)
    if field_names is None or structure.primary_term_header not in field_names:
        return [
            f"{source.source_id}: declared field-name row {structure.field_name_row} "
            f"does not contain {structure.primary_term_header!r}"
        ]
    failures: list[str] = []
    for non_entry in structure.non_entry_rows:
        cell = _csv_cell(
            rows, field_names, non_entry.row, structure.primary_term_header
        )
        if cell != non_entry.expected_primary_term_cell:
            failures.append(
                f"{source.source_id}: declared {non_entry.purpose} row "
                f"{non_entry.row} should contain "
                f"{non_entry.expected_primary_term_cell!r} but contains {cell!r}"
            )
    return failures


def _verify_file_facts(source_root: Path, source: TerminologySource) -> list[str]:
    failures: list[str] = []
    if source.terminology_role != TERMINOLOGY_ROLE:
        failures.append(f"{source.source_id}: invalid terminology role")
    path = source_root / source.filename
    if path.stat().st_size != source.byte_count:
        failures.append(f"{source.source_id}: byte-count mismatch")
    if sha256_file(path) != source.sha256:
        failures.append(f"{source.source_id}: SHA-256 mismatch")
    if source.detected_file_type is DetectedFileType.PDF:
        if path.read_bytes()[:5] != b"%PDF-":
            failures.append(f"{source.source_id}: PDF signature mismatch")
        if source.file_facts.csv_structure is not None:
            failures.append(f"{source.source_id}: PDF source declares CSV structure")
    else:
        failures.extend(_verify_csv_structure(path, source))
    return failures


def _metadata_consistency_failures(source: TerminologySource) -> list[str]:
    """Reject metadata that contradicts itself or its provenance claim."""

    failures: list[str] = []
    verified = source.verified_fields
    unresolved_order = source.unresolved_fields
    unresolved = frozenset(unresolved_order)
    if len(unresolved_order) != len(unresolved):
        failures.append(f"{source.source_id}: duplicate unresolved metadata fields")
    contradictions = sorted(field.value for field in verified & unresolved)
    if contradictions:
        failures.append(
            f"{source.source_id}: metadata cannot be both source-verified and "
            f"unresolved: {contradictions}"
        )
    project = source.project_inferred_metadata
    if project.provenance_status is (
        ProvenanceStatus.CONTENT_AND_FILE_VERIFIED_METADATA_PARTIAL
    ):
        missing = sorted(
            field.value for field in CONTENT_VERIFIED_METADATA if field not in verified
        )
        if missing:
            failures.append(
                f"{source.source_id}: content-verified provenance requires "
                f"source-verified metadata for {missing}"
            )
        if not unresolved:
            failures.append(
                f"{source.source_id}: partial metadata provenance requires at least "
                "one explicitly unresolved metadata field"
            )
    else:
        claimed = sorted(
            field.value
            for field in FILE_ONLY_UNRESOLVED_METADATA
            if field in verified
        )
        if claimed:
            failures.append(
                f"{source.source_id}: file-verified/metadata-unresolved provenance "
                f"cannot claim source-verified metadata for {claimed}"
            )
        absent = sorted(
            field.value
            for field in FILE_ONLY_UNRESOLVED_METADATA
            if field not in unresolved
        )
        if absent:
            failures.append(
                f"{source.source_id}: file-verified/metadata-unresolved provenance "
                f"must explicitly record unresolved metadata for {absent}"
            )
    failures.extend(_licence_consistency_failures(source, verified, unresolved))
    return failures


def _licence_consistency_failures(
    source: TerminologySource,
    verified: frozenset[MetadataField],
    unresolved: frozenset[MetadataField],
) -> list[str]:
    status = source.project_inferred_metadata.licence_reuse_status
    failures: list[str] = []
    if MetadataField.LICENCE_REUSE_TERMS in verified:
        failures.append(
            f"{source.source_id}: a source-verified reuse licence requires an "
            "explicit licence status, which this project classification cannot express"
        )
        return failures
    if MetadataField.LICENCE_REUSE_TERMS not in unresolved:
        failures.append(
            f"{source.source_id}: licence/reuse terms must be either source-verified "
            "or explicitly unresolved"
        )
    if status is LicenceReuseStatus.COPYRIGHT_NOTICE_NO_REUSE_TERMS_IDENTIFIED:
        if MetadataField.COPYRIGHT_NOTICE not in verified:
            failures.append(
                f"{source.source_id}: a copyright-based licence status requires a "
                "source-verified copyright notice"
            )
    elif MetadataField.COPYRIGHT_NOTICE not in unresolved:
        failures.append(
            f"{source.source_id}: licence status cannot claim that nothing is stated "
            "while the copyright notice is not recorded as unresolved"
        )
    return failures


def _located_source_text(
    path: Path,
    source: TerminologySource,
    evidence: MetadataEvidence,
    extractor: PdfTextExtractor,
) -> str:
    """Return the exact text at a declared machine-checkable file location."""

    if isinstance(evidence, PdfPageEvidence):
        if source.detected_file_type is not DetectedFileType.PDF:
            raise IntegrityError("PDF page evidence requires a PDF source")
        if evidence.page > extractor.page_count(path):
            raise IntegrityError(f"PDF page {evidence.page} is out of range")
        return extractor.page_text(path, evidence.page)
    if source.detected_file_type is not DetectedFileType.CSV_SEMICOLON_UTF8:
        raise IntegrityError("CSV cell evidence requires a CSV source")
    structure = source.file_facts.csv_structure
    if structure is None:
        raise IntegrityError("CSV source has no declared CSV structure")
    rows = _csv_rows(path, structure.delimiter)
    cell = _csv_cell(
        rows,
        rows.get(structure.field_name_row) or [],
        evidence.row,
        evidence.header,
    )
    if cell is None:
        raise IntegrityError(
            f"CSV row {evidence.row} column {evidence.header!r} does not exist"
        )
    return cell


def _derivation_failures(
    label: str,
    item: SourceVerifiedMetadata,
    located: str,
) -> list[str]:
    if item.derivation is MetadataDerivation.EXACT_SOURCE_TEXT:
        if item.value not in located:
            return [f"{label} value is not present at its declared source location"]
        return []
    fragment = item.source_fragment
    if fragment is None:
        return [
            f"{label} declares {item.derivation.value} without a source fragment"
        ]
    if fragment not in located:
        return [
            f"{label} source fragment is not present at its declared source location"
        ]
    if item.derivation is MetadataDerivation.LINE_BREAK_NORMALIZED:
        if _collapse_layout_whitespace(fragment) != item.value:
            return [f"{label} value is not the whitespace-normalized source fragment"]
        return []
    if item.derivation is MetadataDerivation.DATE_NORMALIZED_ISO:
        if _normalized_source_date(fragment) != item.value:
            return [
                f"{label} value is not the ISO-normalized date in its source fragment"
            ]
        return []
    raise AssertionError(f"Unhandled metadata derivation: {item.derivation}")


def _metadata_evidence_failures(
    source_root: Path,
    source: TerminologySource,
    extractor: PdfTextExtractor,
) -> list[str]:
    """Re-derive every source-verified value from the registered file itself."""

    path = source_root / source.filename
    failures: list[str] = []
    for item in source.source_verified_metadata:
        label = f"{source.source_id}: source-verified {item.field.value}"
        try:
            located = _located_source_text(path, source, item.evidence, extractor)
        except IntegrityError as exc:
            failures.append(f"{label}: {exc}")
            continue
        failures.extend(_derivation_failures(label, item, located))
    return failures


def verify_metadata_field_bindings(repository: Path, manifest_path: Path) -> None:
    """Check semantic identity independently of caller-supplied evidence labels."""
    manifest = _load_json_object(manifest_path)
    records = cast(list[dict[str, Any]], manifest["sources"])
    extractor = PdfTextExtractor()
    try:
        for source in records:
            facts = source["file_facts"]
            for field, item in source["source_verified_metadata"].items():
                expected = METADATA_BINDINGS.get((facts["sha256"], field))
                label = f"{source['source_id']}: {field} field-specific evidence binding"
                if expected is None or item["evidence"] != expected:
                    raise IntegrityError(f"{label} mismatch")
                fragment = item.get("source_fragment", item["value"])
                if fragment != expected["exact_source_text"]:
                    raise IntegrityError(f"{label}: incomplete or unrelated field text")
                path = repository / "data/Sanasto" / facts["filename"]
                if expected["kind"] == "PDF_PAGE":
                    lines = extractor.page_text(path, expected["page"]).split("\n")
                    start = expected["line_start"]
                    context = "\n".join(lines[start:start + expected["line_count"]])
                    if context != expected["context_text"]:
                        raise IntegrityError(f"{label}: structural/context mismatch")
                    if context[expected["span_start"]:expected["span_end"]] != fragment:
                        raise IntegrityError(f"{label}: field span mismatch")
                else:
                    structure = facts["csv_structure"]
                    rows = structure["non_entry_rows"]
                    if not any(row["row"] == expected["row"]
                               and row["purpose"] == "VOCABULARY_TITLE"
                               and row["expected_primary_term_cell"] == fragment for row in rows):
                        raise IntegrityError(f"{label}: CSV title-row semantics mismatch")
                    if structure["primary_term_header"] != expected["header"]:
                        raise IntegrityError(f"{label}: CSV header semantics mismatch")
    finally:
        extractor.close()


def verify_terminology_sources(
    repository: Path,
    manifest_path: Path,
    schema_path: Path,
) -> tuple[TerminologySource, ...]:
    """Verify file facts, metadata consistency, and metadata evidence binding."""

    sources = load_terminology_sources(manifest_path, schema_path)
    verify_metadata_field_bindings(repository, manifest_path)
    source_root = repository / "data/Sanasto"
    actual_filenames = {path.name for path in source_root.iterdir() if path.is_file()}
    manifested_filenames = {source.filename for source in sources}
    if actual_filenames != manifested_filenames:
        raise IntegrityError(
            "Terminology source manifest membership mismatch: "
            f"missing={sorted(actual_filenames - manifested_filenames)} "
            f"extra={sorted(manifested_filenames - actual_filenames)}"
        )

    failures: list[str] = []
    extractor = PdfTextExtractor()
    try:
        for source in sources:
            failures.extend(_verify_file_facts(source_root, source))
            failures.extend(_metadata_consistency_failures(source))
            failures.extend(
                _metadata_evidence_failures(source_root, source, extractor)
            )
    finally:
        extractor.close()
    if failures:
        raise IntegrityError(
            "Terminology source verification failed: " + "; ".join(failures)
        )
    return sources


def _join_nonempty(values: list[str]) -> str | None:
    nonempty = [value for value in values if value]
    return " | ".join(nonempty) if nonempty else None


def _csv_terms(path: Path, source: TerminologySource) -> list[ExtractedTerm]:
    structure = source.file_facts.csv_structure
    if structure is None:
        raise IntegrityError(
            f"{source.source_id}: CSV source has no declared CSV structure"
        )
    non_entry_rows = structure.non_entry_row_numbers
    records: list[ExtractedTerm] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=structure.delimiter)
            if reader.fieldnames is None:
                raise IntegrityError(f"Terminology CSV has no header: {path}")
            for row_number, row in enumerate(reader, structure.field_name_row + 1):
                if row_number in non_entry_rows:
                    continue
                term_fi = (row.get(structure.primary_term_header) or "").strip()
                if not term_fi:
                    continue
                term_en = (row.get("properties.prefLabel.en") or "").strip() or None
                definition = (
                    (row.get("properties.definition.fi") or "").strip() or None
                )
                context = _join_nonempty(
                    [
                        (row.get("properties.note.fi") or "").strip(),
                        (row.get("properties.scopeNote.fi") or "").strip(),
                    ]
                )
                source_record_id = (row.get("id") or "").strip() or None
                provided = ["term_fi"]
                if term_en is not None:
                    provided.append("term_en")
                if definition is not None:
                    provided.append("definition")
                if context is not None:
                    provided.append("context")
                fragment = json.dumps(
                    {
                        "context": context,
                        "definition": definition,
                        "term_en": term_en,
                        "term_fi": term_fi,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                records.append(
                    ExtractedTerm(
                        entry_id=f"TERM-EVID-{source.source_id.removeprefix('TERM-SRC-')}-ROW-{row_number:04d}",
                        term_fi=term_fi,
                        term_en=term_en,
                        term_en_origin=(
                            "SOURCE_EXPLICIT" if term_en is not None else "NOT_PROVIDED"
                        ),
                        definition=definition,
                        context=context,
                        source_id=source.source_id,
                        source_filename=source.filename,
                        source_sha256=source.sha256,
                        source_location=SourceLocation(
                            kind="CSV_ROW",
                            number=row_number,
                            source_record_id=source_record_id,
                        ),
                        source_organisation=source.publisher_organisation,
                        source_date_version=source.publication_version_date,
                        extraction_method="CSV_EXPLICIT_COLUMN_EXTRACTION",
                        source_fragment=fragment,
                        source_provided_fields=provided,
                        project_interpretation=None,
                        approval_status="DISCOVERED",
                        notes=[],
                    )
                )
    except (OSError, UnicodeError, csv.Error) as exc:
        raise IntegrityError(f"Cannot extract terminology CSV {path}: {exc}") from exc
    return records


def _pdf_terms(
    source_root: Path,
    sources_by_id: dict[str, TerminologySource],
    rules_path: Path,
    rule_schema_path: Path,
) -> list[ExtractedTerm]:
    rule_set = _load_json_object(rules_path)
    _validate_schema(rule_set, rule_schema_path, "Terminology PDF extraction rules")
    rules = cast(list[dict[str, object]], rule_set["rules"])
    records: list[ExtractedTerm] = []
    seen_ids: set[str] = set()
    extractor = PdfTextExtractor()
    try:
        for rule in rules:
            entry_id = cast(str, rule["entry_id"])
            if entry_id in seen_ids:
                raise IntegrityError(f"Duplicate terminology extraction ID: {entry_id}")
            seen_ids.add(entry_id)
            source_id = cast(str, rule["source_id"])
            source = sources_by_id.get(source_id)
            if source is None or source.detected_file_type != "PDF":
                raise IntegrityError(
                    f"{entry_id}: PDF rule references invalid source {source_id}"
                )
            source_path = source_root / source.filename
            page_number = cast(int, rule["page"])
            if page_number > extractor.page_count(source_path):
                raise IntegrityError(f"{entry_id}: PDF page is out of range")
            page_text = extractor.page_text(source_path, page_number)
            exact_fragment = cast(str, rule["exact_fragment"])
            if exact_fragment not in page_text:
                raise IntegrityError(
                    f"{entry_id}: exact PDF fragment not found on page {page_number}"
                )
            term_en = cast(str | None, rule["term_en"])
            definition = cast(str | None, rule["definition"])
            context = cast(str | None, rule["context"])
            provided = ["term_fi"]
            if term_en is not None:
                provided.append("term_en")
            if definition is not None:
                provided.append("definition")
            if context is not None:
                provided.append("context")
            records.append(
                ExtractedTerm(
                    entry_id=entry_id,
                    term_fi=cast(str, rule["term_fi"]),
                    term_en=term_en,
                    term_en_origin=(
                        "SOURCE_EXPLICIT" if term_en is not None else "NOT_PROVIDED"
                    ),
                    definition=definition,
                    context=context,
                    source_id=source.source_id,
                    source_filename=source.filename,
                    source_sha256=source.sha256,
                    source_location=SourceLocation(
                        kind="PDF_PAGE",
                        number=page_number,
                        source_record_id=None,
                    ),
                    source_organisation=source.publisher_organisation,
                    source_date_version=source.publication_version_date,
                    extraction_method="PDF_EXACT_FRAGMENT_RULE",
                    source_fragment=exact_fragment,
                    source_provided_fields=provided,
                    project_interpretation=None,
                    approval_status="DISCOVERED",
                    notes=[],
                )
            )
    finally:
        extractor.close()
    return records


def extract_terminology(
    repository: Path,
    sources: tuple[TerminologySource, ...],
    rules_path: Path,
    rule_schema_path: Path,
) -> list[ExtractedTerm]:
    source_root = repository / "data/Sanasto"
    sources_by_id = {source.source_id: source for source in sources}
    records: list[ExtractedTerm] = []
    for source in sources:
        if source.detected_file_type is DetectedFileType.CSV_SEMICOLON_UTF8:
            records.extend(_csv_terms(source_root / source.filename, source))
    records.extend(
        _pdf_terms(source_root, sources_by_id, rules_path, rule_schema_path)
    )
    return sorted(records, key=lambda record: record["entry_id"])


def serialize_extracted_terms(records: list[ExtractedTerm]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for record in records
    )


def validate_extracted_terms(
    records: list[ExtractedTerm],
    schema_path: Path,
) -> None:
    failures: list[str] = []
    seen: set[str] = set()
    for line_number, record in enumerate(records, 1):
        try:
            _validate_schema(record, schema_path, f"Extracted term line {line_number}")
        except IntegrityError as exc:
            failures.append(str(exc))
        entry_id = record["entry_id"]
        if entry_id in seen:
            failures.append(f"Duplicate extracted terminology ID: {entry_id}")
        seen.add(entry_id)
        if record["project_interpretation"] is not None:
            failures.append(
                f"{entry_id}: extraction output must not contain project interpretation"
            )
        source_values = {
            "term_fi": record["term_fi"],
            "term_en": record["term_en"],
            "definition": record["definition"],
            "context": record["context"],
        }
        for field in record["source_provided_fields"]:
            value = source_values[field]
            if isinstance(value, str) and value not in record["source_fragment"]:
                failures.append(
                    f"{entry_id}: source-provided {field} is absent from source fragment"
                )
    if failures:
        raise IntegrityError("Extracted terminology validation failed: " + "; ".join(failures))


def load_glossary(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != GLOSSARY_COLUMNS:
                raise IntegrityError(
                    f"Glossary columns mismatch: expected={GLOSSARY_COLUMNS} "
                    f"actual={tuple(reader.fieldnames or ())}"
                )
            return [dict(row) for row in reader]
    except (OSError, UnicodeError, csv.Error) as exc:
        raise IntegrityError(f"Cannot read terminology glossary {path}: {exc}") from exc


def validate_glossary(rows: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    failures: list[str] = []
    approved: list[dict[str, str]] = []
    seen: set[str] = set()
    for row_number, row in enumerate(rows, 2):
        term_id = row.get("term_id", "").strip()
        if not term_id or term_id in seen:
            failures.append(f"row {row_number}: missing or duplicate term_id {term_id!r}")
        seen.add(term_id)
        try:
            status = GlossaryStatus(row.get("status", ""))
        except ValueError:
            failures.append(f"row {row_number}: invalid glossary status")
            continue
        approved_fi = row.get("approved_fi", "").strip()
        if status is GlossaryStatus.APPROVED:
            required = (
                "concept_en",
                "approved_fi",
                "source_refs",
                "decision_note",
                "decided_by",
                "decision_date",
            )
            missing = [field for field in required if not row.get(field, "").strip()]
            if missing:
                failures.append(
                    f"row {row_number}: APPROVED terminology missing {missing}"
                )
            else:
                approved.append(row)
        elif approved_fi:
            failures.append(
                f"row {row_number}: unapproved terminology cannot set approved_fi"
            )
    if failures:
        raise IntegrityError("Terminology glossary validation failed: " + "; ".join(failures))
    return tuple(approved)


def derive_conflicts(records: list[ExtractedTerm]) -> list[dict[str, object]]:
    english_groups: dict[str, list[ExtractedTerm]] = defaultdict(list)
    for record in records:
        if record["term_en"] is not None:
            english_groups[record["term_en"].casefold()].append(record)
    conflicts: list[dict[str, object]] = []
    for concept_key, group in sorted(english_groups.items()):
        finnish_terms = sorted({record["term_fi"] for record in group})
        if len(finnish_terms) < 2:
            continue
        conflicts.append(
            {
                "conflict_id": f"TERM-CONFLICT-{len(conflicts) + 1:03d}",
                "conflict_type": "DIFFERENT_FINNISH_TERMS_FOR_EXPLICIT_ENGLISH_CONCEPT",
                "concept_en": concept_key,
                "candidate_fi": finnish_terms,
                "source_entry_ids": sorted(record["entry_id"] for record in group),
                "status": "HUMAN_REVIEW_REQUIRED",
            }
        )
    finnish_groups: dict[str, list[ExtractedTerm]] = defaultdict(list)
    for record in records:
        finnish_groups[record["term_fi"].casefold()].append(record)
    for term_key, group in sorted(finnish_groups.items()):
        definitions = sorted(
            {record["definition"] for record in group if record["definition"] is not None}
        )
        if len(definitions) < 2:
            continue
        explicit_english = sorted(
            {record["term_en"] for record in group if record["term_en"] is not None}
        )
        conflicts.append(
            {
                "conflict_id": f"TERM-CONFLICT-{len(conflicts) + 1:03d}",
                "conflict_type": "DIFFERENT_DEFINITIONS_FOR_FINNISH_TERM",
                "concept_en": explicit_english[0] if len(explicit_english) == 1 else None,
                "candidate_fi": sorted({record["term_fi"] for record in group}),
                "definitions": definitions,
                "source_entry_ids": sorted(record["entry_id"] for record in group),
                "status": "HUMAN_REVIEW_REQUIRED",
                "term_key": term_key,
            }
        )
    return conflicts


def serialize_conflicts(conflicts: list[dict[str, object]]) -> str:
    return "".join(
        json.dumps(conflict, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for conflict in conflicts
    )


def build_relevance_rows(
    source_units: list[SourceUnitRecord],
    records: list[ExtractedTerm],
    conflicts: list[dict[str, object]],
) -> list[dict[str, str]]:
    validate_source_units(source_units)
    conflict_concepts = {
        concept
        for conflict in conflicts
        if isinstance((concept := conflict.get("concept_en")), str)
    }
    rows: list[dict[str, str]] = []
    for unit in source_units:
        source_text = cast(str, unit["source_text_en"])
        normalized_source = source_text.casefold()
        for record in records:
            term_en = record["term_en"]
            if term_en is None or len(term_en) < 4:
                continue
            pattern = rf"(?<!\w){re.escape(term_en.casefold())}(?!\w)"
            if re.search(pattern, normalized_source) is None:
                continue
            conflict_count = int(term_en.casefold() in conflict_concepts)
            rows.append(
                {
                    "unit_id": cast(str, unit["unit_id"]),
                    "english_phrase_concept": term_en,
                    "matched_terminology_source": record["source_id"],
                    "finnish_source_term": record["term_fi"],
                    "match_method": "CASEFOLD_EXACT_PHRASE_BOUNDARY",
                    "confidence": "HIGH" if not conflict_count else "AMBIGUOUS",
                    "human_review_required": "true",
                    "conflict_count": str(conflict_count),
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            row["unit_id"],
            row["english_phrase_concept"],
            row["matched_terminology_source"],
            row["finnish_source_term"],
        ),
    )


def serialize_relevance_rows(rows: list[dict[str, str]]) -> str:
    columns = (
        "unit_id",
        "english_phrase_concept",
        "matched_terminology_source",
        "finnish_source_term",
        "match_method",
        "confidence",
        "human_review_required",
        "conflict_count",
    )
    lines = ["\t".join(columns)]
    lines.extend("\t".join(row[column] for column in columns) for row in rows)
    return "\n".join(lines) + "\n"


def duplicate_finnish_term_groups(
    records: list[ExtractedTerm],
) -> dict[str, list[ExtractedTerm]]:
    groups: dict[str, list[ExtractedTerm]] = defaultdict(list)
    for record in records:
        groups[record["term_fi"].casefold()].append(record)
    return {
        key: group
        for key, group in sorted(groups.items())
        if len({record["source_id"] for record in group}) > 1
    }


def _source_provided_english_count(records: list[ExtractedTerm]) -> int:
    return sum(1 for record in records if record["term_en"] is not None)


def render_terminology_report(
    sources: tuple[TerminologySource, ...],
    records: list[ExtractedTerm],
    conflicts: list[dict[str, object]],
    glossary_rows: list[dict[str, str]],
    approved_count: int,
    relevance_count: int,
) -> str:
    duplicates = duplicate_finnish_term_groups(records)
    high_risk = [
        row["concept_en"]
        for row in glossary_rows
        if row.get("clinical_risk") == "HIGH"
    ]
    english_labels = _source_provided_english_count(records)
    unlabeled = len(records) - english_labels
    lines = [
        "# Terminology evidence report",
        "",
        "Status: terminology evidence only; no project terminology is approved.",
        "",
        "## Counts",
        f"- Registered terminology/reference sources: {len(sources)}",
        f"- Extracted source-provided terminology entries: {len(records)}",
        f"- Source-provided English labels: {english_labels}",
        f"- Entries with no source-provided English label: {unlabeled}",
        f"- Mechanical source-unit relevance matches: {relevance_count}",
        f"- Explicit terminology conflicts: {len(conflicts)}",
        f"- Cross-source duplicate Finnish term groups: {len(duplicates)}",
        f"- Glossary concepts requiring human review: {len(glossary_rows)}",
        f"- Approved project terminology: {approved_count}",
        "",
        "## Registered source files",
    ]
    for source in sources:
        unresolved = source.unresolved_reasons
        lines.extend(
            [
                f"- `{source.filename}`",
                f"  - SHA-256: `{source.sha256}`",
                f"  - Bytes: {source.byte_count}",
                f"  - Role: `{source.terminology_role}`; evidence level {source.evidence_level}",
                f"  - Provenance: `{source.provenance_status}`; metadata confidence `{source.metadata_confidence}`",
                f"  - Licence/reuse: `{source.licence_reuse_status}`",
                *([f"  - Unresolved: {'; '.join(unresolved)}"] if unresolved else []),
            ]
        )
    lines.extend(
        [
            "",
            "## Duplicate concepts and source terms",
        ]
    )
    if duplicates:
        for key, group in duplicates.items():
            refs = ", ".join(
                f"{record['source_id']}:{record['entry_id']}" for record in group
            )
            lines.append(f"- `{key}` — {refs}")
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Conflicts and different definitions"])
    if conflicts:
        for conflict in conflicts:
            lines.append(
                f"- `{conflict['conflict_id']}` `{conflict['conflict_type']}`: "
                f"{', '.join(cast(list[str], conflict['candidate_fi']))}; "
                f"human review required."
            )
    else:
        lines.append("- No mechanical conflict was detected; this is not a human resolution.")
    lines.extend(
        [
            "",
            "## Currency and source-authority differences",
            "- Dated 2018, 2019, and 2022 materials remain evidence, but currency must be checked by a human terminology reviewer before approval.",
            "- Evidence levels 2 and 3 are kept distinct. Missing CSV publisher, date, URL, and licence metadata are explicit and do not block G0.",
            "- No source is classified as canonical SPICT authority.",
            "",
            "## Concepts without an approved Finnish equivalent",
        ]
    )
    lines.extend(
        f"- `{row['concept_en']}` — `{row['status']}`"
        for row in glossary_rows
        if row.get("status") != GlossaryStatus.APPROVED.value
    )
    lines.extend(["", "## High-risk clinical concepts requiring human review"])
    lines.extend(f"- `{concept}`" for concept in high_risk)
    lines.extend(
        [
            "",
            "## Source-unit relevance",
            f"- Conservative exact English phrase matching produced {relevance_count} rows.",
            "- Zero matches are caused by lack of exact source-provided English concept overlap with SPICT source units, not by a failed extractor.",
            "- Remaining extracted entries have no source-provided English label.",
            "- No palliative/clinical Finnish terminology without explicit English source labels is automatically mapped to SPICT concepts.",
            "- Semantic mapping would require a separately reviewed methodology. This report does not infer matches.",
            "- Ambiguous matches, if present, remain flagged for human review.",
            "",
            "## Official-source integrity boundary",
            "- ValidateTerminology verifies terminology/reference evidence only.",
            "- VerifySources remains responsible for rejecting unmanifested files under `sources/official/`.",
            "- A standalone ValidateTerminology PASS is not a complete repository source-integrity PASS.",
            "",
            "## Authority boundary",
            "- Level 1 English SPICT source text and official change requirements define what must be translated.",
            "- These Finnish materials are terminology/reference evidence only. They cannot add, remove, redefine, or override English SPICT source content.",
            "- No AI suggestion or extracted term is mandatory. Only terminology with explicit `APPROVED` status and human disposition may later be supplied to both independent forward translators.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_terminology_evidence(repository: Path) -> TerminologyValidationResult:
    sources = verify_terminology_sources(
        repository,
        repository / "terminology/sources/terminology_source_manifest.json",
        repository / "schemas/terminology_source_manifest.schema.json",
    )
    records = extract_terminology(
        repository,
        sources,
        repository / "terminology/sources/pdf_extraction_rules.json",
        repository / "schemas/terminology_pdf_extraction_rule.schema.json",
    )
    validate_extracted_terms(
        records, repository / "schemas/terminology_extracted_entry.schema.json"
    )
    expected_extracted = serialize_extracted_terms(records)
    extracted_path = repository / "terminology/extracted/terminology_evidence.jsonl"
    try:
        actual_extracted = extracted_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise IntegrityError(f"Cannot read extracted terminology artifact: {exc}") from exc
    if actual_extracted != expected_extracted:
        raise IntegrityError(
            "Extracted terminology artifact is not reproducible from registered sources"
        )

    conflicts = derive_conflicts(records)
    conflicts_path = repository / "terminology/conflicts/terminology_conflicts.jsonl"
    if conflicts_path.read_text(encoding="utf-8") != serialize_conflicts(conflicts):
        raise IntegrityError("Terminology conflict artifact is not reproducible")

    glossary_rows = load_glossary(repository / "terminology/terms.csv")
    approved = validate_glossary(glossary_rows)
    source_units = load_source_units(repository / "data/source_units.jsonl")
    relevance = build_relevance_rows(source_units, records, conflicts)
    relevance_path = repository / "terminology/reports/source_unit_terminology_map.tsv"
    if relevance_path.read_text(encoding="utf-8") != serialize_relevance_rows(relevance):
        raise IntegrityError("Terminology relevance map is not reproducible")
    expected_report = render_terminology_report(
        sources,
        records,
        conflicts,
        glossary_rows,
        len(approved),
        len(relevance),
    )
    report_path = repository / "terminology/reports/TERMINOLOGY_EVIDENCE_REPORT.md"
    if report_path.read_text(encoding="utf-8") != expected_report:
        raise IntegrityError("Terminology evidence report is not reproducible")
    return TerminologyValidationResult(
        source_count=len(sources),
        extracted_count=len(records),
        source_provided_english_count=_source_provided_english_count(records),
        conflict_count=len(conflicts),
        approved_count=len(approved),
        relevance_count=len(relevance),
    )
