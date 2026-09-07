"""Unit-level coverage comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import CoverageError
from .evidence import EvidenceSource


@dataclass(frozen=True)
class CoverageResult:
    source_count: int
    artifact_count: int
    missing: tuple[str, ...]
    extra: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.missing and not self.extra and self.source_count == self.artifact_count


def check_coverage(
    source_units: list[dict[str, Any]] | list[EvidenceSource],
    artifact_records: list[dict[str, Any]],
) -> CoverageResult:
    source_ids = [
        source.evidence_id
        if isinstance(source, EvidenceSource)
        else str(source["unit_id"])
        for source in source_units
    ]
    artifact_ids = [record.get("unit_id") for record in artifact_records]
    valid_artifact_ids = [item for item in artifact_ids if isinstance(item, str)]
    duplicate_ids = sorted(
        {item for item in valid_artifact_ids if valid_artifact_ids.count(item) > 1}
    )
    if duplicate_ids:
        raise CoverageError(f"Duplicate artifact unit IDs: {duplicate_ids}")
    source_set = set(source_ids)
    artifact_set = set(valid_artifact_ids)
    return CoverageResult(
        source_count=len(source_ids),
        artifact_count=len(artifact_records),
        missing=tuple(sorted(source_set - artifact_set)),
        extra=tuple(sorted(artifact_set - source_set)),
    )


def require_complete_coverage(
    source_units: list[dict[str, Any]] | list[EvidenceSource],
    artifact_records: list[dict[str, Any]],
) -> CoverageResult:
    result = check_coverage(source_units, artifact_records)
    if not result.complete:
        raise CoverageError(
            f"Incomplete coverage: missing={list(result.missing)}, extra={list(result.extra)}, "
            f"source_count={result.source_count}, artifact_count={result.artifact_count}"
        )
    return result
