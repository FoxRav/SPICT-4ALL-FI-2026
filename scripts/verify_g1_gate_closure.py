"""Independent verifier for the sealed G1 gate-closure audit delivery."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

NAME = "SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip"
WORK_PACKAGE = "WP-G1-GATE-CLOSURE-001"
EXPECTED_CANDIDATE_COUNT = 54
CANONICAL_COUNT = 53
REQUIREMENT_ID = "S4A-REQ-2026-001"
TITLE_ID = "S4A-2026-000"
AGENT_A_MODEL = "GPT-6"
AGENT_B_MODEL = "Cursor Grok 4.6"
AGENT_A_CANDIDATES = "work/agent-a/candidates.jsonl"
AGENT_B_ORIGINAL_CANDIDATES = "work/agent-b/candidates.jsonl"
AGENT_B_R2_CANDIDATES = "work/agent-b/runs/G1-B-20260908-002/candidates.jsonl"
CLOSURE_PREFIX = "deliverables/audit/g1-closure/"
REPORT = f"{CLOSURE_PREFIX}G1_GATE_CLOSURE_REPORT.md"
MANIFEST = f"{CLOSURE_PREFIX}G1_GATE_CLOSURE_MANIFEST.json"
INDEX = f"{CLOSURE_PREFIX}G1_GATE_FILE_HASHES.tsv"
VALIDATION = f"{CLOSURE_PREFIX}G1_GATE_VALIDATION_RESULTS.json"
GIT_STATE = f"{CLOSURE_PREFIX}G1_GATE_GIT_STATE.txt"
G1_A_ZIP = "SPICT4ALL-FI-G1-A-forward-translation-audit-20260908.zip"
G1_B_R2_ZIP = "SPICT4ALL-FI-G1-B-R2-forward-translation-audit-20260908.zip"
EXPECTED_CANDIDATE_HASHES = {
    AGENT_A_CANDIDATES: (
        "82d06571c855c87d04e015bf905b1943c5fcd31e68827695fd4cfceb52f4c2cd"
    ),
    AGENT_B_ORIGINAL_CANDIDATES: (
        "0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640"
    ),
    AGENT_B_R2_CANDIDATES: (
        "6033c9970d0b61fd64dfc5c0350b6c97a9ba3cf35725d2f8db7aee79752a25a1"
    ),
}
EXPECTED_UPSTREAM_ZIP_HASHES = {
    G1_A_ZIP: "cfffef8b6adac0586d00c3ca450143626a710ec40cff2b7d99b969f0a7970cd2",
    G1_B_R2_ZIP: "459f79ede3abde0c0e64a9e7c63b4549a4c1911c1bbe702b2f63ec6485729f4b",
}
UPSTREAM_SIDECARS = (
    f"deliverables/audit/{G1_A_ZIP}.sha256",
    f"deliverables/audit/{G1_A_ZIP}.members.sha256",
    f"deliverables/audit/{G1_A_ZIP}.verification.json",
    f"deliverables/audit/{G1_B_R2_ZIP}.sha256",
    f"deliverables/audit/{G1_B_R2_ZIP}.members.sha256",
    f"deliverables/audit/{G1_B_R2_ZIP}.verification.json",
)
REQUIRED_MEMBERS = (
    AGENT_A_CANDIDATES,
    AGENT_B_ORIGINAL_CANDIDATES,
    AGENT_B_R2_CANDIDATES,
    "work/agent-a/run_metadata.json",
    "work/agent-b/runs/G1-B-20260908-002/run_metadata.json",
    "data/source_units.jsonl",
    "data/source_requirements.jsonl",
    "data/canonical_unit_manifest.json",
    "data/canonical_unit_exceptions.jsonl",
    "data/governance_integrity_manifest.json",
    "sources/manifests/source_manifest.json",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "tests/conftest.py",
    "tests/test_g1_t1_isolation.py",
    "tests/test_adjudication.py",
    "scripts/create_g1_gate_closure.py",
    "scripts/verify_g1_gate_closure.py",
    "AGENTS.md",
    "docs/METHODOLOGY.md",
    "docs/WORKFLOW.md",
    "docs/PROJECT_CHARTER.md",
    "config/model_roles.yaml",
    "terminology/terms.csv",
    REPORT,
    MANIFEST,
    INDEX,
    VALIDATION,
    GIT_STATE,
    *UPSTREAM_SIDECARS,
)
LATER_GATE_PREFIXES = (
    "work/synthesis/",
    "work/backtranslation/",
    "work/critics/",
    "work/final/",
    "work/human-review/",
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
APPROVED_STATUSES = {"HUMAN_APPROVED", "HUMAN_REJECTED"}


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
    for prefix in LATER_GATE_PREFIXES:
        if name.startswith(prefix) and not name.endswith("/.gitkeep"):
            return f"later-gate artifact present: {name}"
    return None


def english_and_sha(row: dict[str, Any]) -> tuple[str, str]:
    digest = str(row.get("source_text_sha256") or "")
    extensions = row.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError(f"{row.get('unit_id')}: missing extensions")
    agent_a = extensions.get("g1_agent_a")
    if isinstance(agent_a, dict):
        text = agent_a.get("source_text_en")
        if isinstance(text, str) and text:
            return text, digest
    forward = extensions.get("g1_forward")
    if isinstance(forward, dict):
        text = forward.get("exact_source_text_en")
        if isinstance(text, str) and text:
            return text, digest
    raise ValueError(f"{row.get('unit_id')}: missing exact English source")


def inclusion_and_insertable(row: dict[str, Any]) -> tuple[object, object]:
    extensions = row.get("extensions")
    if not isinstance(extensions, dict):
        return None, None
    agent_a = extensions.get("g1_agent_a")
    if isinstance(agent_a, dict):
        contract = agent_a.get("source_contract")
        if isinstance(contract, dict):
            return contract.get("final_inclusion_status"), contract.get(
                "eligible_for_document_insertion"
            )
    forward = extensions.get("g1_forward")
    if isinstance(forward, dict):
        return forward.get("final_inclusion_status"), forward.get(
            "eligible_for_document_insertion"
        )
    return None, None


def expected_source_index(
    units: list[dict[str, Any]], requirements: list[dict[str, Any]]
) -> dict[str, tuple[str, str]]:
    expected: dict[str, tuple[str, str]] = {}
    for row in units:
        unit_id = str(row["unit_id"])
        expected[unit_id] = (str(row["source_text_en"]), str(row["source_text_sha256"]))
    for row in requirements:
        if row.get("translation_evidence_required") is True:
            req_id = str(row["requirement_id"])
            if req_id in expected:
                raise ValueError(f"duplicate source identifier {req_id}")
            expected[req_id] = (
                str(row["exact_source_text_en"]),
                str(row["exact_text_sha256"]),
            )
    return expected


def candidate_coverage_failures(
    candidates: list[dict[str, Any]],
    expected: dict[str, tuple[str, str]],
    *,
    model: str,
    label: str,
) -> list[str]:
    failures: list[str] = []
    ids = [str(row.get("unit_id")) for row in candidates]
    if len(ids) != EXPECTED_CANDIDATE_COUNT:
        failures.append(f"{label}: candidate count is {len(ids)}")
    if len(ids) != len(set(ids)):
        failures.append(f"{label}: duplicate candidate IDs")
    missing = sorted(set(expected) - set(ids))
    extra = sorted(set(ids) - set(expected))
    if missing:
        failures.append(f"{label}: missing IDs {missing}")
    if extra:
        failures.append(f"{label}: extra IDs {extra}")
    for row in candidates:
        unit_id = str(row.get("unit_id"))
        finnish = row.get("candidate_fi")
        if not isinstance(finnish, str) or not finnish.strip():
            failures.append(f"{label} {unit_id}: blank Finnish candidate")
        if row.get("status") in APPROVED_STATUSES:
            failures.append(f"{label} {unit_id}: unsupported approval state")
        if row.get("model") != model:
            failures.append(f"{label} {unit_id}: model is {row.get('model')!r}")
        try:
            english, digest = english_and_sha(row)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        frozen = expected.get(unit_id)
        if frozen is None:
            continue
        frozen_en, frozen_sha = frozen
        if english != frozen_en:
            failures.append(f"{label} {unit_id}: exact English differs from frozen source")
        if digest != frozen_sha or row.get("source_text_sha256") != frozen_sha:
            failures.append(f"{label} {unit_id}: source SHA differs from frozen source")
        if sha256_bytes(english.encode("utf-8")) != digest:
            failures.append(f"{label} {unit_id}: English does not hash to source SHA")
        if unit_id in {TITLE_ID, REQUIREMENT_ID}:
            status, insertable = inclusion_and_insertable(row)
            if status != "UNRESOLVED":
                failures.append(f"{label} {unit_id}: authority is {status!r}")
            if insertable is not False:
                failures.append(f"{label} {unit_id}: marked insertable")
    return failures


def universe_failures(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> list[str]:
    left_map = {str(row["unit_id"]): english_and_sha(row) for row in left}
    right_map = {str(row["unit_id"]): english_and_sha(row) for row in right}
    failures: list[str] = []
    if set(left_map) != set(right_map):
        failures.append("A and B source IDs differ")
        return failures
    for unit_id in sorted(left_map):
        if left_map[unit_id][0] != right_map[unit_id][0]:
            failures.append(f"{unit_id}: English source differs between A and B")
        if left_map[unit_id][1] != right_map[unit_id][1]:
            failures.append(f"{unit_id}: source SHA differs between A and B")
    return failures


def requirement_authority_failures(requirements: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(requirements) != 1:
        return [f"requirement count is {len(requirements)}"]
    row = requirements[0]
    if row.get("requirement_id") != REQUIREMENT_ID:
        failures.append("requirement_id mismatch")
    if row.get("canonical_source_presence") is True:
        failures.append("requirement marked canonical")
    if row.get("publication_blocking") is not True:
        failures.append("requirement publication_blocking lost")
    if row.get("final_inclusion_status") != "UNRESOLVED":
        failures.append("requirement is not UNRESOLVED")
    return failures


def glossary_approved_count(terms_csv: str) -> int:
    rows = list(csv.DictReader(io.StringIO(terms_csv)))
    return sum(1 for row in rows if row.get("status") == "APPROVED")


def evidence_failures(payload: dict[str, bytes]) -> list[str]:
    failures: list[str] = []
    for name, expected in EXPECTED_CANDIDATE_HASHES.items():
        data = payload.get(name)
        if data is None:
            failures.append(f"candidate file missing: {name}")
            continue
        if sha256_bytes(data) != expected:
            failures.append(f"candidate hash mismatch: {name}")
    units_data = payload.get("data/source_units.jsonl")
    req_data = payload.get("data/source_requirements.jsonl")
    if units_data is None or req_data is None:
        failures.append("frozen source membership files missing")
        return failures
    missing_candidates = [
        name for name in EXPECTED_CANDIDATE_HASHES if name not in payload
    ]
    if missing_candidates:
        return failures
    units = load_jsonl_bytes(units_data)
    requirements = load_jsonl_bytes(req_data)
    if len(units) != CANONICAL_COUNT or len({row["unit_id"] for row in units}) != CANONICAL_COUNT:
        failures.append("canonical unit count is not 53 unique")
    failures += requirement_authority_failures(requirements)
    expected = expected_source_index(units, requirements)
    if len(expected) != EXPECTED_CANDIDATE_COUNT:
        failures.append(f"frozen source universe is {len(expected)}")
    agent_a = load_jsonl_bytes(payload[AGENT_A_CANDIDATES])
    agent_b_r2 = load_jsonl_bytes(payload[AGENT_B_R2_CANDIDATES])
    agent_b_original = load_jsonl_bytes(payload[AGENT_B_ORIGINAL_CANDIDATES])
    failures += candidate_coverage_failures(
        agent_a, expected, model=AGENT_A_MODEL, label="Agent A"
    )
    failures += candidate_coverage_failures(
        agent_b_r2, expected, model=AGENT_B_MODEL, label="Agent B R2"
    )
    failures += candidate_coverage_failures(
        agent_b_original, expected, model=AGENT_B_MODEL, label="Agent B original"
    )
    failures += universe_failures(agent_a, agent_b_r2)
    a_models = {str(row.get("model")) for row in agent_a}
    b_models = {str(row.get("model")) for row in agent_b_r2}
    if a_models != {AGENT_A_MODEL} or b_models != {AGENT_B_MODEL}:
        failures.append("independent model provenance not preserved")
    if a_models & b_models:
        failures.append("A and B share a model identity")
    official_data = payload.get("sources/manifests/source_manifest.json")
    if official_data is None:
        failures.append("sources/manifests/source_manifest.json missing")
        return failures
    official = json.loads(official_data)
    if not isinstance(official, list):
        failures.append("source_manifest.json is not a list")
    else:
        for record in official:
            name = "sources/official/" + str(record["filename"])
            data = payload.get(name)
            if data is None:
                failures.append(f"official source missing: {name}")
                continue
            if sha256_bytes(data) != record["sha256"] or len(data) != record["bytes"]:
                failures.append(f"official source mismatch: {name}")
    terms = payload.get("terminology/terms.csv")
    if terms is None:
        failures.append("terminology/terms.csv missing")
    else:
        approved = glossary_approved_count(terms.decode("utf-8"))
        if approved != 0:
            failures.append(f"approved glossary rows are {approved}")
    return failures


def gate_payload_failures(payload: dict[str, bytes]) -> list[str]:
    failures: list[str] = []
    for name in REQUIRED_MEMBERS:
        if name not in payload:
            failures.append(f"required member missing: {name}")
    for name in payload:
        reason = forbidden_member_reason(name)
        if reason:
            failures.append(reason)
    for sidecar, zip_name in (
        (UPSTREAM_SIDECARS[0], G1_A_ZIP),
        (UPSTREAM_SIDECARS[3], G1_B_R2_ZIP),
    ):
        data = payload.get(sidecar)
        if data is None:
            continue
        recorded = data.decode("utf-8").split()[0]
        if recorded != EXPECTED_UPSTREAM_ZIP_HASHES[zip_name]:
            failures.append(f"sidecar ZIP hash mismatch: {sidecar}")
    failures += evidence_failures(payload)
    return failures


def live_evidence_payload(root: Path) -> dict[str, bytes]:
    names = [
        *EXPECTED_CANDIDATE_HASHES,
        "data/source_units.jsonl",
        "data/source_requirements.jsonl",
        "data/canonical_unit_manifest.json",
        "data/canonical_unit_exceptions.jsonl",
        "data/governance_integrity_manifest.json",
        "sources/manifests/source_manifest.json",
        "terminology/terms.csv",
    ]
    official = json.loads(
        (root / "sources/manifests/source_manifest.json").read_text(encoding="utf-8")
    )
    for record in official:
        names.append("sources/official/" + str(record["filename"]))
    payload: dict[str, bytes] = {}
    for name in names:
        path = root / name
        if path.is_file():
            payload[name] = path.read_bytes()
    return payload


def later_gate_files(root: Path) -> list[str]:
    found: list[str] = []
    for prefix in LATER_GATE_PREFIXES:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                found.append(path.relative_to(root).as_posix())
    return found


def verify_upstream_zip_files(root: Path) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for zip_name, expected in EXPECTED_UPSTREAM_ZIP_HASHES.items():
        path = root / "deliverables/audit" / zip_name
        digest = sha256_bytes(path.read_bytes())
        sidecar = (root / "deliverables/audit" / zip_name).with_name(zip_name + ".sha256")
        recorded = sidecar.read_text(encoding="utf-8").split()[0]
        if digest != expected or recorded != expected:
            raise ValueError(f"upstream ZIP hash mismatch: {zip_name}")
        records[zip_name] = {
            "path": f"deliverables/audit/{zip_name}",
            "sha256": digest,
            "bytes": path.stat().st_size,
            "verification_status": "PASS",
            "nested_in_closure_zip": False,
        }
    return records


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
        failures = gate_payload_failures(payload)
        if failures:
            raise ValueError("Gate evidence failure: " + "; ".join(failures))
        manifest = json.loads(payload[MANIFEST])
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE:
            raise ValueError("Work-package identity mismatch")
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
        "agent_a_coverage": f"PASS ({EXPECTED_CANDIDATE_COUNT}/{EXPECTED_CANDIDATE_COUNT}; {CANONICAL_COUNT} canonical + 1 source requirement)",
        "agent_b_r2_coverage": f"PASS ({EXPECTED_CANDIDATE_COUNT}/{EXPECTED_CANDIDATE_COUNT}; {CANONICAL_COUNT} canonical + 1 source requirement)",
        "source_universe_equality": "PASS",
        "candidate_hashes": "PASS",
        "upstream_audit_zips": "PASS (hashed and recorded; not nested)",
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "g2_started": False,
        "agent_a_model": AGENT_A_MODEL,
        "agent_b_model": AGENT_B_MODEL,
        "unexpected_files": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
