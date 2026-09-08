"""Source-derived OOXML change completeness and typed evidence preparation.

Visible paragraph text is composed in XML order from text in ``w:r`` runs. ``w:t``
contributes its text, ``w:tab`` contributes a tab, ``w:br``/``w:cr`` contribute a
newline, and explicit soft/no-break hyphens are retained. A change marker counts
only when it is in that visible run's own ``w:rPr``. Paragraph properties and
paragraph-mark run properties never mark visible source text. Boundary layout
whitespace is removed from paragraph source text; internal whitespace is preserved.

WordprocessingML allows ``w:p`` elements to nest, for example inside a text box
carried by a run. Text and runs are attributed to the leaf paragraph that owns
them, so a container paragraph never reports the concatenation of the nested
paragraphs it wraps.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .artifacts import load_schema
from .authority import (
    CanonicalAuthorityDecision,
    CanonicalAuthorityDisposition,
    RequirementAuthorityDecision,
    RequirementAuthorityDisposition,
)
from .canonical_freeze import EXTRACTION_BINDINGS
from .errors import ArtifactValidationError, IntegrityError
from .evidence import (
    EvidenceProvenance,
    EvidenceSource,
    EvidenceSourceKind,
    FinalInclusionStatus,
)
from .hashing import sha256_file, sha256_text
from .jsonl import load_jsonl
from .sources import load_source_manifest
from .units import TranslationStatus, validate_source_units

WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD = f"{{{WORD_NAMESPACE}}}"
RELEVANT_WORD_PART = re.compile(
    r"^word/(?:document|header[^/]*|footer[^/]*|footnotes|endnotes)\.xml$"
)


class MarkerMechanism(str, Enum):
    HIGHLIGHT_YELLOW = "highlight_yellow"
    HIGHLIGHT_GREEN = "highlight_green"
    FONT_COLOR_ACCENT6 = "font_color_accent6"


class ConflictStatus(str, Enum):
    UNRESOLVED_CANONICAL_OMISSION = "UNRESOLVED_CANONICAL_OMISSION"
    AUTHORITY_RESOLVED = "AUTHORITY_RESOLVED"


class CanonicalExceptionType(str, Enum):
    NORMALIZED_CANONICAL_TEXT = "NORMALIZED_CANONICAL_TEXT"


class CanonicalNormalizationMethod(str, Enum):
    LINE_BREAK_TO_SPACE = "LINE_BREAK_TO_SPACE"


@dataclass(frozen=True)
class SourceMarking:
    marker_type: str
    value: str | None
    theme_color: str | None
    theme_shade: str | None


@dataclass(frozen=True)
class SourceProvenance:
    document_part: str
    table_index: int | None
    row: int | None
    column: int | None
    paragraph: int | None
    paragraph_index: int | None
    marking: SourceMarking


@dataclass(frozen=True)
class SourceRequirement:
    """A provenance-locked official requirement outside the canonical namespace."""

    requirement_id: str
    exact_source_text_en: str
    exact_text_sha256: str
    official_source_filename: str
    official_source_file_sha256: str
    source_role: str
    source_provenance: SourceProvenance
    change_year: int
    canonical_source_presence: bool
    conflict_status: ConflictStatus
    translation_evidence_required: bool
    requires_human_signoff: bool
    source_authority_confirmation_required: bool
    final_inclusion_status: FinalInclusionStatus
    publication_blocking: bool
    authority_disposition: RequirementAuthorityDisposition | None

    def __post_init__(self) -> None:
        if self.conflict_status is ConflictStatus.UNRESOLVED_CANONICAL_OMISSION:
            if (
                self.final_inclusion_status is not FinalInclusionStatus.UNRESOLVED
                or not self.publication_blocking
                or not self.source_authority_confirmation_required
            ):
                raise IntegrityError(
                    f"{self.requirement_id}: unresolved canonical omission must "
                    "remain authority-required, UNRESOLVED, and publication-blocking"
                )
        elif self.authority_disposition is None:
            raise IntegrityError(
                f"{self.requirement_id}: resolved conflict requires an explicit "
                "authority inclusion or exclusion disposition"
            )
        else:
            disposition = self.authority_disposition
            expected_decision = {
                FinalInclusionStatus.INCLUDE: RequirementAuthorityDecision.INCLUDE,
                FinalInclusionStatus.EXCLUDE: RequirementAuthorityDecision.EXCLUDE,
            }.get(self.final_inclusion_status)
            if (
                disposition.requirement_id != self.requirement_id
                or disposition.status != "FINAL"
                or disposition.decision is not expected_decision
            ):
                raise IntegrityError(
                    f"{self.requirement_id}: authority disposition must be "
                    "requirement-linked, FINAL, and match final inclusion status"
                )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> SourceRequirement:
        provenance = record["source_provenance"]
        marking = provenance["marking"]
        disposition_record = record.get("authority_disposition")
        disposition = (
            RequirementAuthorityDisposition(
                requirement_id=disposition_record["requirement_id"],
                decision=RequirementAuthorityDecision(disposition_record["decision"]),
                status=disposition_record["status"],
                decision_maker=disposition_record["decision_maker"],
                decision_date=disposition_record["decision_date"],
                evidence_reference=disposition_record["evidence_reference"],
            )
            if isinstance(disposition_record, dict)
            else None
        )
        return cls(
            requirement_id=record["requirement_id"],
            exact_source_text_en=record["exact_source_text_en"],
            exact_text_sha256=record["exact_text_sha256"],
            official_source_filename=record["official_source_filename"],
            official_source_file_sha256=record["official_source_file_sha256"],
            source_role=record["source_role"],
            source_provenance=SourceProvenance(
                document_part=provenance["document_part"],
                table_index=provenance.get("table_index"),
                row=provenance.get("row"),
                column=provenance.get("column"),
                paragraph=provenance.get("paragraph"),
                paragraph_index=provenance.get("paragraph_index"),
                marking=SourceMarking(
                    marker_type=marking["type"],
                    value=marking.get("value", marking.get("w_val")),
                    theme_color=marking.get("theme_color"),
                    theme_shade=marking.get("theme_shade"),
                ),
            ),
            change_year=record["change_year"],
            canonical_source_presence=record["canonical_source_presence"],
            conflict_status=ConflictStatus(record["conflict_status"]),
            translation_evidence_required=record["translation_evidence_required"],
            requires_human_signoff=record["requires_human_signoff"],
            source_authority_confirmation_required=record[
                "source_authority_confirmation_required"
            ],
            final_inclusion_status=FinalInclusionStatus(
                record["final_inclusion_status"]
            ),
            publication_blocking=record["publication_blocking"],
            authority_disposition=disposition,
        )


@dataclass(frozen=True)
class CanonicalUnitException:
    unit_id: str
    unit_text: str
    unit_source_text_sha256: str
    exception_type: CanonicalExceptionType
    canonical_docx_filename: str
    canonical_docx_sha256: str
    document_part: str
    paragraph_index: int
    table_index: int | None
    row: int | None
    column: int | None
    paragraph: int | None
    extraction_method: str
    normalization_method: CanonicalNormalizationMethod
    exact_canonical_visible_text: str
    exact_canonical_visible_text_sha256: str
    normalized_canonical_text: str
    reason_exact_matching_not_applicable: str
    authority_status: TranslationStatus
    source_authority_decision_required: bool
    publication_blocking: bool
    evidence_status: str
    authority_disposition: CanonicalAuthorityDisposition | None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> CanonicalUnitException:
        provenance = record["source_provenance"]
        disposition_record = record.get("authority_disposition")
        disposition = (
            CanonicalAuthorityDisposition(
                unit_id=disposition_record["unit_id"],
                decision=CanonicalAuthorityDecision(disposition_record["decision"]),
                decision_maker=disposition_record["decision_maker"],
                decision_date=disposition_record["decision_date"],
                evidence_reference=disposition_record["evidence_reference"],
                status=disposition_record["status"],
            )
            if isinstance(disposition_record, dict)
            else None
        )
        return cls(
            unit_id=record["unit_id"],
            unit_text=record["unit_text"],
            unit_source_text_sha256=record["unit_source_text_sha256"],
            exception_type=CanonicalExceptionType(record["exception_type"]),
            canonical_docx_filename=provenance["canonical_docx_filename"],
            canonical_docx_sha256=provenance["canonical_docx_sha256"],
            document_part=provenance["document_part"],
            paragraph_index=provenance["paragraph_index"],
            table_index=provenance.get("table_index"),
            row=provenance.get("row"),
            column=provenance.get("column"),
            paragraph=provenance.get("paragraph"),
            extraction_method=provenance["extraction_method"],
            normalization_method=CanonicalNormalizationMethod(
                provenance["normalization_method"]
            ),
            exact_canonical_visible_text=provenance["exact_canonical_visible_text"],
            exact_canonical_visible_text_sha256=provenance[
                "exact_canonical_visible_text_sha256"
            ],
            normalized_canonical_text=provenance["normalized_canonical_text"],
            reason_exact_matching_not_applicable=record[
                "reason_exact_matching_not_applicable"
            ],
            authority_status=TranslationStatus(record["authority_status"]),
            source_authority_decision_required=record[
                "source_authority_decision_required"
            ],
            publication_blocking=record["publication_blocking"],
            evidence_status=record["evidence_status"],
            authority_disposition=disposition,
        )


@dataclass(frozen=True)
class WordPart:
    name: str
    root: ET.Element


@dataclass(frozen=True)
class ParagraphLocation:
    document_part: str
    paragraph_index: int
    table_index: int | None
    row: int | None
    column: int | None
    paragraph: int | None


@dataclass(frozen=True)
class MarkedRun:
    visible_text: str
    mechanism: MarkerMechanism
    value: str | None
    theme_color: str | None
    theme_shade: str | None


@dataclass(frozen=True)
class MarkedParagraph:
    visible_text: str
    location: ParagraphLocation
    marked_runs: tuple[MarkedRun, ...]


@dataclass(frozen=True)
class ChangeSpecCensus:
    marked_paragraphs: tuple[MarkedParagraph, ...]

    @property
    def yellow_highlighted_runs(self) -> int:
        return self._count(MarkerMechanism.HIGHLIGHT_YELLOW)

    @property
    def green_highlighted_runs(self) -> int:
        return self._count(MarkerMechanism.HIGHLIGHT_GREEN)

    @property
    def accent6_font_runs(self) -> int:
        return self._count(MarkerMechanism.FONT_COLOR_ACCENT6)

    def _count(self, mechanism: MarkerMechanism) -> int:
        return sum(
            run.mechanism is mechanism
            for paragraph in self.marked_paragraphs
            for run in paragraph.marked_runs
        )


@dataclass(frozen=True)
class ChangeSpecCompleteness:
    census: ChangeSpecCensus
    canonical_paragraph_count: int
    absent_from_canonical: tuple[str, ...]


@dataclass(frozen=True)
class SourceRequirementVerification:
    requirements: tuple[SourceRequirement, ...]
    completeness: ChangeSpecCompleteness


@dataclass(frozen=True)
class VerifiedOfficialSource:
    filename: str
    role: str
    path: Path
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class CanonicalUnitResolution:
    unit: dict[str, Any]
    translation_status: TranslationStatus
    direct_location: ParagraphLocation | None
    normalized_location: ParagraphLocation | None
    exception: CanonicalUnitException | None
    final_inclusion_status: FinalInclusionStatus
    eligible_for_document_insertion: bool


@dataclass(frozen=True)
class CanonicalUnitVerification:
    canonical_source: VerifiedOfficialSource
    canonical_docx_texts: frozenset[str]
    resolutions: tuple[CanonicalUnitResolution, ...]
    exceptions: tuple[CanonicalUnitException, ...]


def enumerate_wordprocessing_parts(path: Path) -> tuple[WordPart, ...]:
    """Parse all relevant WordprocessingML text-bearing parts in a DOCX."""

    try:
        with zipfile.ZipFile(path, "r") as document:
            names = sorted(
                name for name in document.namelist() if RELEVANT_WORD_PART.fullmatch(name)
            )
            parts = tuple(
                WordPart(name=name, root=ET.fromstring(document.read(name)))
                for name in names
            )
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise IntegrityError(f"Cannot inspect official DOCX {path}: {exc}") from exc
    if not any(part.name == "word/document.xml" for part in parts):
        raise IntegrityError(f"Official DOCX has no word/document.xml: {path}")
    return parts


def _own_visible_text(element: ET.Element, fragments: list[str]) -> None:
    """Collect visible text owned by ``element``, excluding nested paragraphs."""

    for node in element:
        if node.tag == f"{WORD}p":
            continue
        if node.tag == f"{WORD}t":
            fragments.append(node.text or "")
        elif node.tag == f"{WORD}tab":
            fragments.append("\t")
        elif node.tag in {f"{WORD}br", f"{WORD}cr"}:
            fragments.append("\n")
        elif node.tag == f"{WORD}noBreakHyphen":
            fragments.append("\N{NON-BREAKING HYPHEN}")
        elif node.tag == f"{WORD}softHyphen":
            fragments.append("\N{SOFT HYPHEN}")
        _own_visible_text(node, fragments)


def _visible_text(element: ET.Element) -> str:
    fragments: list[str] = []
    _own_visible_text(element, fragments)
    return "".join(fragments)


def _own_runs(paragraph: ET.Element) -> tuple[ET.Element, ...]:
    """Return the ``w:r`` elements owned by this paragraph, not by nested ones."""

    runs: list[ET.Element] = []

    def collect(element: ET.Element) -> None:
        for node in element:
            if node.tag == f"{WORD}p":
                continue
            if node.tag == f"{WORD}r":
                runs.append(node)
                continue
            collect(node)

    collect(paragraph)
    return tuple(runs)


def _paragraph_visible_text(paragraph: ET.Element) -> str:
    """Remove only boundary layout whitespace; preserve internal visible content."""

    return _visible_text(paragraph).strip(" \t\r\n")


def _table_locations(
    part: WordPart,
) -> dict[int, tuple[int, int, int, int]]:
    locations: dict[int, tuple[int, int, int, int]] = {}
    for table_index, table in enumerate(part.root.iter(f"{WORD}tbl")):
        for row_index, row in enumerate(table.findall(f"{WORD}tr")):
            for column_index, cell in enumerate(row.findall(f"{WORD}tc")):
                for paragraph_index, paragraph in enumerate(cell.iter(f"{WORD}p")):
                    locations.setdefault(
                        id(paragraph),
                        (table_index, row_index, column_index, paragraph_index),
                    )
    return locations


def _run_markers(run: ET.Element) -> tuple[MarkedRun, ...]:
    visible_text = _visible_text(run)
    if not visible_text:
        return ()
    run_properties = run.find(f"{WORD}rPr")
    if run_properties is None:
        return ()

    markers: list[MarkedRun] = []
    highlight = run_properties.find(f"{WORD}highlight")
    highlight_value = (
        highlight.get(f"{WORD}val") if highlight is not None else None
    )
    highlight_mechanisms = {
        "yellow": MarkerMechanism.HIGHLIGHT_YELLOW,
        "green": MarkerMechanism.HIGHLIGHT_GREEN,
    }
    if highlight_value in highlight_mechanisms:
        markers.append(
            MarkedRun(
                visible_text=visible_text,
                mechanism=highlight_mechanisms[highlight_value],
                value=highlight_value,
                theme_color=None,
                theme_shade=None,
            )
        )

    color = run_properties.find(f"{WORD}color")
    if color is not None and color.get(f"{WORD}themeColor") == "accent6":
        markers.append(
            MarkedRun(
                visible_text=visible_text,
                mechanism=MarkerMechanism.FONT_COLOR_ACCENT6,
                value=color.get(f"{WORD}val"),
                theme_color=color.get(f"{WORD}themeColor"),
                theme_shade=color.get(f"{WORD}themeShade"),
            )
        )
    return tuple(markers)


def extract_visible_paragraphs(path: Path) -> tuple[tuple[ParagraphLocation, str], ...]:
    """Return exact visible paragraph text across all relevant Word parts."""

    paragraphs: list[tuple[ParagraphLocation, str]] = []
    for part in enumerate_wordprocessing_parts(path):
        table_locations = _table_locations(part)
        for paragraph_index, paragraph in enumerate(part.root.iter(f"{WORD}p")):
            table_location = table_locations.get(id(paragraph))
            paragraphs.append(
                (
                    ParagraphLocation(
                        document_part=part.name,
                        paragraph_index=paragraph_index,
                        table_index=table_location[0] if table_location else None,
                        row=table_location[1] if table_location else None,
                        column=table_location[2] if table_location else None,
                        paragraph=table_location[3] if table_location else None,
                    ),
                    _paragraph_visible_text(paragraph),
                )
            )
    return tuple(paragraphs)


def derive_marked_change_census(path: Path) -> ChangeSpecCensus:
    """Derive marked visible runs and their containing paragraphs from OOXML."""

    marked_paragraphs: list[MarkedParagraph] = []
    for part in enumerate_wordprocessing_parts(path):
        table_locations = _table_locations(part)
        for paragraph_index, paragraph in enumerate(part.root.iter(f"{WORD}p")):
            marked_runs = tuple(
                marker
                for run in _own_runs(paragraph)
                for marker in _run_markers(run)
            )
            if not marked_runs:
                continue
            table_location = table_locations.get(id(paragraph))
            marked_paragraphs.append(
                MarkedParagraph(
                    visible_text=_paragraph_visible_text(paragraph),
                    location=ParagraphLocation(
                        document_part=part.name,
                        paragraph_index=paragraph_index,
                        table_index=table_location[0] if table_location else None,
                        row=table_location[1] if table_location else None,
                        column=table_location[2] if table_location else None,
                        paragraph=table_location[3] if table_location else None,
                    ),
                    marked_runs=marked_runs,
                )
            )
    return ChangeSpecCensus(marked_paragraphs=tuple(marked_paragraphs))


def _require_verified_role(
    manifest_path: Path,
    official_dir: Path,
    role: str,
) -> VerifiedOfficialSource:
    entries = [
        item for item in load_source_manifest(manifest_path) if item["role"] == role
    ]
    if len(entries) != 1:
        raise IntegrityError(
            f"Expected exactly one official source with role {role!r}; found {len(entries)}"
        )
    entry = entries[0]
    path = official_dir / entry["filename"]
    if not path.is_file():
        raise IntegrityError(f"Missing official {role} file: {entry['filename']}")
    actual_bytes = path.stat().st_size
    actual_sha256 = sha256_file(path)
    failures: list[str] = []
    if actual_bytes != entry["bytes"]:
        failures.append(
            f"byte-count mismatch expected={entry['bytes']} actual={actual_bytes}"
        )
    if actual_sha256 != entry["sha256"]:
        failures.append(
            f"SHA-256 mismatch expected={entry['sha256']} actual={actual_sha256}"
        )
    if failures:
        raise IntegrityError(
            f"Official {role} verification failed for {entry['filename']}: "
            + "; ".join(failures)
        )
    return VerifiedOfficialSource(
        filename=entry["filename"],
        role=role,
        path=path,
        sha256=actual_sha256,
        byte_count=actual_bytes,
    )


def load_canonical_unit_exceptions(
    path: Path,
    schema_path: Path,
) -> list[CanonicalUnitException]:
    """Load schema-validated, unique canonical provenance exceptions."""

    try:
        records = load_jsonl(path)
    except ArtifactValidationError as exc:
        raise IntegrityError(f"Cannot load canonical unit exceptions: {exc}") from exc
    validator = Draft202012Validator(
        load_schema(schema_path), format_checker=FormatChecker()
    )
    failures: list[str] = []
    exceptions: list[CanonicalUnitException] = []
    seen: set[str] = set()
    for line_number, record in enumerate(records, 1):
        schema_errors = sorted(
            validator.iter_errors(record), key=lambda error: list(error.path)
        )
        failures.extend(
            f"line {line_number} {'.'.join(map(str, error.path)) or '<record>'}: "
            f"{error.message}"
            for error in schema_errors
        )
        unit_id = record.get("unit_id")
        if isinstance(unit_id, str):
            if unit_id in seen:
                failures.append(f"line {line_number}: duplicate exception unit_id {unit_id}")
            seen.add(unit_id)
        if not schema_errors:
            try:
                exceptions.append(CanonicalUnitException.from_record(record))
            except (IntegrityError, ValueError) as exc:
                failures.append(f"line {line_number}: {exc}")
    if failures:
        raise IntegrityError(
            "Canonical-unit exception validation failed: " + "; ".join(failures)
        )
    return exceptions


def _unit_location_matches(
    unit: dict[str, Any],
    location: ParagraphLocation,
) -> bool:
    source_location = unit.get("source_location")
    if not isinstance(source_location, dict):
        return False
    required = ("table_index", "row", "column", "paragraph")
    if not all(key in source_location for key in required):
        return False
    return (
        location.document_part == "word/document.xml"
        and location.table_index == source_location["table_index"]
        and location.row == source_location["row"]
        and location.column == source_location["column"]
        and location.paragraph == source_location["paragraph"]
    )


def normalize_canonical_text(
    text: str,
    method: CanonicalNormalizationMethod,
) -> str:
    """Apply one enumerated layout-only normalization."""

    if method is CanonicalNormalizationMethod.LINE_BREAK_TO_SPACE:
        return re.sub(r"[ \t]*[\r\n]+[ \t]*", " ", text)
    raise AssertionError(f"Unhandled canonical normalization method: {method}")


def _exception_location_matches(
    exception: CanonicalUnitException,
    location: ParagraphLocation,
) -> bool:
    if (
        location.document_part != exception.document_part
        or location.paragraph_index != exception.paragraph_index
    ):
        return False
    optional_values = (
        (exception.table_index, location.table_index),
        (exception.row, location.row),
        (exception.column, location.column),
        (exception.paragraph, location.paragraph),
    )
    return all(expected is None or expected == actual for expected, actual in optional_values)


def _exception_final_state(
    exception: CanonicalUnitException,
) -> tuple[FinalInclusionStatus, bool]:
    disposition = exception.authority_disposition
    if disposition is None:
        return FinalInclusionStatus.UNRESOLVED, False
    if disposition.decision is CanonicalAuthorityDecision.APPROVE:
        return FinalInclusionStatus.INCLUDE, True
    return FinalInclusionStatus.EXCLUDE, False


def canonical_binding_records(
    canonical_source: VerifiedOfficialSource,
) -> list[dict[str, Any]]:
    """Recompute the complete frozen mapping from the official document."""
    paragraphs = extract_visible_paragraphs(canonical_source.path)
    records: list[dict[str, Any]] = []
    for binding in EXTRACTION_BINDINGS:
        matches = [text for location, text in paragraphs
                   if asdict(location) == binding["structural_location"]]
        if len(matches) != 1:
            raise IntegrityError("Canonical freeze structural location is not unique")
        text = matches[0]
        if binding["normalization_method"] == "LINE_BREAK_TO_SPACE":
            text = normalize_canonical_text(text, CanonicalNormalizationMethod.LINE_BREAK_TO_SPACE)
        records.append({**binding, "source_text_en": text,
                        "source_text_sha256": sha256_text(text),
                        "canonical_official_filename": canonical_source.filename,
                        "canonical_official_sha256": canonical_source.sha256,
                        "extraction_method": "OOXML_VISIBLE_PARAGRAPH_TEXT",
                        "baseline_translation_status": "AUTHORITY_DECISION_REQUIRED"
                        if binding["authority_required"] else "UNTRANSLATED",
                        "baseline_final_inclusion_status": "UNRESOLVED"
                        if binding["authority_required"] else "CANONICAL",
                        "baseline_publication_blocking": binding["authority_required"],
                        "baseline_insertable": not binding["authority_required"]})
    return records


def verify_canonical_binding(
    canonical_source: VerifiedOfficialSource, units: list[dict[str, Any]],
    manifest_path: Path,
) -> None:
    expected = canonical_binding_records(canonical_source)
    repository = manifest_path.parent.parent.parent
    freeze_path = repository / "data/canonical_unit_manifest.json"
    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise IntegrityError(f"Cannot read canonical freeze: {exc}") from exc
    schema = load_schema(repository / "schemas/canonical_unit_manifest.schema.json")
    if list(Draft202012Validator(schema).iter_errors(freeze)):
        raise IntegrityError("Canonical freeze schema mismatch")
    if freeze != {"version": 1, "bindings": expected}:
        raise IntegrityError("Canonical freeze differs from source-derived extraction specification")
    by_id = {unit["unit_id"]: unit for unit in units}
    if set(by_id) != {row["unit_id"] for row in expected}:
        raise IntegrityError("Canonical membership mismatch: missing or extra unit")
    for row in expected:
        unit = by_id[row["unit_id"]]
        for field in ("source_text_en", "source_text_sha256", "source_location"):
            if unit[field] != row[field]:
                raise IntegrityError(f"{row['unit_id']}: frozen canonical identity {field} mismatch")
        if row["authority_required"] and unit["translation_status"] not in {
            "AUTHORITY_DECISION_REQUIRED", "AUTHORITY_RESOLVED"
        }:
            raise IntegrityError(f"{row['unit_id']}: frozen canonical authority requirement lost")


def verify_canonical_units_against_source(
    manifest_path: Path,
    official_dir: Path,
    canonical_units: list[dict[str, Any]],
    exceptions_path: Path,
    exception_schema_path: Path,
) -> CanonicalUnitVerification:
    """Resolve every unit to verified DOCX content or an explicit exception."""

    validate_source_units(canonical_units)
    canonical_source = _require_verified_role(
        manifest_path, official_dir, "canonical_source"
    )
    paragraphs = extract_visible_paragraphs(canonical_source.path)
    canonical_docx_texts = frozenset(text for _, text in paragraphs if text)
    if not exceptions_path.read_text(encoding="utf-8").strip():
        verify_canonical_binding(canonical_source, canonical_units, manifest_path)
        raise IntegrityError("Canonical freeze requires S4A-2026-000 title normalization record")
    exceptions = load_canonical_unit_exceptions(
        exceptions_path, exception_schema_path
    )
    exceptions_by_id = {exception.unit_id: exception for exception in exceptions}

    failures: list[str] = []
    resolutions: list[CanonicalUnitResolution] = []
    resolved_exception_ids: set[str] = set()
    for unit in canonical_units:
        unit_id = str(unit["unit_id"])
        source_text = str(unit["source_text_en"])
        status = TranslationStatus(unit["translation_status"])
        direct_locations = [
            location
            for location, text in paragraphs
            if text == source_text and _unit_location_matches(unit, location)
        ]
        exception = exceptions_by_id.get(unit_id)
        if direct_locations:
            if exception is not None:
                failures.append(
                    f"{unit_id}: canonical exception is unnecessary for directly "
                    "resolved DOCX text"
                )
            if status is not TranslationStatus.UNTRANSLATED:
                failures.append(
                    f"{unit_id}: direct canonical unit cannot clear or acquire an "
                    "authority status without an exception disposition"
                )
            resolutions.append(
                CanonicalUnitResolution(
                    unit=unit,
                    translation_status=status,
                    direct_location=direct_locations[0],
                    normalized_location=None,
                    exception=None,
                    final_inclusion_status=FinalInclusionStatus.CANONICAL,
                    eligible_for_document_insertion=True,
                )
            )
            continue

        if exception is None:
            failures.append(
                f"{unit_id}: source text does not resolve to its verified canonical "
                "DOCX location and has no canonical-unit exception"
            )
            continue
        resolved_exception_ids.add(unit_id)
        if exception.unit_source_text_sha256 != unit["source_text_sha256"]:
            failures.append(f"{unit_id}: exception source-text SHA-256 mismatch")
        if exception.unit_text != source_text:
            failures.append(f"{unit_id}: exception unit text mismatch")
        if exception.canonical_docx_filename != canonical_source.filename:
            failures.append(f"{unit_id}: exception canonical DOCX filename mismatch")
        if exception.canonical_docx_sha256 != canonical_source.sha256:
            failures.append(f"{unit_id}: exception canonical DOCX SHA-256 mismatch")
        provenance_matches = [
            (location, text)
            for location, text in paragraphs
            if _exception_location_matches(exception, location)
        ]
        normalized_location: ParagraphLocation | None = None
        if len(provenance_matches) != 1:
            failures.append(
                f"{unit_id}: exception provenance must resolve exactly one canonical "
                f"DOCX paragraph; found {len(provenance_matches)}"
            )
        else:
            normalized_location, canonical_text = provenance_matches[0]
            if canonical_text != exception.exact_canonical_visible_text:
                failures.append(
                    f"{unit_id}: declared canonical visible text does not match DOCX"
                )
            if sha256_text(canonical_text) != exception.exact_canonical_visible_text_sha256:
                failures.append(
                    f"{unit_id}: canonical visible-text SHA-256 mismatch"
                )
            normalized_text = normalize_canonical_text(
                canonical_text, exception.normalization_method
            )
            if "\n" not in canonical_text and "\r" not in canonical_text:
                failures.append(
                    f"{unit_id}: line-break normalization requires a canonical line break"
                )
            if re.findall(r"\S+", canonical_text) != re.findall(r"\S+", normalized_text):
                failures.append(
                    f"{unit_id}: normalization changed lexical content"
                )
            if normalized_text != exception.normalized_canonical_text:
                failures.append(
                    f"{unit_id}: independently normalized canonical text mismatch"
                )
            if normalized_text != source_text:
                failures.append(
                    f"{unit_id}: normalized canonical text does not equal source-unit text"
                )
        if exception.authority_status is not status:
            failures.append(
                f"{unit_id}: translation_status does not match exception authority status"
            )
        disposition = exception.authority_disposition
        if status is TranslationStatus.AUTHORITY_DECISION_REQUIRED:
            if (
                disposition is not None
                or not exception.source_authority_decision_required
                or not exception.publication_blocking
            ):
                failures.append(
                    f"{unit_id}: unresolved authority exception lost its blocker"
                )
        elif status is TranslationStatus.AUTHORITY_RESOLVED:
            if disposition is None:
                failures.append(
                    f"{unit_id}: authority status cleared without a disposition"
                )
            elif disposition.unit_id != unit_id:
                failures.append(
                    f"{unit_id}: authority disposition is not unit-linked"
                )
        else:
            failures.append(
                f"{unit_id}: unmatched canonical unit requires typed authority status"
            )
        final_status, eligible = _exception_final_state(exception)
        resolutions.append(
            CanonicalUnitResolution(
                unit=unit,
                translation_status=status,
                direct_location=None,
                normalized_location=normalized_location,
                exception=exception,
                final_inclusion_status=final_status,
                eligible_for_document_insertion=eligible,
            )
        )

    extra_exceptions = sorted(set(exceptions_by_id) - resolved_exception_ids)
    if extra_exceptions:
        failures.append(
            f"canonical exceptions do not resolve unmatched units: {extra_exceptions}"
        )
    if failures:
        raise IntegrityError(
            "Canonical-unit source verification failed: " + "; ".join(failures)
        )
    verify_canonical_binding(canonical_source, canonical_units, manifest_path)
    return CanonicalUnitVerification(
        canonical_source=canonical_source,
        canonical_docx_texts=canonical_docx_texts,
        resolutions=tuple(resolutions),
        exceptions=tuple(exceptions),
    )


def load_source_requirements(
    path: Path,
    schema_path: Path,
) -> list[SourceRequirement]:
    """Load requirement records with schema, hash, and uniqueness checks."""

    try:
        records = load_jsonl(path)
    except ArtifactValidationError as exc:
        raise IntegrityError(f"Cannot load source requirements: {exc}") from exc

    validator = Draft202012Validator(
        load_schema(schema_path), format_checker=FormatChecker()
    )
    failures: list[str] = []
    requirements: list[SourceRequirement] = []
    seen: set[str] = set()
    for line_number, record in enumerate(records, 1):
        schema_errors = sorted(
            validator.iter_errors(record), key=lambda error: list(error.path)
        )
        failures.extend(
            f"line {line_number} {'.'.join(map(str, error.path)) or '<record>'}: "
            f"{error.message}"
            for error in schema_errors
        )
        requirement_id = record.get("requirement_id")
        if isinstance(requirement_id, str):
            if requirement_id in seen:
                failures.append(
                    f"line {line_number}: duplicate requirement_id {requirement_id}"
                )
            seen.add(requirement_id)
        exact_text = record.get("exact_source_text_en")
        exact_hash = record.get("exact_text_sha256")
        if (
            isinstance(requirement_id, str)
            and isinstance(exact_text, str)
            and isinstance(exact_hash, str)
            and sha256_text(exact_text) != exact_hash
        ):
            failures.append(
                f"line {line_number}: exact-text hash mismatch for {requirement_id}"
            )
        if not schema_errors:
            try:
                requirements.append(SourceRequirement.from_record(record))
            except (IntegrityError, ValueError) as exc:
                failures.append(f"line {line_number}: {exc}")

    if failures:
        raise IntegrityError("Source-requirement validation failed: " + "; ".join(failures))
    return requirements


def verify_change_spec_completeness(
    manifest_path: Path,
    official_dir: Path,
    canonical_verification: CanonicalUnitVerification,
    source_requirements: list[SourceRequirement],
) -> ChangeSpecCompleteness:
    """Prove every source-derived marked paragraph is canonically accounted for."""

    canonical_source = _require_verified_role(
        manifest_path, official_dir, "canonical_source"
    )
    change_spec = _require_verified_role(
        manifest_path, official_dir, "official_change_spec"
    )
    if (
        canonical_source.filename
        != canonical_verification.canonical_source.filename
        or canonical_source.sha256 != canonical_verification.canonical_source.sha256
    ):
        raise IntegrityError(
            "Canonical verification token does not match manifest-verified source"
        )
    canonical_docx_texts = canonical_verification.canonical_docx_texts
    census = derive_marked_change_census(change_spec.path)
    absent_paragraphs = tuple(
        paragraph
        for paragraph in census.marked_paragraphs
        if paragraph.visible_text not in canonical_docx_texts
    )
    coverage_failures: list[str] = []
    for paragraph in absent_paragraphs:
        matching_requirements = [
            requirement
            for requirement in source_requirements
            if requirement.exact_source_text_en == paragraph.visible_text
            and _location_matches(paragraph.location, requirement.source_provenance)
        ]
        if len(matching_requirements) != 1:
            coverage_failures.append(
                f"{paragraph.visible_text!r} at {paragraph.location}: expected exactly "
                f"one official_change_requirement, found {len(matching_requirements)}"
            )
    if coverage_failures:
        raise IntegrityError(
            "Absent marked change-spec paragraph coverage failed: "
            + "; ".join(coverage_failures)
        )
    absent_from_canonical = tuple(
        dict.fromkeys(
            paragraph.visible_text for paragraph in absent_paragraphs
        )
    )
    return ChangeSpecCompleteness(
        census=census,
        canonical_paragraph_count=len(canonical_docx_texts),
        absent_from_canonical=absent_from_canonical,
    )


def _location_matches(
    location: ParagraphLocation,
    provenance: SourceProvenance,
) -> bool:
    if location.document_part != provenance.document_part:
        return False
    if provenance.paragraph_index is not None:
        return location.paragraph_index == provenance.paragraph_index
    return (
        location.table_index == provenance.table_index
        and location.row == provenance.row
        and location.column == provenance.column
        and location.paragraph == provenance.paragraph
    )


def _marking_matches(
    marked_runs: tuple[MarkedRun, ...],
    marking: SourceMarking,
) -> bool:
    if marking.marker_type == "highlight":
        if marking.value is None:
            return False
        expected = {
            "yellow": MarkerMechanism.HIGHLIGHT_YELLOW,
            "green": MarkerMechanism.HIGHLIGHT_GREEN,
        }.get(marking.value)
        return expected is not None and any(
            run.mechanism is expected for run in marked_runs
        )
    if marking.marker_type == "font_color":
        return any(
            run.mechanism is MarkerMechanism.FONT_COLOR_ACCENT6
            and run.value == marking.value
            and run.theme_color == marking.theme_color
            and run.theme_shade == marking.theme_shade
            for run in marked_runs
        )
    return False


def verify_source_requirements(
    requirements_path: Path,
    schema_path: Path,
    manifest_path: Path,
    official_dir: Path,
    canonical_verification: CanonicalUnitVerification,
) -> SourceRequirementVerification:
    """Verify requirements, marked completeness, linkage, and canonical presence."""

    requirements = load_source_requirements(requirements_path, schema_path)
    canonical_source = _require_verified_role(
        manifest_path, official_dir, "canonical_source"
    )
    if (
        canonical_source.filename
        != canonical_verification.canonical_source.filename
        or canonical_source.sha256 != canonical_verification.canonical_source.sha256
    ):
        raise IntegrityError(
            "Canonical verification token does not match manifest-verified source"
        )
    change_spec = _require_verified_role(
        manifest_path, official_dir, "official_change_spec"
    )
    canonical_texts = canonical_verification.canonical_docx_texts
    census = derive_marked_change_census(change_spec.path)

    failures: list[str] = []
    for requirement in requirements:
        if requirement.official_source_filename != change_spec.filename:
            failures.append(
                f"{requirement.requirement_id}: official source is not the "
                "manifest-linked official_change_spec"
            )
        if requirement.source_role != change_spec.role:
            failures.append(f"{requirement.requirement_id}: source role mismatch")
        if requirement.official_source_file_sha256 != change_spec.sha256:
            failures.append(f"{requirement.requirement_id}: source-file SHA-256 mismatch")

        matching_paragraphs = [
            paragraph
            for paragraph in census.marked_paragraphs
            if _location_matches(
                paragraph.location, requirement.source_provenance
            )
        ]
        if not matching_paragraphs:
            failures.append(
                f"{requirement.requirement_id}: marked official source location not found"
            )
            continue
        paragraph = matching_paragraphs[0]
        if paragraph.visible_text != requirement.exact_source_text_en:
            failures.append(
                f"{requirement.requirement_id}: exact requirement text not found at "
                "official source location"
            )
        if not _marking_matches(
            paragraph.marked_runs, requirement.source_provenance.marking
        ):
            failures.append(
                f"{requirement.requirement_id}: marking is not present on a visible "
                "source-text run"
            )
        actual_presence = requirement.exact_source_text_en in canonical_texts
        if actual_presence != requirement.canonical_source_presence:
            failures.append(
                f"{requirement.requirement_id}: canonical source presence mismatch"
            )

    if failures:
        raise IntegrityError(
            "Official source-requirement verification failed: " + "; ".join(failures)
        )
    completeness = verify_change_spec_completeness(
        manifest_path, official_dir, canonical_verification, requirements
    )
    return SourceRequirementVerification(
        requirements=tuple(requirements),
        completeness=completeness,
    )


def build_translation_evidence_sources(
    canonical_verification: CanonicalUnitVerification,
    requirements: list[SourceRequirement] | tuple[SourceRequirement, ...],
) -> list[EvidenceSource]:
    """Build typed stage inputs with explicit document-insertion eligibility."""

    sources: list[EvidenceSource] = []
    for resolution in canonical_verification.resolutions:
        unit = resolution.unit
        if resolution.direct_location is not None:
            provenance = EvidenceProvenance(
                source_role="canonical_source",
                document_part=resolution.direct_location.document_part,
                location=(
                    ("table_index", resolution.direct_location.table_index or 0),
                    ("row", resolution.direct_location.row or 0),
                    ("column", resolution.direct_location.column or 0),
                    ("paragraph", resolution.direct_location.paragraph or 0),
                ),
            )
        else:
            exception = resolution.exception
            if exception is None:
                raise IntegrityError(
                    f"{unit['unit_id']}: missing verified canonical resolution"
                )
            provenance = EvidenceProvenance(
                source_role="canonical_source_exception",
                document_part=exception.document_part,
                location=(
                    ("paragraph_index", exception.paragraph_index),
                    ("normalization_method", exception.normalization_method.value),
                ),
            )
        sources.append(
            EvidenceSource(
                evidence_id=str(unit["unit_id"]),
                source_kind=EvidenceSourceKind.CANONICAL_SOURCE_UNIT,
                exact_source_text_en=str(unit["source_text_en"]),
                source_text_sha256=str(unit["source_text_sha256"]),
                source_provenance=provenance,
                requires_translation_evidence=True,
                requires_human_signoff=bool(unit["requires_human_signoff"]),
                final_inclusion_status=resolution.final_inclusion_status,
                eligible_for_document_insertion=(
                    resolution.eligible_for_document_insertion
                ),
            )
        )
    sources.extend(
        EvidenceSource(
            evidence_id=requirement.requirement_id,
            source_kind=EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT,
            exact_source_text_en=requirement.exact_source_text_en,
            source_text_sha256=requirement.exact_text_sha256,
            source_provenance=EvidenceProvenance(
                source_role=requirement.source_role,
                document_part=requirement.source_provenance.document_part,
                location=tuple(
                    (key, value)
                    for key, value in (
                        ("table_index", requirement.source_provenance.table_index),
                        ("row", requirement.source_provenance.row),
                        ("column", requirement.source_provenance.column),
                        ("paragraph", requirement.source_provenance.paragraph),
                        (
                            "paragraph_index",
                            requirement.source_provenance.paragraph_index,
                        ),
                    )
                    if value is not None
                ),
            ),
            requires_translation_evidence=requirement.translation_evidence_required,
            requires_human_signoff=requirement.requires_human_signoff,
            final_inclusion_status=requirement.final_inclusion_status,
            eligible_for_document_insertion=(
                requirement.final_inclusion_status is FinalInclusionStatus.INCLUDE
                and requirement.authority_disposition is not None
            ),
        )
        for requirement in requirements
        if requirement.translation_evidence_required
    )
    return sources


def current_requirement_ids(
    requirements: list[SourceRequirement] | tuple[SourceRequirement, ...],
) -> tuple[str, ...]:
    """Return requirement IDs in data order. This is a report helper, not an allow-list."""

    return tuple(requirement.requirement_id for requirement in requirements)


def requirement_identity_summary(
    requirements: list[SourceRequirement] | tuple[SourceRequirement, ...],
) -> str:
    """Describe current frozen requirement identities derived from loaded data."""

    identifiers = current_requirement_ids(requirements)
    if not identifiers:
        return "requirement_ids=(none; derived from data)"
    return "requirement_ids=" + ",".join(identifiers)
