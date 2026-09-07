"""R5 direct attacks against frozen source and metadata identity."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from spict4all.cli import main
from spict4all.errors import IntegrityError
from spict4all.governance import (
    build_governance_manifest,
    serialize_governance_manifest,
)
from spict4all.sources import require_verified_sources
from spict4all.terminology import verify_terminology_sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch(tmp_path):
    for directory in ("sources", "data", "schemas", "config"):
        shutil.copytree(
            ROOT / directory,
            tmp_path / directory,
            ignore=shutil.ignore_patterns("Sanasto"),
        )
    return tmp_path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def units(root):
    return [
        json.loads(line)
        for line in (root / "data/source_units.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]


def save_units(root, records):
    (root / "data/source_units.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )


def rehash(root):
    (root / "data/governance_integrity_manifest.json").write_text(
        serialize_governance_manifest(build_governance_manifest(root)), encoding="utf-8"
    )


@pytest.mark.parametrize(
    "attack",
    [
        "delete_052",
        "duplicate_053",
        "replace_000",
        "swap_ids",
        "location",
        "remove_normalization",
        "rewrite_freeze",
    ],
)
def test_canonical_membership_identity_attacks(scratch, capsys, attack):
    records = units(scratch)
    if attack == "delete_052":
        records.pop()
    elif attack == "duplicate_053":
        records.append({**records[-1], "unit_id": "S4A-2026-053"})
    elif attack in {"replace_000", "rewrite_freeze"}:
        records[0] = {**records[1], "unit_id": "S4A-2026-000"}
        (scratch / "data/canonical_unit_exceptions.jsonl").write_text(
            "\n", encoding="utf-8"
        )
        if attack == "rewrite_freeze":
            path = scratch / "data/canonical_unit_manifest.json"
            frozen = read(path)
            frozen["bindings"][0] = {**frozen["bindings"][1], "unit_id": "S4A-2026-000"}
            write(path, frozen)
    elif attack == "swap_ids":
        records[1]["unit_id"], records[2]["unit_id"] = (
            records[2]["unit_id"],
            records[1]["unit_id"],
        )
    elif attack == "location":
        records[1]["source_location"] = records[2]["source_location"]
    else:
        (scratch / "data/canonical_unit_exceptions.jsonl").write_text(
            "\n", encoding="utf-8"
        )
    save_units(scratch, records)
    rehash(scratch)
    assert main(["--root", str(scratch), "validate-canonical"]) == 1
    message = capsys.readouterr().err
    assert any(
        word in message for word in ("membership", "identity", "location", "freeze")
    )
    assert "Governance data integrity failed" not in message
    assert (
        main(
            [
                "--root",
                str(scratch),
                "check-final",
                "--status",
                "FINAL",
                "--gate-results",
                "absent.json",
                "--review",
                "absent.tsv",
            ]
        )
        == 1
    )
    assert "absent" not in capsys.readouterr().err


def test_title_blocker_and_clean_canonical_remain(scratch, capsys):
    assert main(["--root", str(scratch), "validate-canonical"]) == 0
    assert "direct=52, normalized=1" in capsys.readouterr().out
    assert (
        main(
            [
                "--root",
                str(scratch),
                "check-final",
                "--status",
                "FINAL",
                "--gate-results",
                "absent.json",
                "--review",
                "absent.tsv",
            ]
        )
        == 1
    )
    assert "S4A-2026-000" in capsys.readouterr().err


@pytest.mark.parametrize(
    "attack",
    [
        "publisher_as_title",
        "title_as_publisher",
        "same_page",
        "truncated_publisher",
        "unrelated_url",
        "relabel_evidence",
        "csv_title_as_publisher",
    ],
)
def test_metadata_field_binding_attacks(tmp_path, attack):
    manifest = read(ROOT / "terminology/sources/terminology_source_manifest.json")
    source = manifest["sources"][0]
    metadata = source["source_verified_metadata"]
    if attack in {"publisher_as_title", "relabel_evidence"}:
        metadata["title"] = copy.deepcopy(metadata["publisher_organisation"])
        if attack == "relabel_evidence":
            metadata["title"]["evidence"]["metadata_field"] = "title"
            metadata["title"]["evidence"]["semantic_evidence_type"] = "DOCUMENT_TITLE"
    elif attack == "title_as_publisher":
        metadata["publisher_organisation"] = copy.deepcopy(metadata["title"])
    elif attack == "same_page":
        metadata["title"] = copy.deepcopy(metadata["source_url"])
    elif attack == "truncated_publisher":
        item = metadata["publisher_organisation"]
        item["value"] = "Duodecim"
        item["evidence"]["exact_source_text"] = "Duodecim"
    elif attack == "unrelated_url":
        metadata["source_url"] = copy.deepcopy(
            manifest["sources"][1]["source_verified_metadata"]["source_url"]
        )
    else:
        source = manifest["sources"][3]
        metadata = source["source_verified_metadata"]
        metadata["publisher_organisation"] = copy.deepcopy(metadata["title"])
        source["unresolved_metadata"] = [
            row
            for row in source["unresolved_metadata"]
            if row["field"] != "publisher_organisation"
        ]
    path = tmp_path / "metadata.json"
    write(path, manifest)
    with pytest.raises(
        IntegrityError, match="field-specific evidence binding|publisher_organisation"
    ):
        verify_terminology_sources(
            ROOT, path, ROOT / "schemas/terminology_source_manifest.schema.json"
        )


def test_valid_title_and_publisher_bindings():
    sources = verify_terminology_sources(
        ROOT,
        ROOT / "terminology/sources/terminology_source_manifest.json",
        ROOT / "schemas/terminology_source_manifest.schema.json",
    )
    assert len(sources) == 5
    assert all(source.title and source.publisher_organisation for source in sources[:3])


@pytest.mark.parametrize(
    ("index", "role"),
    [
        (0, "unknown"),
        (0, "TERMINOLOGY_REFERENCE"),
        (0, ""),
        (0, "official_change_spec"),
        (1, "official_reference"),
        (2, "official_reference"),
        (3, "canonical_source"),
        (3, "official_change_spec"),
    ],
)
def test_official_role_binding_attacks(scratch, index, role):
    path = scratch / "sources/manifests/source_manifest.json"
    manifest = sorted(read(path), key=lambda row: row["filename"])
    manifest[index]["role"] = role
    write(path, manifest)
    with pytest.raises(IntegrityError, match="role"):
        require_verified_sources(path, scratch / "sources/official")


@pytest.mark.parametrize("name", ["test.txt", "test.docx", "copy.pdf", ".hidden"])
def test_recursive_unmanifested_official_files(scratch, name):
    directory = scratch / "sources/official/review-probe"
    directory.mkdir()
    path = directory / name
    if name == "copy.pdf":
        shutil.copyfile(next((ROOT / "sources/official").glob("*.pdf")), path)
    else:
        path.write_bytes(b"unmanifested")
    if name == ".hidden" and os.name == "nt":
        subprocess.run(["attrib", "+H", str(path)], check=True)
    with pytest.raises(IntegrityError, match="unmanifested official files"):
        require_verified_sources(
            scratch / "sources/manifests/source_manifest.json",
            scratch / "sources/official",
        )


def test_official_directory_junction_or_symlink_rejected(scratch, tmp_path):
    target = tmp_path / "external"
    target.mkdir()
    link = scratch / "sources/official/link"
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True
        )
        if result.returncode:
            pytest.skip("junction creation unsupported")
    else:
        link.symlink_to(target, target_is_directory=True)
    try:
        with pytest.raises(IntegrityError, match="symlink/junction/reparse"):
            require_verified_sources(
                scratch / "sources/manifests/source_manifest.json",
                scratch / "sources/official",
            )
    finally:
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()
