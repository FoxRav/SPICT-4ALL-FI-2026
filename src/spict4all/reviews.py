"""Human-review TSV validation."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError
from .evidence import EvidenceSource, EvidenceSourceKind, FinalInclusionStatus

REQUIRED_COLUMNS = {
    "unit_id", "clinical_reviewer", "language_reviewer", "methodology_reviewer",
    "decision", "approved_fi", "issues_remaining", "date",
}
REVIEW_DISPOSITIONS = {"APPROVED", "REVISED", "REJECTED", "PENDING_AUTHORITY"}


def load_human_reviews(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None:
                raise ArtifactValidationError(f"Human-review file has no header: {path}")
            missing = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise ArtifactValidationError(
                    f"Human-review file missing columns: {sorted(missing)}"
                )
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ArtifactValidationError(f"Cannot read human-review file {path}: {exc}") from exc


def validate_human_reviews(
    reviews: list[dict[str, str]],
    source_units: list[dict[str, Any]] | list[EvidenceSource],
    *,
    require_release_ready: bool = False,
) -> list[dict[str, str]]:
    failures: list[str] = []
    by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(reviews, 2):
        unit_id = row.get("unit_id", "")
        if unit_id in by_id:
            failures.append(f"row {row_number}: duplicate unit_id {unit_id}")
        by_id[unit_id] = row
    source_ids: set[str] = set()
    for unit in source_units:
        unit_id = (
            unit.evidence_id
            if isinstance(unit, EvidenceSource)
            else str(unit["unit_id"])
        )
        source_ids.add(unit_id)
        review_row = by_id.get(unit_id)
        if review_row is None:
            failures.append(f"missing human review for {unit_id}")
            continue
        disposition = review_row.get("decision", "").strip().upper()
        if disposition not in REVIEW_DISPOSITIONS:
            failures.append(f"missing required human disposition for {unit_id}")
            continue
        if disposition == "PENDING_AUTHORITY":
            pending_allowed = (
                isinstance(unit, EvidenceSource)
                and unit.source_kind
                is EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT
                and unit.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
            )
            if not pending_allowed:
                failures.append(
                    f"{unit_id}: PENDING_AUTHORITY is only valid for an unresolved "
                    "official source requirement"
                )
            if require_release_ready:
                failures.append(f"{unit_id}: pending authority blocks release")
        if require_release_ready and disposition == "REJECTED":
            failures.append(f"{unit_id}: rejected disposition blocks release")
        for field in ("clinical_reviewer", "language_reviewer", "methodology_reviewer", "date"):
            if not review_row.get(field, "").strip():
                failures.append(f"{unit_id}: missing {field}")
        if (
            disposition in {"APPROVED", "REVISED"}
            and not review_row.get("approved_fi", "").strip()
        ):
            failures.append(f"{unit_id}: {disposition} requires approved_fi")
        if review_row.get("issues_remaining", "").strip():
            failures.append(f"{unit_id}: unresolved issues block release")
    extra = sorted(set(by_id) - source_ids)
    if extra:
        failures.append(f"unknown human-review unit IDs: {extra}")
    if failures:
        raise ArtifactValidationError("Human-review validation failed: " + "; ".join(failures))
    return reviews
