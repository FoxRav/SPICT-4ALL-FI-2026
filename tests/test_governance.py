from __future__ import annotations

import json
from pathlib import Path

import pytest

from spict4all.errors import IntegrityError
from spict4all.governance import (
    GOVERNANCE_PATHS,
    build_governance_manifest,
    serialize_governance_manifest,
    verify_governance_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/governance_integrity_manifest.json"
SCHEMA = ROOT / "schemas/governance_integrity_manifest.schema.json"


def test_governance_data_hashes_pass() -> None:
    checks = verify_governance_manifest(ROOT, MANIFEST, SCHEMA)
    assert [check.relative_path for check in checks] == list(GOVERNANCE_PATHS)


def test_governance_data_mutation_is_detected(tmp_path: Path) -> None:
    for relative_path in GOVERNANCE_PATHS:
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative_path).read_bytes())
    manifest = tmp_path / "governance.json"
    manifest.write_text(
        serialize_governance_manifest(build_governance_manifest(tmp_path)),
        encoding="utf-8",
    )
    (tmp_path / GOVERNANCE_PATHS[0]).write_text("mutated\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="SHA-256 mismatch"):
        verify_governance_manifest(tmp_path, manifest, SCHEMA)


def test_governance_manifest_duplicate_record_fails(tmp_path: Path) -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    value["files"].append(dict(value["files"][0]))
    manifest = tmp_path / "governance.json"
    manifest.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(IntegrityError, match="duplicate file records"):
        verify_governance_manifest(ROOT, manifest, SCHEMA)
