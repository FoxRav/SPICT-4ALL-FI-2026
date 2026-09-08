"""Independent verifier for the sealed G2 synthesis audit delivery."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from spict4all.g2_synthesis import (
    ACTUAL_MODEL,
    AGENT_A_ARTIFACT,
    AGENT_B_R2_ARTIFACT,
    EXPECTED_AGREE,
    EXPECTED_COUNT,
    EXPECTED_DISAGREE,
    FROZEN_INPUT_HASHES,
    G2_RUN_DIR,
    G2_RUN_ID,
    SAME_FAMILY_LIMITATION,
    expected_source_index,
    g2_failures,
    load_jsonl_records,
)

NAME = "SPICT4ALL-FI-G2-synthesis-audit-20260908.zip"
WORK_PACKAGE = "WP-G2-SYNTHESIS-001"
G1_GATE_ZIP = "SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip"
G1_GATE_SIDECARS = (
    f"deliverables/audit/{G1_GATE_ZIP}.sha256",
    f"deliverables/audit/{G1_GATE_ZIP}.members.sha256",
    f"deliverables/audit/{G1_GATE_ZIP}.verification.json",
)
RUN_PREFIX = G2_RUN_DIR.as_posix()
CANDIDATES = f"{RUN_PREFIX}/candidates.jsonl"
DECISIONS = f"{RUN_PREFIX}/synthesis_decisions.jsonl"
RUN_METADATA = f"{RUN_PREFIX}/run_metadata.json"
REPORT = f"{RUN_PREFIX}/G2_SYNTHESIS_REPORT.md"
RUN_VALIDATION = f"{RUN_PREFIX}/validation_results.json"
MANIFEST = "G2_SYNTHESIS_AUDIT_MANIFEST.json"
INDEX = "G2_SYNTHESIS_AUDIT_FILE_HASHES.tsv"
VALIDATION = "G2_SYNTHESIS_AUDIT_VALIDATION_RESULTS.json"
GIT_STATE = "G2_SYNTHESIS_AUDIT_GIT_STATE.txt"
REQUIRED_MEMBERS = (
    CANDIDATES,
    DECISIONS,
    RUN_METADATA,
    REPORT,
    RUN_VALIDATION,
    AGENT_A_ARTIFACT,
    AGENT_B_R2_ARTIFACT,
    "work/agent-b/candidates.jsonl",
    "data/source_units.jsonl",
    "data/source_requirements.jsonl",
    "data/canonical_unit_manifest.json",
    "data/canonical_unit_exceptions.jsonl",
    "data/governance_integrity_manifest.json",
    "sources/manifests/source_manifest.json",
    "terminology/terms.csv",
    "terminology/adjudication/human_terminology_decisions.tsv",
    "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
    "terminology/adjudication/T1_3_project_owner_disposition.json",
    "src/spict4all/g2_synthesis.py",
    "src/spict4all/g2_authored.py",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "scripts/build_g2_synthesis_run.py",
    "scripts/validate_g2_synthesis.py",
    "scripts/create_g2_synthesis_audit.py",
    "scripts/verify_g2_synthesis_audit.py",
    "tests/test_g2_synthesis.py",
    "tests/test_g1_t1_isolation.py",
    "tests/conftest.py",
    "config/model_roles.yaml",
    "AGENTS.md",
    MANIFEST,
    INDEX,
    VALIDATION,
    GIT_STATE,
    *G1_GATE_SIDECARS,
)
FORBIDDEN_SUFFIXES = {".zip", ".7z", ".tar", ".gz", ".rar", ".pyc", ".tmp"}
FORBIDDEN_PARTS = {
    ".git",
    ".firecrawl",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
}
LATER_GATE_PREFIXES = (
    "work/backtranslation/",
    "work/critics/",
    "work/final/",
    "work/human-review/",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def forbidden_member_reason(name: str) -> str | None:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or "\\" in name:
        return f"unsafe path: {name}"
    if any(part in FORBIDDEN_PARTS for part in member.parts):
        return f"forbidden directory part: {name}"
    if member.suffix.lower() in FORBIDDEN_SUFFIXES:
        return f"nested or cache archive suffix: {name}"
    for prefix in LATER_GATE_PREFIXES:
        if name.startswith(prefix) and not name.endswith("/.gitkeep"):
            return f"later-gate artifact present: {name}"
    return None


def payload_failures(payload: dict[str, bytes]) -> list[str]:
    failures: list[str] = []
    for name in REQUIRED_MEMBERS:
        if name not in payload:
            failures.append(f"required member missing: {name}")
    for name in payload:
        reason = forbidden_member_reason(name)
        if reason:
            failures.append(reason)
    for relative, expected in FROZEN_INPUT_HASHES.items():
        if relative == f"deliverables/audit/{G1_GATE_ZIP}":
            sidecar = payload.get(G1_GATE_SIDECARS[0])
            if sidecar is None:
                failures.append("G1 gate ZIP sidecar missing")
                continue
            recorded = sidecar.decode("utf-8").split()[0]
            if recorded != expected:
                failures.append("G1 gate ZIP sidecar hash mismatch")
            continue
        data = payload.get(relative)
        if data is None:
            failures.append(f"frozen input missing from ZIP: {relative}")
            continue
        if sha256_bytes(data) != expected:
            failures.append(f"frozen input hash mismatch: {relative}")
    if any(name not in payload for name in (CANDIDATES, DECISIONS, "data/source_units.jsonl")):
        return failures
    units = load_jsonl_records(payload["data/source_units.jsonl"].decode("utf-8"))
    requirements = load_jsonl_records(
        payload["data/source_requirements.jsonl"].decode("utf-8")
    )
    expected = expected_source_index(units, requirements)
    candidates = load_jsonl_records(payload[CANDIDATES].decode("utf-8"))
    decisions = load_jsonl_records(payload[DECISIONS].decode("utf-8"))
    agent_a = load_jsonl_records(payload[AGENT_A_ARTIFACT].decode("utf-8"))
    agent_b = load_jsonl_records(payload[AGENT_B_R2_ARTIFACT].decode("utf-8"))
    failures.extend(g2_failures(candidates, decisions, expected, agent_a, agent_b))
    report = payload[REPORT].decode("utf-8")
    if ACTUAL_MODEL not in report:
        failures.append("audit report model identity missing")
    if SAME_FAMILY_LIMITATION not in report:
        failures.append("same-family limitation missing from report")
    if "HUMAN_APPROVED" in report:
        failures.append("report claims HUMAN_APPROVED")
    metadata = json.loads(payload[RUN_METADATA].decode("utf-8"))
    if metadata.get("actual_model") != ACTUAL_MODEL:
        failures.append("run metadata actual_model mismatch")
    if metadata.get("same_family_limitation") != SAME_FAMILY_LIMITATION:
        failures.append("run metadata same-family limitation missing")
    if ACTUAL_MODEL not in str(metadata.get("role", "")):
        failures.append("run metadata role omits Cursor Grok 4.6")
    agree = sum(
        1
        for row in decisions
        if row.get("classification") == "A_B_AGREE"
    )
    if agree != EXPECTED_AGREE:
        failures.append(f"A_B_AGREE count is {agree}")
    disagree = EXPECTED_COUNT - agree
    if disagree != EXPECTED_DISAGREE:
        failures.append(f"disagreement count is {disagree}")
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
        payload = {name: archive.read(name) for name in names}
        for name in names:
            if sha256_bytes(payload[name]) != hashes[name]:
                raise ValueError(f"Member hash mismatch: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        nested = [name for name in names if name.lower().endswith(".zip")]
        if nested:
            raise ValueError(f"nested ZIP members: {nested}")
        failures = payload_failures(payload)
        if failures:
            raise ValueError("G2 audit evidence failure: " + "; ".join(failures))
        manifest = json.loads(payload[MANIFEST])
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE:
            raise ValueError("Work-package identity mismatch")
        if manifest.get("actual_model") != ACTUAL_MODEL:
            raise ValueError("Manifest actual_model mismatch")
        if manifest.get("g2_run_id") != G2_RUN_ID:
            raise ValueError("Manifest run_id mismatch")
        payload_hashes = manifest["payload_sha256"]
        if not isinstance(payload_hashes, dict):
            raise ValueError("Manifest payload_sha256 must be an object")
        for name, value in payload_hashes.items():
            if hashes[str(name)] != value:
                raise ValueError("Manifest payload hash mismatch")
        index = list(
            csv.DictReader(
                io.StringIO(payload[INDEX].decode("utf-8")),
                delimiter="\t",
            )
        )
        if {row["path"] for row in index} != set(names) - {INDEX}:
            raise ValueError("Internal hash index scope mismatch")
        if any(row["sha256"] != hashes[row["path"]] for row in index):
            raise ValueError("Internal hash index mismatch")
    return {
        "zip": path.name,
        "bytes": path.stat().st_size,
        "sha256": digest,
        "members": len(names),
        "member_hashes": "PASS (every member, including audit metadata)",
        "crc": "PASS",
        "manifest_membership": "PASS",
        "nested_archives": 0,
        "coverage": f"PASS ({EXPECTED_COUNT}/{EXPECTED_COUNT})",
        "canonical_plus_requirement": "PASS (53 canonical + 1 source requirement)",
        "a_b_agreements": EXPECTED_AGREE,
        "a_b_disagreements": EXPECTED_DISAGREE,
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "g3_started": False,
        "actual_model": ACTUAL_MODEL,
        "same_family_limitation_recorded": True,
        "title_authority_unresolved": True,
        "requirement_noncanonical_unresolved": True,
        "agent_a_unchanged": True,
        "agent_b_unchanged": True,
        "g1_gate_zip_nested": False,
        "unexpected_files": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
