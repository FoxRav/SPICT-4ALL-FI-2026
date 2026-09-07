"""Typed source contracts shared by translation evidence stages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

ProvenanceValue = str | int | bool


class EvidenceSourceKind(str, Enum):
    """Allowed origins for exact English translation evidence."""

    CANONICAL_SOURCE_UNIT = "canonical_source_unit"
    OFFICIAL_CHANGE_REQUIREMENT = "official_change_requirement"


class FinalInclusionStatus(str, Enum):
    """Authority state governing final document inclusion."""

    CANONICAL = "CANONICAL"
    UNRESOLVED = "UNRESOLVED"
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


@dataclass(frozen=True)
class EvidenceProvenance:
    """Immutable, explicit location and source-role evidence."""

    source_role: str
    document_part: str | None
    location: tuple[tuple[str, ProvenanceValue], ...]


@dataclass(frozen=True)
class EvidenceSource:
    """Exact source text plus authority-safe document insertion semantics."""

    evidence_id: str
    source_kind: EvidenceSourceKind
    exact_source_text_en: str
    source_text_sha256: str
    source_provenance: EvidenceProvenance
    requires_translation_evidence: bool
    requires_human_signoff: bool
    final_inclusion_status: FinalInclusionStatus
    eligible_for_document_insertion: bool

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, EvidenceSourceKind):
            raise ValueError(f"Invalid source_kind: {self.source_kind!r}")
        if not isinstance(self.final_inclusion_status, FinalInclusionStatus):
            raise ValueError(
                f"Invalid final_inclusion_status: {self.final_inclusion_status!r}"
            )
        if (
            self.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
            and self.eligible_for_document_insertion
        ):
            raise ValueError(
                "Unresolved evidence source cannot be document-insertable"
            )

    @property
    def unit_id(self) -> str:
        """Compatibility identifier for existing unit-oriented evidence formats."""

        return self.evidence_id


def document_insertion_sources(
    sources: list[EvidenceSource],
) -> tuple[EvidenceSource, ...]:
    """Select Stage-7 inputs only through explicit insertion eligibility."""

    return tuple(source for source in sources if source.eligible_for_document_insertion)
