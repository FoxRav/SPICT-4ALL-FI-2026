"""Loading and integrity checks for the machine-readable source-unit index."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .hashing import sha256_text
from .jsonl import load_jsonl

UNIT_PATTERN = re.compile(r"^S4A-2026-(\d{3})$")
REQUIRED_FIELDS = {
    "unit_id", "section", "source_text_en", "source_text_sha256",
    "source_location", "source_style", "translation_status",
    "target_fi", "requires_human_signoff",
}


class TranslationStatus(str, Enum):
    UNTRANSLATED = "UNTRANSLATED"
    AUTHORITY_DECISION_REQUIRED = "AUTHORITY_DECISION_REQUIRED"
    AUTHORITY_RESOLVED = "AUTHORITY_RESOLVED"


def validate_source_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate IDs, source hashes, target emptiness, and typed authority status."""

    if not units:
        raise IntegrityError("Source-unit index is empty")
    seen: set[str] = set()
    numbers: list[int] = []
    for line_number, unit in enumerate(units, 1):
        missing = REQUIRED_FIELDS - unit.keys()
        if missing:
            raise IntegrityError(
                f"Source unit line {line_number} missing fields: {sorted(missing)}"
            )
        unit_id = unit["unit_id"]
        match = UNIT_PATTERN.fullmatch(unit_id) if isinstance(unit_id, str) else None
        if match is None:
            raise IntegrityError(f"Invalid unit_id at line {line_number}: {unit_id!r}")
        if unit_id in seen:
            raise IntegrityError(f"Duplicate unit_id: {unit_id}")
        seen.add(unit_id)
        numbers.append(int(match.group(1)))
        source_text = unit["source_text_en"]
        if not isinstance(source_text, str) or not source_text:
            raise IntegrityError(f"Missing source text for {unit_id}")
        if sha256_text(source_text) != unit["source_text_sha256"]:
            raise IntegrityError(f"Source-text hash mismatch for {unit_id}")
        if unit["target_fi"] != "":
            raise IntegrityError(f"Source index contains target translation for {unit_id}")
        if unit["requires_human_signoff"] is not True:
            raise IntegrityError(f"Source unit does not require human sign-off: {unit_id}")
        try:
            TranslationStatus(unit["translation_status"])
        except (TypeError, ValueError) as exc:
            raise IntegrityError(
                f"Invalid translation_status for {unit_id}: "
                f"{unit['translation_status']!r}"
            ) from exc
    expected = list(range(0, max(numbers) + 1))
    if sorted(numbers) != expected:
        missing_numbers = sorted(set(expected) - set(numbers))
        missing_ids = [f"S4A-2026-{number:03d}" for number in missing_numbers]
        raise IntegrityError(f"Missing source unit IDs: {missing_ids}")
    return units


def load_source_units(path: Path) -> list[dict[str, Any]]:
    return validate_source_units(load_jsonl(path))


def index_source_units(units: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {unit["unit_id"]: unit for unit in units}
