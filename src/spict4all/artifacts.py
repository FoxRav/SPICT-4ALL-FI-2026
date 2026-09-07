"""Schema and source-link validation for JSONL evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import ArtifactValidationError
from .jsonl import load_jsonl
from .units import index_source_units, load_source_units


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"Cannot load schema {path}: {exc}") from exc
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ArtifactValidationError(f"Invalid JSON schema {path}: {exc}") from exc
    return schema


def validate_jsonl_artifact(
    artifact_path: Path,
    schema_path: Path,
    source_units_path: Path | None = None,
) -> list[dict[str, Any]]:
    records = load_jsonl(artifact_path)
    validator = Draft202012Validator(load_schema(schema_path))
    source_by_id = (
        index_source_units(load_source_units(source_units_path))
        if source_units_path is not None
        else None
    )
    seen: set[str] = set()
    failures: list[str] = []
    for line_number, record in enumerate(records, 1):
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        failures.extend(
            f"line {line_number} {'.'.join(map(str, error.path)) or '<record>'}: {error.message}"
            for error in errors
        )
        unit_id = record.get("unit_id")
        if isinstance(unit_id, str):
            if unit_id in seen:
                failures.append(f"line {line_number}: duplicate unit_id {unit_id}")
            seen.add(unit_id)
            if source_by_id is not None:
                source = source_by_id.get(unit_id)
                if source is None:
                    failures.append(f"line {line_number}: unknown unit_id {unit_id}")
                elif record.get("source_text_sha256") != source["source_text_sha256"]:
                    failures.append(f"line {line_number}: source hash mismatch for {unit_id}")
    if failures:
        raise ArtifactValidationError("Artifact validation failed: " + "; ".join(failures))
    return records
