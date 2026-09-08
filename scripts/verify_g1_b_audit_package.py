"""Independent standard-library verifier for the sealed G1-B audit delivery."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

NAME = "SPICT4ALL-FI-G1-B-forward-translation-audit-20260908.zip"
WORK_PACKAGE = "WP-G1-B-AUDIT-PACKAGE-001"
EXPECTED_CANDIDATE_COUNT = 54
CANONICAL_COUNT = 53
REQUIREMENT_ID = "S4A-REQ-2026-001"
ACTUAL_MODEL = "Cursor Grok 4.6"
RECORDED_STATUS = "READY_FOR_SYNTHESIS"
TRANSLATION_HASHES = {
    "work/agent-b/agent_b_translations.json": (
        "1d10eb85a0fbad412148e90c2f890a05c473bcf4165b1b3bca99dfbd185a775e"
    ),
    "work/agent-b/candidates.jsonl": (
        "0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640"
    ),
}
REQUIRED_G1_B_MEMBERS = (
    "work/agent-b/agent_b_translations.json",
    "work/agent-b/candidates.jsonl",
    "scripts/build_g1_b_candidates.py",
    "scripts/validate_g1_b_candidates.py",
    "src/spict4all/forward_candidates.py",
    "src/spict4all/g1_forward_runner.py",
    "tests/test_forward_candidates.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "tests/test_adjudication.py",
    "G1_B_AUDIT_SUMMARY.md",
    "G1_B_AUDIT_MANIFEST.json",
    "G1_B_AUDIT_FILE_HASHES.tsv",
    "G1_B_AUDIT_VALIDATION_RESULTS.json",
    "G1_B_GIT_STATE.txt",
)
PLACEHOLDER_ONLY_DIRECTORIES = (
    "work/agent-a/",
    "work/synthesis/",
    "work/backtranslation/",
    "work/critics/",
)
FORBIDDEN_NAME_MARKERS = (
    "g1-forward-a",
    "spict-g1-a",
    "120.spict-g1-a",
)
FORBIDDEN_SUFFIXES = {".zip", ".7z", ".tar", ".gz", ".rar", ".pyc", ".tmp"}
FORBIDDEN_PARTS = {
    ".git",
    ".firecrawl",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules",
}
ALLOWED_README = {
    "data/README.md",
    "sources/official/README.md",
    "sources/reference/README.md",
    "terminology/README.md",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_jsonl_bytes(data: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record {line_number} is not an object")
        records.append(value)
    return records


def forbidden_member_reason(name: str) -> str | None:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or "\\" in name:
        return f"unsafe path: {name}"
    if any(part in FORBIDDEN_PARTS for part in member.parts):
        return f"forbidden directory part: {name}"
    if member.suffix.lower() in FORBIDDEN_SUFFIXES:
        return f"nested or cache archive suffix: {name}"
    if member.name.lower() == "readme.md" and name not in ALLOWED_README:
        return f"unrelated README: {name}"
    lowered = name.lower()
    for marker in FORBIDDEN_NAME_MARKERS:
        if marker in lowered:
            return f"Agent A / sibling marker: {name}"
    for prefix in PLACEHOLDER_ONLY_DIRECTORIES:
        if name.startswith(prefix) and not name.endswith("/.gitkeep"):
            return f"later-gate artifact present: {name}"
    return None


def independence_failures(names: list[str]) -> list[str]:
    failures = [reason for name in names if (reason := forbidden_member_reason(name))]
    for prefix in PLACEHOLDER_ONLY_DIRECTORIES:
        gitkeep = f"{prefix}.gitkeep"
        if gitkeep not in names:
            failures.append(f"missing independence placeholder {gitkeep}")
    return failures


def glossary_approved_count(terms_csv: str) -> int:
    rows = list(csv.DictReader(io.StringIO(terms_csv)))
    return sum(1 for row in rows if row.get("status") == "APPROVED")


def candidate_evidence_failures(
    candidates: list[dict[str, Any]],
    units: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    ids = [str(row.get("unit_id")) for row in candidates]
    if len(ids) != EXPECTED_CANDIDATE_COUNT:
        failures.append(f"candidate count is {len(ids)}, expected {EXPECTED_CANDIDATE_COUNT}")
    if len(ids) != len(set(ids)):
        failures.append("duplicate candidate IDs")
    unit_ids = {str(row["unit_id"]) for row in units}
    req_ids = {
        str(row["requirement_id"])
        for row in requirements
        if row.get("translation_evidence_required") is True
    }
    expected_ids = unit_ids | req_ids
    missing = sorted(expected_ids - set(ids))
    extra = sorted(set(ids) - expected_ids)
    if missing:
        failures.append(f"missing IDs: {missing}")
    if extra:
        failures.append(f"extra IDs: {extra}")
    if len(unit_ids) != CANONICAL_COUNT:
        failures.append(f"canonical count is {len(unit_ids)}, expected {CANONICAL_COUNT}")
    if req_ids != {REQUIREMENT_ID}:
        failures.append(f"source-requirement IDs are {sorted(req_ids)}")
    units_by_id = {str(row["unit_id"]): row for row in units}
    req_by_id = {str(row["requirement_id"]): row for row in requirements}
    approved_statuses = {"HUMAN_APPROVED", "HUMAN_REJECTED"}
    for row in candidates:
        unit_id = str(row.get("unit_id"))
        status = row.get("status")
        candidate = row.get("candidate_fi")
        if not isinstance(candidate, str) or not candidate.strip():
            failures.append(f"{unit_id}: blank Finnish candidate")
        if status in approved_statuses:
            failures.append(f"{unit_id}: unsupported approval state {status}")
        if status != RECORDED_STATUS:
            failures.append(
                f"{unit_id}: recorded status is {status!r}, sealed run used {RECORDED_STATUS}"
            )
        if row.get("model") != ACTUAL_MODEL:
            failures.append(f"{unit_id}: model is {row.get('model')!r}, expected {ACTUAL_MODEL}")
        extensions = row.get("extensions")
        g1 = extensions.get("g1_forward") if isinstance(extensions, dict) else None
        if not isinstance(g1, dict):
            failures.append(f"{unit_id}: missing g1_forward extension")
            continue
        exact = g1.get("exact_source_text_en")
        if unit_id == REQUIREMENT_ID:
            source = req_by_id.get(unit_id)
            if source is None:
                failures.append(f"{unit_id}: missing frozen requirement")
                continue
            if g1.get("source_kind") != "official_change_requirement":
                failures.append(f"{unit_id}: source_kind is not official_change_requirement")
            if source.get("canonical_source_presence") is True:
                failures.append(f"{unit_id}: frozen requirement marked canonical")
            if source.get("final_inclusion_status") != "UNRESOLVED":
                failures.append(f"{unit_id}: frozen requirement is not UNRESOLVED")
            if source.get("publication_blocking") is not True:
                failures.append(f"{unit_id}: publication_blocking lost")
            if exact != source.get("exact_source_text_en"):
                failures.append(f"{unit_id}: exact English differs from frozen requirement")
            if row.get("source_text_sha256") != source.get("exact_text_sha256"):
                failures.append(f"{unit_id}: source_text_sha256 differs from frozen requirement")
        else:
            source = units_by_id.get(unit_id)
            if source is None:
                failures.append(f"{unit_id}: missing frozen canonical unit")
                continue
            if g1.get("source_kind") != "canonical_source_unit":
                failures.append(f"{unit_id}: source_kind is not canonical_source_unit")
            if exact != source.get("source_text_en"):
                failures.append(f"{unit_id}: exact English differs from frozen unit")
            if row.get("source_text_sha256") != source.get("source_text_sha256"):
                failures.append(f"{unit_id}: source_text_sha256 differs from frozen unit")
        if isinstance(exact, str) and sha256_bytes(exact.encode("utf-8")) != row.get(
            "source_text_sha256"
        ):
            failures.append(f"{unit_id}: exact English does not hash to source_text_sha256")
        location = g1.get("source_location")
        if not isinstance(location, dict) or not location:
            failures.append(f"{unit_id}: source provenance location missing")
    title = next((row for row in candidates if row.get("unit_id") == "S4A-2026-000"), None)
    if title is None:
        failures.append("S4A-2026-000 missing")
    else:
        extensions = title.get("extensions")
        g1 = extensions.get("g1_forward") if isinstance(extensions, dict) else {}
        if not isinstance(g1, dict):
            failures.append("S4A-2026-000 missing g1_forward extension")
        else:
            if g1.get("final_inclusion_status") != "UNRESOLVED":
                failures.append("S4A-2026-000 authority is not UNRESOLVED")
            if g1.get("eligible_for_document_insertion") is not False:
                failures.append("S4A-2026-000 is insertable")
    return failures


def verify(path: Path) -> dict[str, Any]:
    expected_zip = path.with_suffix(path.suffix + ".sha256").read_text(encoding="utf-8").split()[0]
    digest = sha256_bytes(path.read_bytes())
    if digest != expected_zip:
        raise ValueError("ZIP SHA-256 mismatch")
    hashes: dict[str, str] = {}
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
            reason = forbidden_member_reason(name)
            if reason:
                raise ValueError(reason)
            if sha256_bytes(archive.read(name)) != hashes[name]:
                raise ValueError(f"Member hash mismatch: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        missing_required = [name for name in REQUIRED_G1_B_MEMBERS if name not in names]
        if missing_required:
            raise ValueError(f"Required G1-B members missing: {missing_required}")
        independence = independence_failures(names)
        if independence:
            raise ValueError("Independence contamination: " + "; ".join(independence))
        for relative, expected in TRANSLATION_HASHES.items():
            if hashes[relative] != expected:
                raise ValueError(f"Translation evidence bytes changed: {relative}")
        manifest = json.loads(archive.read("G1_B_AUDIT_MANIFEST.json"))
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE:
            raise ValueError("Work-package identity mismatch")
        if manifest.get("actual_model") != ACTUAL_MODEL:
            raise ValueError("Actual model provenance mismatch")
        if manifest.get("configured_role_model") == ACTUAL_MODEL:
            raise ValueError("Configured/planned role model discrepancy was not preserved")
        payload_hashes = manifest["payload_sha256"]
        if not isinstance(payload_hashes, dict):
            raise ValueError("Manifest payload_sha256 must be an object")
        for name, value in payload_hashes.items():
            if hashes[str(name)] != value:
                raise ValueError("Manifest payload hash mismatch")
        index = list(
            csv.DictReader(
                io.StringIO(archive.read("G1_B_AUDIT_FILE_HASHES.tsv").decode("utf-8")),
                delimiter="\t",
            )
        )
        if {row["path"] for row in index} != set(names) - {"G1_B_AUDIT_FILE_HASHES.tsv"}:
            raise ValueError("Internal hash index scope mismatch")
        if any(row["sha256"] != hashes[row["path"]] for row in index):
            raise ValueError("Internal hash index mismatch")
        official = json.loads(archive.read("sources/manifests/source_manifest.json"))
        for record in official:
            data = archive.read("sources/official/" + record["filename"])
            if sha256_bytes(data) != record["sha256"] or len(data) != record["bytes"]:
                raise ValueError("Official-source integrity mismatch")
        units = load_jsonl_bytes(archive.read("data/source_units.jsonl"))
        requirements = load_jsonl_bytes(archive.read("data/source_requirements.jsonl"))
        candidates = load_jsonl_bytes(archive.read("work/agent-b/candidates.jsonl"))
        evidence_failures = candidate_evidence_failures(candidates, units, requirements)
        if evidence_failures:
            raise ValueError("Candidate evidence failure: " + "; ".join(evidence_failures))
        approved = glossary_approved_count(
            archive.read("terminology/terms.csv").decode("utf-8")
        )
        if approved != 0:
            raise ValueError(f"Approved glossary rows are {approved}, expected 0")
        authored = json.loads(archive.read("work/agent-b/agent_b_translations.json"))
        run = authored["run"]
        if run["model"] != ACTUAL_MODEL:
            raise ValueError("Authored run model provenance mismatch")
        if "Claude Opus" in json.dumps(run):
            raise ValueError("Authored run claims Claude Opus produced this translation")
    return {
        "zip": path.name,
        "bytes": path.stat().st_size,
        "sha256": digest,
        "members": len(names),
        "member_hashes": "PASS (every member, including audit metadata)",
        "crc": "PASS",
        "source_integrity": (
            f"PASS ({len(official)} frozen official files; "
            "candidate hashes match frozen units/requirements)"
        ),
        "candidate_coverage": (
            f"PASS ({EXPECTED_CANDIDATE_COUNT}/{EXPECTED_CANDIDATE_COUNT}; "
            f"{CANONICAL_COUNT} canonical + 1 source requirement)"
        ),
        "independence_contamination": (
            "PASS (no Agent A, synthesis, back-translation, critic, "
            "or sibling-worktree members)"
        ),
        "approved_glossary_rows": 0,
        "recorded_schema_status": RECORDED_STATUS,
        "human_approval_present": False,
        "actual_model": ACTUAL_MODEL,
        "translation_evidence_unchanged": True,
        "unexpected_files": 0,
        "nested_archives": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
