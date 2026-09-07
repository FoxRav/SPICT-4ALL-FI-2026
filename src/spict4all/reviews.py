"""Human-review TSV validation."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError

REQUIRED_COLUMNS = {
    "unit_id", "clinical_reviewer", "language_reviewer", "methodology_reviewer",
    "decision", "approved_fi", "issues_remaining", "date",
}
FINAL_DISPOSITIONS = {"APPROVED", "REVISED", "REJECTED"}


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
    source_units: list[dict[str, Any]],
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
    for unit in source_units:
        unit_id = unit["unit_id"]
        row = by_id.get(unit_id)
        if row is None:
            failures.append(f"missing human review for {unit_id}")
            continue
        disposition = row.get("decision", "").strip().upper()
        if disposition not in FINAL_DISPOSITIONS:
            failures.append(f"missing required human disposition for {unit_id}")
            continue
        if require_release_ready and disposition == "REJECTED":
            failures.append(f"{unit_id}: rejected disposition blocks release")
        for field in ("clinical_reviewer", "language_reviewer", "methodology_reviewer", "date"):
            if not row.get(field, "").strip():
                failures.append(f"{unit_id}: missing {field}")
        if disposition in {"APPROVED", "REVISED"} and not row.get("approved_fi", "").strip():
            failures.append(f"{unit_id}: {disposition} requires approved_fi")
        if row.get("issues_remaining", "").strip():
            failures.append(f"{unit_id}: unresolved issues block release")
    extra = sorted(set(by_id) - {unit["unit_id"] for unit in source_units})
    if extra:
        failures.append(f"unknown human-review unit IDs: {extra}")
    if failures:
        raise ArtifactValidationError("Human-review validation failed: " + "; ".join(failures))
    return reviews
