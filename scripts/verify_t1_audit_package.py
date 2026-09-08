"""Independent standard-library verifier for the sealed T1 audit delivery."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath


def verify(path: Path) -> dict:
    expected_zip = path.with_suffix(path.suffix + ".sha256").read_text().split()[0]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_zip:
        raise ValueError("ZIP SHA-256 mismatch")
    hashes = {}
    for line in Path(str(path) + ".members.sha256").read_text(encoding="utf-8").splitlines():
        value, name = line.split("  ", 1)
        if name in hashes:
            raise ValueError("Duplicate detached hash entry")
        hashes[name] = value
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != sorted(names) or len(set(names)) != len(names):
            raise ValueError("Unsorted or duplicate members")
        if set(names) != set(hashes):
            raise ValueError("Unexpected or missing members")
        for name in names:
            member = PurePosixPath(name)
            if (member.is_absolute() or ".." in member.parts or "\\" in name
                    or any(x in {".git", ".firecrawl", "__pycache__", ".pytest_cache", ".venv", "node_modules"} for x in member.parts)
                    or member.suffix.lower() in {".zip", ".7z", ".tar", ".gz", ".rar", ".pyc", ".tmp"}
                    or (member.name.lower() == "readme.md" and name not in {"data/README.md", "sources/official/README.md", "sources/reference/README.md", "terminology/README.md"})):
                raise ValueError(f"Forbidden member: {name}")
            if hashlib.sha256(archive.read(name)).hexdigest() != hashes[name]:
                raise ValueError(f"Member hash mismatch: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        manifest = json.loads(archive.read("T1_AUDIT_MANIFEST.json"))
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        for name, value in manifest["payload_sha256"].items():
            if hashes[name] != value:
                raise ValueError("Manifest payload hash mismatch")
        index = list(csv.DictReader(io.StringIO(archive.read("T1_AUDIT_FILE_HASHES.tsv").decode()), delimiter="\t"))
        if {r["path"] for r in index} != set(names) - {"T1_AUDIT_FILE_HASHES.tsv"}:
            raise ValueError("Internal hash index scope mismatch")
        if any(r["sha256"] != hashes[r["path"]] for r in index):
            raise ValueError("Internal hash index mismatch")
        official = json.loads(archive.read("sources/manifests/source_manifest.json"))
        for record in official:
            data = archive.read("sources/official/" + record["filename"])
            if hashlib.sha256(data).hexdigest() != record["sha256"] or len(data) != record["bytes"]:
                raise ValueError("Official-source integrity mismatch")
        terminology = json.loads(archive.read("terminology/sources/terminology_source_manifest.json"))
        for record in terminology["sources"]:
            facts = record["file_facts"]
            data = archive.read("data/Sanasto/" + facts["filename"])
            if hashlib.sha256(data).hexdigest() != facts["sha256"] or len(data) != facts["byte_count"]:
                raise ValueError("Terminology source integrity mismatch")
        disposition = json.loads(archive.read("terminology/adjudication/T1_3_project_owner_disposition.json"))
        if (disposition["t1_status"] != "READY_FOR_G1" or disposition["terminology_blockers_to_g1"] != 0
                or disposition["mandatory_pre_g1_sami_items"] != 0 or disposition["g1_started"]):
            raise ValueError("Closure status mismatch")
        queue = list(csv.reader(io.StringIO(archive.read("terminology/adjudication/T1_2_MINIMAL_SAMI_QUEUE.tsv").decode()), delimiter="\t"))
        if len(queue) != 1:
            raise ValueError("Active Sami items exist")
    return {"zip": path.name, "bytes": path.stat().st_size, "sha256": digest,
            "members": len(names), "member_hashes": "PASS (every member, including audit metadata)",
            "crc": "PASS", "official_sources": f"PASS ({len(official)} frozen files)",
            "terminology_sources": f"PASS ({len(terminology['sources'])} frozen files)",
            "unexpected_files": 0, "nested_archives": 0, "t1_status": "READY_FOR_G1",
            "active_sami_review_count": 0, "pre_g1_terminology_blockers": 0}


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
