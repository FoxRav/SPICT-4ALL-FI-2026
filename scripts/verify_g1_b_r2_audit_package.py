"""Independent verifier for the sealed G1-B R2 correction audit delivery."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

NAME = "SPICT4ALL-FI-G1-B-R2-forward-translation-audit-20260908.zip"
WORK_PACKAGE = "WP-G1-B-CORRECTION-R2-001"
ORIGINAL_RUN_ID = "G1-B-20260908-001"
CORRECTED_RUN_ID = "G1-B-20260908-002"
CORRECTED_CANDIDATES = f"work/agent-b/runs/{CORRECTED_RUN_ID}/candidates.jsonl"
CORRECTED_AUTHORED = f"work/agent-b/runs/{CORRECTED_RUN_ID}/agent_b_translations.json"
CORRECTION_DIFF = f"work/agent-b/runs/{CORRECTED_RUN_ID}/correction_diff.json"
CORRECTION_REPORT = f"work/agent-b/runs/{CORRECTED_RUN_ID}/CORRECTION_REPORT.md"
RUN_METADATA = f"work/agent-b/runs/{CORRECTED_RUN_ID}/run_metadata.json"
VALIDATION_RESULTS = f"work/agent-b/runs/{CORRECTED_RUN_ID}/validation_results.json"
AUTHORIZED_UNITS = [
    "S4A-2026-001",
    "S4A-2026-004",
    "S4A-2026-014",
    "S4A-2026-017",
    "S4A-2026-042",
]
PROJECT_OWNER_WORDINGS = {
    "S4A-2026-001": "terveydentila on heikentynyt",
    "S4A-2026-042": "terveydentila on heikentynyt",
    "S4A-2026-004": "toimintakyky on heikentynyt",
    "S4A-2026-014": "toimintakyky on heikentynyt",
    "S4A-2026-017": "ei ole riittävän hyväkuntoinen syöpähoitoon",
}
HUMAN_TERMINOLOGY = {
    "S4A-2026-001": "T-002",
    "S4A-2026-035": "T-013",
    "S4A-2026-042": "T-002",
    "S4A-2026-049": "T-016",
}

VERIFY_R1_PATH = Path(__file__).resolve().parent / "verify_g1_b_audit_package.py"
SPEC = importlib.util.spec_from_file_location("verify_g1_b_audit_package", VERIFY_R1_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g1_b_audit_package.py")
r1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r1)

REQUIRED_R2_MEMBERS = (
    "work/agent-b/agent_b_translations.json",
    "work/agent-b/candidates.jsonl",
    CORRECTED_CANDIDATES,
    CORRECTED_AUTHORED,
    CORRECTION_DIFF,
    CORRECTION_REPORT,
    RUN_METADATA,
    VALIDATION_RESULTS,
    "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
    "terminology/adjudication/T1_3_project_owner_disposition.json",
    "scripts/build_g1_b_correction_run.py",
    "scripts/validate_g1_b_candidates.py",
    "src/spict4all/forward_candidates.py",
    "src/spict4all/g1_b_correction.py",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "tests/test_adjudication.py",
    "tests/test_g1_b_correction.py",
    "G1_B_R2_AUDIT_SUMMARY.md",
    "G1_B_R2_AUDIT_MANIFEST.json",
    "G1_B_R2_AUDIT_FILE_HASHES.tsv",
    "G1_B_R2_AUDIT_VALIDATION_RESULTS.json",
    "G1_B_R2_GIT_STATE.txt",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def correction_failures(
    original: list[dict[str, Any]],
    corrected: list[dict[str, Any]],
    diff: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if diff.get("changed_unit_ids") != AUTHORIZED_UNITS:
        failures.append(f"correction_diff unit IDs are {diff.get('changed_unit_ids')}")
    if diff.get("unchanged_candidate_fi_count") != 49:
        failures.append("correction_diff unchanged count is not 49")
    original_fi = {row["unit_id"]: row["candidate_fi"] for row in original}
    corrected_fi = {row["unit_id"]: row["candidate_fi"] for row in corrected}
    if set(original_fi) != set(corrected_fi):
        failures.append("original and corrected membership differ")
        return failures
    changed = sorted(unit_id for unit_id, text in original_fi.items() if text != corrected_fi[unit_id])
    if changed != AUTHORIZED_UNITS:
        failures.append(f"candidate_fi changed for {changed}, expected {AUTHORIZED_UNITS}")
    for unit_id in AUTHORIZED_UNITS:
        required = PROJECT_OWNER_WORDINGS[unit_id]
        text = str(corrected_fi.get(unit_id, "")).lower()
        if required not in text:
            failures.append(f"{unit_id}: missing Project Owner wording {required!r}")
        if unit_id in {"S4A-2026-004", "S4A-2026-014"} and "tavanomais" not in text:
            failures.append(f"{unit_id}: usual/tavanomaiset activities scope missing")
    for unit_id, decision in HUMAN_TERMINOLOGY.items():
        row = next((item for item in corrected if item.get("unit_id") == unit_id), None)
        if row is None:
            failures.append(f"{unit_id}: missing from corrected run")
            continue
        g1 = row.get("extensions", {}).get("g1_forward", {})
        applied = g1.get("human_terminology_decisions_applied")
        if not isinstance(applied, list) or decision not in applied:
            failures.append(f"{unit_id}: {decision} not recorded as applied")
        stems = {
            "T-002": ("elinikää lyhent", "terveydentil"),
            "T-013": ("hengityskone",),
            "T-016": ("kokonaisvaltai", "hoito"),
        }[decision]
        lowered = str(row.get("candidate_fi", "")).lower()
        missing = [stem for stem in stems if stem not in lowered]
        if missing:
            failures.append(f"{unit_id}: {decision} stems missing {missing}")
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
            reason = r1.forbidden_member_reason(name)
            if reason:
                raise ValueError(reason)
            if sha256_bytes(archive.read(name)) != hashes[name]:
                raise ValueError(f"Member hash mismatch: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        missing_required = [name for name in REQUIRED_R2_MEMBERS if name not in names]
        if missing_required:
            raise ValueError(f"Required G1-B R2 members missing: {missing_required}")
        independence = r1.independence_failures(names)
        if independence:
            raise ValueError("Independence contamination: " + "; ".join(independence))
        for relative, expected in r1.TRANSLATION_HASHES.items():
            if hashes[relative] != expected:
                raise ValueError(f"Original G1-B-20260908-001 bytes changed: {relative}")
        manifest = json.loads(archive.read("G1_B_R2_AUDIT_MANIFEST.json"))
        if set(manifest["members"]) != set(names):
            raise ValueError("Manifest membership mismatch")
        if manifest.get("work_package") != WORK_PACKAGE:
            raise ValueError("Work-package identity mismatch")
        if manifest.get("actual_model") != r1.ACTUAL_MODEL:
            raise ValueError("Actual model provenance mismatch")
        if manifest.get("configured_role_model") == r1.ACTUAL_MODEL:
            raise ValueError("Configured/planned role model discrepancy was not preserved")
        if manifest.get("corrected_run_id") != CORRECTED_RUN_ID:
            raise ValueError("Corrected run identity mismatch")
        payload_hashes = manifest["payload_sha256"]
        if not isinstance(payload_hashes, dict):
            raise ValueError("Manifest payload_sha256 must be an object")
        for name, value in payload_hashes.items():
            if hashes[str(name)] != value:
                raise ValueError("Manifest payload hash mismatch")
        index = list(
            csv.DictReader(
                io.StringIO(archive.read("G1_B_R2_AUDIT_FILE_HASHES.tsv").decode("utf-8")),
                delimiter="\t",
            )
        )
        if {row["path"] for row in index} != set(names) - {"G1_B_R2_AUDIT_FILE_HASHES.tsv"}:
            raise ValueError("Internal hash index scope mismatch")
        if any(row["sha256"] != hashes[row["path"]] for row in index):
            raise ValueError("Internal hash index mismatch")
        official = json.loads(archive.read("sources/manifests/source_manifest.json"))
        for record in official:
            data = archive.read("sources/official/" + record["filename"])
            if sha256_bytes(data) != record["sha256"] or len(data) != record["bytes"]:
                raise ValueError("Official-source integrity mismatch")
        units = r1.load_jsonl_bytes(archive.read("data/source_units.jsonl"))
        requirements = r1.load_jsonl_bytes(archive.read("data/source_requirements.jsonl"))
        original = r1.load_jsonl_bytes(archive.read("work/agent-b/candidates.jsonl"))
        corrected = r1.load_jsonl_bytes(archive.read(CORRECTED_CANDIDATES))
        original_failures = r1.candidate_evidence_failures(original, units, requirements)
        if original_failures:
            raise ValueError("Original candidate evidence failure: " + "; ".join(original_failures))
        corrected_failures = r1.candidate_evidence_failures(corrected, units, requirements)
        if corrected_failures:
            raise ValueError("Corrected candidate evidence failure: " + "; ".join(corrected_failures))
        diff = json.loads(archive.read(CORRECTION_DIFF))
        wording_failures = correction_failures(original, corrected, diff)
        if wording_failures:
            raise ValueError("Correction failure: " + "; ".join(wording_failures))
        approved = r1.glossary_approved_count(archive.read("terminology/terms.csv").decode("utf-8"))
        if approved != 0:
            raise ValueError(f"Approved glossary rows are {approved}, expected 0")
        authored = json.loads(archive.read(CORRECTED_AUTHORED))
        run = authored["run"]
        if run["model"] != r1.ACTUAL_MODEL:
            raise ValueError("Corrected run model provenance mismatch")
        if run.get("run_id") != CORRECTED_RUN_ID:
            raise ValueError("Corrected authored run_id mismatch")
        if "Claude Opus" in json.dumps(run):
            raise ValueError("Authored run claims Claude Opus produced this translation")
        metadata = json.loads(archive.read(RUN_METADATA))
        if metadata.get("status") == "HUMAN_APPROVED" or metadata.get("run_id") != CORRECTED_RUN_ID:
            raise ValueError("Corrected run metadata identity or approval mismatch")
    return {
        "zip": path.name,
        "bytes": path.stat().st_size,
        "sha256": digest,
        "members": len(names),
        "member_hashes": "PASS (every member, including audit metadata)",
        "crc": "PASS",
        "source_integrity": (
            f"PASS ({len(official)} frozen official files; "
            "original and corrected hashes match frozen units/requirements)"
        ),
        "candidate_coverage": (
            f"PASS ({r1.EXPECTED_CANDIDATE_COUNT}/{r1.EXPECTED_CANDIDATE_COUNT}; "
            f"{r1.CANONICAL_COUNT} canonical + 1 source requirement)"
        ),
        "original_run_unchanged": True,
        "corrected_run_id": CORRECTED_RUN_ID,
        "changed_unit_ids": AUTHORIZED_UNITS,
        "independence_contamination": (
            "PASS (no Agent A, synthesis, back-translation, critic, "
            "or sibling-worktree members)"
        ),
        "approved_glossary_rows": 0,
        "recorded_schema_status": r1.RECORDED_STATUS,
        "human_approval_present": False,
        "actual_model": r1.ACTUAL_MODEL,
        "translation_evidence_unchanged": True,
        "unexpected_files": 0,
        "nested_archives": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False, indent=2))
