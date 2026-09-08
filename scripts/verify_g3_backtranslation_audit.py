"""Independent verifier for the sealed G3 blind back-translation audit delivery."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from spict4all.g3_backtranslation import (
    ACTUAL_MODEL,
    BACK_TRANSLATION_RELATIVE,
    BLIND_INPUT_RELATIVE,
    ENVIRONMENT,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_RUN_DIR,
    G3_RUN_ID,
    REASONING_EFFORT,
    derivation_failures,
    g2_fi_by_id,
    g3_pair_failures,
    load_jsonl_records,
)

NAME = "SPICT4ALL-FI-G3-blind-backtranslation-audit-20260908.zip"
WORK_PACKAGE = "WP-G3-BLIND-BACKTRANSLATION-AUDIT-001"
RUN_PREFIX = G3_RUN_DIR.as_posix()
RUN_METADATA = f"{RUN_PREFIX}/run_metadata.json"
REPORT = f"{RUN_PREFIX}/G3_BACKTRANSLATION_REPORT.md"
RUN_VALIDATION = f"{RUN_PREFIX}/validation_results.json"
FI_EXTRACT = "G3_G2_CANDIDATE_FI_ONLY.jsonl"
MANIFEST = "G3_BACKTRANSLATION_AUDIT_MANIFEST.json"
INDEX = "G3_BACKTRANSLATION_AUDIT_FILE_HASHES.tsv"
VALIDATION = "G3_BACKTRANSLATION_AUDIT_VALIDATION_RESULTS.json"
GIT_STATE = "G3_BACKTRANSLATION_AUDIT_GIT_STATE.txt"
REQUIRED_MEMBERS = (
    BLIND_INPUT_RELATIVE,
    BACK_TRANSLATION_RELATIVE,
    RUN_METADATA,
    REPORT,
    RUN_VALIDATION,
    FI_EXTRACT,
    "src/spict4all/g3_backtranslation.py",
    "src/spict4all/g1_t1_isolation.py",
    "scripts/write_g3_backtranslation_metadata.py",
    "scripts/validate_g3_backtranslation.py",
    "scripts/create_g3_backtranslation_audit.py",
    "scripts/verify_g3_backtranslation_audit.py",
    "tests/test_g3_backtranslation.py",
    "config/model_roles.yaml",
    "AGENTS.md",
    MANIFEST,
    INDEX,
    VALIDATION,
    GIT_STATE,
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
FORBIDDEN_CONTENT_PREFIXES = (
    "work/agent-a/",
    "work/agent-b/",
    "work/synthesis/",
    "data/source_units",
    "sources/official/",
)
LATER_GATE_PREFIXES = (
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
    for prefix in FORBIDDEN_CONTENT_PREFIXES:
        if name.startswith(prefix):
            return f"non-blind content present: {name}"
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
    for relative in (BLIND_INPUT_RELATIVE, BACK_TRANSLATION_RELATIVE):
        data = payload.get(relative)
        if data is None:
            continue
        if sha256_bytes(data) != EXPECTED_HASHES[relative]:
            failures.append(f"frozen hash mismatch: {relative}")
    if any(
        name not in payload
        for name in (BLIND_INPUT_RELATIVE, BACK_TRANSLATION_RELATIVE, FI_EXTRACT)
    ):
        return failures
    blind = load_jsonl_records(payload[BLIND_INPUT_RELATIVE].decode("utf-8"))
    back = load_jsonl_records(payload[BACK_TRANSLATION_RELATIVE].decode("utf-8"))
    extract = load_jsonl_records(payload[FI_EXTRACT].decode("utf-8"))
    failures.extend(g3_pair_failures(blind, back))
    failures.extend(derivation_failures(blind, g2_fi_by_id(extract)))
    report = payload[REPORT].decode("utf-8")
    if ACTUAL_MODEL not in report:
        failures.append("report omits actual model")
    if "no semantic comparison" not in report.lower():
        failures.append("report does not disclaim source semantic comparison")
    if "HUMAN_APPROVED" in report:
        failures.append("report claims HUMAN_APPROVED")
    metadata = json.loads(payload[RUN_METADATA].decode("utf-8"))
    if metadata.get("actual_model") != ACTUAL_MODEL:
        failures.append("run metadata actual_model mismatch")
    if metadata.get("reasoning_effort") != REASONING_EFFORT:
        failures.append("run metadata reasoning_effort mismatch")
    if metadata.get("environment") != ENVIRONMENT:
        failures.append("run metadata environment mismatch")
    manifest = json.loads(payload[MANIFEST].decode("utf-8"))
    if manifest.get("g2_candidates_sha256") != EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]:
        failures.append("manifest G2 candidates hash mismatch")
    if G2_CANDIDATES_RELATIVE in payload:
        failures.append("full G2 candidates were packaged")
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
            raise ValueError("G3 audit evidence failure: " + "; ".join(failures))
        manifest = json.loads(payload[MANIFEST])
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE:
            raise ValueError("Work-package identity mismatch")
        if manifest.get("actual_model") != ACTUAL_MODEL:
            raise ValueError("Manifest actual_model mismatch")
        if manifest.get("g3_run_id") != G3_RUN_ID:
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
        "id_order_match": True,
        "g2_candidate_fi_derivation": "PASS",
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "semantic_comparison_with_source_performed": False,
        "g4_started": False,
        "actual_model": ACTUAL_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "environment": ENVIRONMENT,
        "unexpected_files": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
