"""Official-source manifest verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .hashing import sha256_file


@dataclass(frozen=True)
class SourceCheck:
    filename: str
    role: str
    expected_sha256: str
    actual_sha256: str | None
    expected_bytes: int
    actual_bytes: int | None
    ok: bool
    detail: str


def load_source_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"Cannot load source manifest {path}: {exc}") from exc
    if not isinstance(value, list) or not value:
        raise IntegrityError("Source manifest must be a non-empty JSON array")
    required = {"filename", "sha256", "bytes", "role", "source_url", "immutable"}
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise IntegrityError(f"Manifest entry {index} must be an object")
        missing = required - item.keys()
        if missing:
            raise IntegrityError(f"Manifest entry {index} missing: {sorted(missing)}")
        filename = item["filename"]
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise IntegrityError(f"Unsafe manifest filename: {filename!r}")
        if filename in seen:
            raise IntegrityError(f"Duplicate manifest filename: {filename}")
        seen.add(filename)
        if item["immutable"] is not True:
            raise IntegrityError(f"Official source must be immutable: {filename}")
        if not isinstance(item["sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) is None:
            raise IntegrityError(f"Invalid SHA-256 in manifest: {filename}")
        if not isinstance(item["bytes"], int) or item["bytes"] < 0:
            raise IntegrityError(f"Invalid byte count in manifest: {filename}")
    return value


def verify_source_manifest(manifest_path: Path, official_dir: Path) -> list[SourceCheck]:
    checks: list[SourceCheck] = []
    for item in load_source_manifest(manifest_path):
        path = official_dir / item["filename"]
        if not path.is_file():
            checks.append(
                SourceCheck(
                    item["filename"], item["role"], item["sha256"], None,
                    item["bytes"], None, False, "missing file",
                )
            )
            continue
        actual_hash = sha256_file(path)
        actual_bytes = path.stat().st_size
        problems: list[str] = []
        if actual_hash != item["sha256"]:
            problems.append("SHA-256 mismatch")
        if actual_bytes != item["bytes"]:
            problems.append("byte-count mismatch")
        checks.append(
            SourceCheck(
                item["filename"], item["role"], item["sha256"], actual_hash,
                item["bytes"], actual_bytes, not problems,
                "; ".join(problems) if problems else "verified",
            )
        )
    return checks


def require_verified_sources(manifest_path: Path, official_dir: Path) -> list[SourceCheck]:
    checks = verify_source_manifest(manifest_path, official_dir)
    failures = [f"{check.filename}: {check.detail}" for check in checks if not check.ok]
    manifested = {item["filename"] for item in load_source_manifest(manifest_path)}
    unmanifested = sorted(
        path.name
        for path in official_dir.iterdir()
        if path.is_file() and path.name != "README.md" and path.name not in manifested
    )
    if unmanifested:
        failures.append(f"unmanifested official files: {unmanifested}")
    if failures:
        raise IntegrityError("Official source verification failed: " + "; ".join(failures))
    return checks
