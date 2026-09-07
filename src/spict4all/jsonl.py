"""Strict JSON Lines loading for deterministic evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ArtifactValidationError(f"Cannot read JSONL {path}: {exc}") from exc

    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ArtifactValidationError(
                f"Malformed JSONL in {path} at line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise ArtifactValidationError(
                f"JSONL record in {path} at line {line_number} must be an object"
            )
        records.append(value)
    return records
