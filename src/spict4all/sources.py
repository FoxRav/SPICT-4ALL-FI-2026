"""Official-source manifest verification."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .hashing import sha256_file

OFFICIAL_ROLES = {
    "20260521-Word-template-SPICT-4ALL-translations-2026.docx": "canonical_source",
    "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx": "official_change_spec",
    "20260130-Using-SPICT-4ALL-2025.docx": "official_reference",
    "20260521-Word-template-SPICT-4ALL-translations-2026.pdf": "official_reference",
}


def official_members(directory: Path) -> set[str]:
    """Enumerate without following any symlink or Windows reparse point."""
    result: set[str] = set()

    def visit(path: Path) -> None:
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise IntegrityError(
                f"Unsafe official symlink/junction/reparse point: {path}"
            )
        if stat.S_ISDIR(info.st_mode):
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(info.st_mode):
            result.add(path.relative_to(directory).as_posix())
        else:
            raise IntegrityError(f"Unsupported official filesystem entry: {path}")

    visit(directory)
    return result


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
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or filename in {".", ".."}
            or any(char in filename for char in "/\\:")
        ):
            raise IntegrityError(f"Unsafe manifest filename: {filename!r}")
        if filename in seen:
            raise IntegrityError(f"Duplicate manifest filename: {filename}")
        seen.add(filename)
        if item["immutable"] is not True:
            raise IntegrityError(f"Official source must be immutable: {filename}")
        if (
            not isinstance(item["sha256"], str)
            or re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) is None
        ):
            raise IntegrityError(f"Invalid SHA-256 in manifest: {filename}")
        if not isinstance(item["bytes"], int) or item["bytes"] < 0:
            raise IntegrityError(f"Invalid byte count in manifest: {filename}")
    for item in value:
        filename = item["filename"]
        if not isinstance(item["role"], str) or item["role"] not in set(
            OFFICIAL_ROLES.values()
        ):
            raise IntegrityError(f"Unsupported official role: {item['role']!r}")
        if OFFICIAL_ROLES.get(filename) != item["role"]:
            raise IntegrityError(f"Official filename-role binding mismatch: {filename}")
    return value


def verify_source_manifest(
    manifest_path: Path, official_dir: Path
) -> list[SourceCheck]:
    official_members(official_dir)
    checks: list[SourceCheck] = []
    for item in load_source_manifest(manifest_path):
        path = official_dir / item["filename"]
        if not path.is_file():
            checks.append(
                SourceCheck(
                    item["filename"],
                    item["role"],
                    item["sha256"],
                    None,
                    item["bytes"],
                    None,
                    False,
                    "missing file",
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
                item["filename"],
                item["role"],
                item["sha256"],
                actual_hash,
                item["bytes"],
                actual_bytes,
                not problems,
                "; ".join(problems) if problems else "verified",
            )
        )
    return checks


def require_verified_sources(
    manifest_path: Path, official_dir: Path
) -> list[SourceCheck]:
    checks = verify_source_manifest(manifest_path, official_dir)
    failures = [f"{check.filename}: {check.detail}" for check in checks if not check.ok]
    manifested = {item["filename"] for item in load_source_manifest(manifest_path)}
    if manifested != set(OFFICIAL_ROLES):
        failures.append(
            "Official manifest membership differs from the frozen four-file set"
        )
    # Existing root README is explicit project metadata, never source authority.
    unmanifested = sorted(official_members(official_dir) - manifested - {"README.md"})
    if unmanifested:
        failures.append(f"unmanifested official files: {unmanifested}")
    if failures:
        raise IntegrityError(
            "Official source verification failed: " + "; ".join(failures)
        )
    return checks
