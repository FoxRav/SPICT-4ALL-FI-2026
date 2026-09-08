"""Independent verifier for the sealed G4 independent-critics audit delivery."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from spict4all.g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_ACTUAL_MODEL,
    CRITIC_A_PROVENANCE_LIMITATION,
    CRITIC_A_RELATIVE,
    CRITIC_B_ACTUAL_MODEL,
    CRITIC_B_RELATIVE,
    EXPECTED_A_ISSUE,
    EXPECTED_B_ISSUE,
    EXPECTED_B_ONLY,
    EXPECTED_CORROBORATED,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    G4_RUN_DIR,
    G4_RUN_ID,
    INDEPENDENCE_STATEMENT,
    REPORT_RELATIVE,
    REVIEW_INPUT_RELATIVE,
    SAME_FAMILY_LIMITATION,
    WORK_PACKAGE,
    build_combined_findings,
    encode_combined_row,
    issue_ids,
    load_jsonl_records,
    status_groups,
)

NAME = "SPICT4ALL-FI-G4-independent-critics-audit-20260908.zip"
WORK_PACKAGE_NAME = WORK_PACKAGE
RUN_PREFIX = G4_RUN_DIR.as_posix()
RUN_METADATA = f"{RUN_PREFIX}/run_metadata.json"
REPORT = REPORT_RELATIVE
RUN_VALIDATION = f"{RUN_PREFIX}/validation_results.json"
MANIFEST = "G4_INDEPENDENT_CRITICS_AUDIT_MANIFEST.json"
INDEX = "G4_INDEPENDENT_CRITICS_AUDIT_FILE_HASHES.tsv"
VALIDATION = "G4_INDEPENDENT_CRITICS_AUDIT_VALIDATION_RESULTS.json"
GIT_STATE = "G4_INDEPENDENT_CRITICS_AUDIT_GIT_STATE.txt"
REQUIRED_MEMBERS = (
    REVIEW_INPUT_RELATIVE,
    CRITIC_A_RELATIVE,
    CRITIC_B_RELATIVE,
    COMBINED_RELATIVE,
    RUN_METADATA,
    REPORT,
    RUN_VALIDATION,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    "src/spict4all/g4_critics.py",
    "src/spict4all/g1_t1_isolation.py",
    "scripts/write_g4_critics_metadata.py",
    "scripts/validate_g4_critics.py",
    "scripts/create_g4_critics_audit.py",
    "scripts/verify_g4_critics_audit.py",
    "tests/test_g4_critics.py",
    "config/model_roles.yaml",
    "README.md",
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
FORBIDDEN_PREFIXES = (
    "work/final/",
    "work/human-review/",
    "deliverables/audit/",
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
    for prefix in FORBIDDEN_PREFIXES:
        if name.startswith(prefix) and not name.endswith("/.gitkeep"):
            return f"forbidden later-gate or historical audit path: {name}"
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
    for relative, expected in EXPECTED_HASHES.items():
        data = payload.get(relative)
        if data is None:
            continue
        if sha256_bytes(data) != expected:
            failures.append(f"frozen hash mismatch: {relative}")
    needed = (
        REVIEW_INPUT_RELATIVE,
        CRITIC_A_RELATIVE,
        CRITIC_B_RELATIVE,
        G2_CANDIDATES_RELATIVE,
        G3_BACK_RELATIVE,
        COMBINED_RELATIVE,
        REPORT,
    )
    if any(name not in payload for name in needed):
        return failures
    review = load_jsonl_records(payload[REVIEW_INPUT_RELATIVE].decode("utf-8"))
    critic_a = load_jsonl_records(payload[CRITIC_A_RELATIVE].decode("utf-8"))
    critic_b = load_jsonl_records(payload[CRITIC_B_RELATIVE].decode("utf-8"))
    g2 = load_jsonl_records(payload[G2_CANDIDATES_RELATIVE].decode("utf-8"))
    back = load_jsonl_records(payload[G3_BACK_RELATIVE].decode("utf-8"))
    combined = build_combined_findings(review, critic_a, critic_b, g2, back)
    expected_text = "".join(encode_combined_row(row) for row in combined)
    if payload[COMBINED_RELATIVE].decode("utf-8") != expected_text:
        failures.append("packaged combined_findings is not the deterministic consolidation")
    groups = status_groups(combined)
    if tuple(groups["CORROBORATED"]) != EXPECTED_CORROBORATED:
        failures.append("packaged corroborated IDs mismatch")
    if groups["CRITIC_A_ONLY"]:
        failures.append("packaged critic-A-only findings present")
    if tuple(groups["CRITIC_B_ONLY"]) != EXPECTED_B_ONLY:
        failures.append("packaged critic-B-only IDs mismatch")
    if len(issue_ids(critic_a)) != EXPECTED_A_ISSUE:
        failures.append("packaged critic-a ISSUE count mismatch")
    if len(issue_ids(critic_b)) != EXPECTED_B_ISSUE:
        failures.append("packaged critic-b ISSUE count mismatch")
    report = payload[REPORT].decode("utf-8")
    if INDEPENDENCE_STATEMENT not in report:
        failures.append("report omits independence statement")
    if CRITIC_A_PROVENANCE_LIMITATION not in report:
        failures.append("report omits Critic A provenance limitation")
    if SAME_FAMILY_LIMITATION not in report:
        failures.append("report omits same-family limitation")
    if "does not adjudicate" not in report or "does not revise Finnish wording" not in report:
        failures.append("report does not disclaim adjudication/revision")
    if "G4 PASS" in report or "HUMAN_APPROVED" in report:
        failures.append("report claims G4 PASS or HUMAN_APPROVED")
    readme = payload["README.md"].decode("utf-8")
    if "G4 independent review is in progress" not in readme:
        failures.append("README is not G4 in progress")
    if "G4 PASS" in readme:
        failures.append("README claims G4 PASS")
    metadata = json.loads(payload[RUN_METADATA].decode("utf-8"))
    if metadata.get("critic_a_actual_model") != CRITIC_A_ACTUAL_MODEL:
        failures.append("run metadata critic_a_actual_model mismatch")
    if metadata.get("critic_b_actual_model") != CRITIC_B_ACTUAL_MODEL:
        failures.append("run metadata critic_b_actual_model mismatch")
    if metadata.get("g5_created") is not False:
        failures.append("run metadata claims G5 created")
    manifest = json.loads(payload[MANIFEST].decode("utf-8"))
    if manifest.get("g2_candidates_sha256") != EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]:
        failures.append("manifest G2 candidates hash mismatch")
    if manifest.get("g3_back_translation_sha256") != EXPECTED_HASHES[G3_BACK_RELATIVE]:
        failures.append("manifest G3 back-translation hash mismatch")
    if len(review) != EXPECTED_COUNT:
        failures.append(f"review input count is {len(review)}")
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
            raise ValueError("G4 audit evidence failure: " + "; ".join(failures))
        manifest = json.loads(payload[MANIFEST])
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE_NAME:
            raise ValueError("Work-package identity mismatch")
        if manifest.get("g4_run_id") != G4_RUN_ID:
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
        "corroborated": len(EXPECTED_CORROBORATED),
        "critic_a_only": 0,
        "critic_b_only": len(EXPECTED_B_ONLY),
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "finnish_revised": False,
        "g5_created": False,
        "g4_pass_claimed": False,
        "critic_a_actual_model": CRITIC_A_ACTUAL_MODEL,
        "critic_b_actual_model": CRITIC_B_ACTUAL_MODEL,
        "unexpected_files": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
