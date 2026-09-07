from __future__ import annotations

import json
from pathlib import Path

import pytest

from spict4all.errors import IntegrityError
from spict4all.hashing import sha256_file
from spict4all.sources import load_source_manifest, require_verified_sources


def _manifest(path: Path, source: Path, **overrides: object) -> Path:
    item = {
        "filename": source.name,
        "sha256": sha256_file(source),
        "bytes": source.stat().st_size,
        "role": "canonical_source",
        "source_url": "user-supplied",
        "immutable": True,
    }
    item.update(overrides)
    path.write_text(json.dumps([item]), encoding="utf-8")
    return path


def test_repository_official_sources_match_manifest() -> None:
    root = Path(__file__).resolve().parents[1]
    checks = require_verified_sources(
        root / "sources/manifests/source_manifest.json", root / "sources/official"
    )
    assert len(checks) == 4


def test_source_hash_change_fails(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    source = official / "source.docx"
    source.write_bytes(b"original")
    manifest = _manifest(tmp_path / "manifest.json", source)
    source.write_bytes(b"changed")
    with pytest.raises(IntegrityError, match="SHA-256 mismatch"):
        require_verified_sources(manifest, official)


def test_source_byte_count_change_fails(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    source = official / "source.docx"
    source.write_bytes(b"source")
    manifest = _manifest(tmp_path / "manifest.json", source, bytes=999)
    with pytest.raises(IntegrityError, match="byte-count mismatch"):
        require_verified_sources(manifest, official)


def test_missing_official_source_fails(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    source = tmp_path / "source.docx"
    source.write_bytes(b"source")
    manifest = _manifest(tmp_path / "manifest.json", source)
    with pytest.raises(IntegrityError, match="missing file"):
        require_verified_sources(manifest, official)


def test_duplicate_manifest_filename_fails(tmp_path: Path) -> None:
    item = {
        "filename": "source.docx", "sha256": "0" * 64, "bytes": 0,
        "role": "reference", "source_url": "x", "immutable": True,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps([item, item]), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Duplicate manifest filename"):
        load_source_manifest(path)


def test_nonimmutable_official_source_fails(tmp_path: Path) -> None:
    item = {
        "filename": "source.docx", "sha256": "0" * 64, "bytes": 0,
        "role": "reference", "source_url": "x", "immutable": False,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps([item]), encoding="utf-8")
    with pytest.raises(IntegrityError, match="must be immutable"):
        load_source_manifest(path)


def test_unmanifested_official_file_fails(tmp_path: Path) -> None:
    official = tmp_path / "official"
    official.mkdir()
    source = official / "source.docx"
    source.write_bytes(b"source")
    manifest = _manifest(tmp_path / "manifest.json", source)
    (official / "new-official.docx").write_bytes(b"new")
    with pytest.raises(IntegrityError, match="unmanifested official files"):
        require_verified_sources(manifest, official)
