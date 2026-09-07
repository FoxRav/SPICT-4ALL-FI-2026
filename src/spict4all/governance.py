"""Integrity controls for mutable project governance data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

from .artifacts import load_schema
from .errors import IntegrityError
from .hashing import sha256_file

GOVERNANCE_PATHS = (
    "data/canonical_unit_exceptions.jsonl",
    "data/source_requirements.jsonl",
)


@dataclass(frozen=True)
class GovernanceFileCheck:
    relative_path: str
    sha256: str
    byte_count: int


def build_governance_manifest(repository: Path) -> dict[str, object]:
    """Build a deterministic, non-self-referential project governance ledger."""

    files: list[dict[str, object]] = []
    for relative_path in GOVERNANCE_PATHS:
        path = repository / relative_path
        if not path.is_file():
            raise IntegrityError(f"Missing governance data file: {relative_path}")
        files.append(
            {
                "relative_path": relative_path,
                "byte_count": path.stat().st_size,
                "sha256": sha256_file(path),
                "role": "MUTABLE_GOVERNANCE_DATA",
                "official_source": False,
            }
        )
    return {
        "manifest_version": 1,
        "trust_model": "PROJECT_CONTROLLED_GIT_AND_AUDIT_ANCHOR",
        "files": files,
    }


def serialize_governance_manifest(manifest: dict[str, object]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def verify_governance_manifest(
    repository: Path,
    manifest_path: Path,
    schema_path: Path,
) -> tuple[GovernanceFileCheck, ...]:
    """Verify schema, exact membership, byte counts, and SHA-256 values."""

    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(
            f"Cannot read governance integrity manifest {manifest_path}: {exc}"
        ) from exc
    errors = sorted(
        Draft202012Validator(load_schema(schema_path)).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<manifest>'}: {error.message}"
            for error in errors
        )
        raise IntegrityError(f"Governance integrity manifest validation failed: {details}")

    manifest = cast(dict[str, object], value)
    records = cast(list[dict[str, object]], manifest["files"])
    paths = [cast(str, record["relative_path"]) for record in records]
    if len(paths) != len(set(paths)):
        raise IntegrityError("Governance integrity manifest has duplicate file records")
    if set(paths) != set(GOVERNANCE_PATHS):
        raise IntegrityError(
            "Governance integrity manifest membership mismatch: "
            f"expected={list(GOVERNANCE_PATHS)} actual={sorted(paths)}"
        )

    failures: list[str] = []
    checks: list[GovernanceFileCheck] = []
    for record in records:
        relative_path = cast(str, record["relative_path"])
        path = repository / relative_path
        if not path.is_file():
            failures.append(f"{relative_path}: missing")
            continue
        actual_sha256 = sha256_file(path)
        actual_bytes = path.stat().st_size
        if actual_sha256 != record["sha256"]:
            failures.append(f"{relative_path}: SHA-256 mismatch")
        if actual_bytes != record["byte_count"]:
            failures.append(f"{relative_path}: byte-count mismatch")
        checks.append(
            GovernanceFileCheck(
                relative_path=relative_path,
                sha256=actual_sha256,
                byte_count=actual_bytes,
            )
        )
    if failures:
        raise IntegrityError("Governance data integrity failed: " + "; ".join(failures))
    return tuple(checks)
