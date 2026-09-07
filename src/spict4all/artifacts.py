"""Schema and source-link validation for JSONL evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .errors import ArtifactValidationError
from .evidence import EvidenceSource
from .jsonl import load_jsonl
from .units import index_source_units, load_source_units

COMPLETED_CANDIDATE_STATUSES = frozenset(
    {
        "READY_FOR_SYNTHESIS",
        "READY_FOR_HUMAN_REVIEW",
        "HUMAN_APPROVED",
        "HUMAN_REJECTED",
    }
)


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema_value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"Cannot load schema {path}: {exc}") from exc
    if not isinstance(schema_value, dict):
        raise ArtifactValidationError(f"JSON schema must be an object: {path}")
    schema = cast(dict[str, Any], schema_value)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ArtifactValidationError(f"Invalid JSON schema {path}: {exc}") from exc
    return schema


def _completed_candidate_failures(
    line_number: int,
    record: dict[str, Any],
) -> list[str]:
    """Reject blank Finnish candidates in completed states even without a schema."""

    status = record.get("status")
    if not isinstance(status, str) or status not in COMPLETED_CANDIDATE_STATUSES:
        return []
    candidate = record.get("candidate_fi")
    if isinstance(candidate, str) and candidate.strip():
        return []
    return [
        f"line {line_number}: candidate_fi must contain non-whitespace text in "
        f"status {status}; got {candidate!r}"
    ]


def validate_jsonl_artifact(
    artifact_path: Path,
    schema_path: Path,
    source_units_path: Path | None = None,
    *,
    source_records: list[EvidenceSource] | list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    records = load_jsonl(artifact_path)
    validator = Draft202012Validator(load_schema(schema_path))
    if source_units_path is not None and source_records is not None:
        raise ArtifactValidationError(
            "Provide source_units_path or source_records, not both"
        )
    source_by_id: dict[str, EvidenceSource | dict[str, Any]] | None
    if source_records is not None:
        source_by_id = {
            (
                source.evidence_id
                if isinstance(source, EvidenceSource)
                else str(source["unit_id"])
            ): source
            for source in source_records
        }
    elif source_units_path is not None:
        source_by_id = cast(
            dict[str, EvidenceSource | dict[str, Any]],
            index_source_units(load_source_units(source_units_path)),
        )
    else:
        source_by_id = None
    seen: set[str] = set()
    failures: list[str] = []
    for line_number, record in enumerate(records, 1):
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        failures.extend(
            f"line {line_number} {'.'.join(map(str, error.path)) or '<record>'}: {error.message}"
            for error in errors
        )
        failures.extend(_completed_candidate_failures(line_number, record))
        unit_id = record.get("unit_id")
        if isinstance(unit_id, str):
            if unit_id in seen:
                failures.append(f"line {line_number}: duplicate unit_id {unit_id}")
            seen.add(unit_id)
            if source_by_id is not None:
                source = source_by_id.get(unit_id)
                if source is None:
                    failures.append(f"line {line_number}: unknown unit_id {unit_id}")
                else:
                    expected_hash = (
                        source.source_text_sha256
                        if isinstance(source, EvidenceSource)
                        else source["source_text_sha256"]
                    )
                    if record.get("source_text_sha256") != expected_hash:
                        failures.append(
                            f"line {line_number}: source hash mismatch for {unit_id}"
                        )
    if failures:
        raise ArtifactValidationError("Artifact validation failed: " + "; ".join(failures))
    return records
