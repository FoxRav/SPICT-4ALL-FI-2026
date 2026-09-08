"""Seal the G2 synthesis audit package. Historical G1/T1 evidence is never rewritten."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from spict4all.g2_synthesis import (
    ACTUAL_MODEL,
    AGENT_A_MODEL,
    AGENT_B_MODEL,
    EXPECTED_AGREE,
    EXPECTED_COUNT,
    EXPECTED_DISAGREE,
    FROZEN_INPUT_HASHES,
    G2_RUN_ID,
    SAME_FAMILY_LIMITATION,
    classification_counts,
    g2_run_failures,
    load_g2_run,
    verify_frozen_inputs,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g2_synthesis_audit.py"
SPEC = importlib.util.spec_from_file_location("verify_g2_synthesis_audit", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g2_synthesis_audit.py")
verify_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mod)

NAME = verify_mod.NAME
FIXED_TIME = (2026, 9, 8, 0, 0, 0)
T1_BASELINE = "2aa066fdba27fa083ff9ad78f285c0751d3f085f"
T1_FILES = (
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "tests/test_adjudication.py",
)
NAMED_FILES = (
    "AGENTS.md",
    "pyproject.toml",
    "tools.ps1",
    "docs/METHODOLOGY.md",
    "docs/WORKFLOW.md",
    "docs/MODEL_STRATEGY.md",
    "docs/PROJECT_CHARTER.md",
    "config/model_roles.yaml",
    "config/project.yaml",
    "config/quality_gates.yaml",
    "data/source_units.jsonl",
    "data/source_units.tsv",
    "data/source_requirements.jsonl",
    "data/canonical_unit_manifest.json",
    "data/canonical_unit_exceptions.jsonl",
    "data/governance_integrity_manifest.json",
    "sources/official/README.md",
    "sources/reference/README.md",
    "sources/manifests/source_manifest.json",
    "terminology/terms.csv",
    "terminology/adjudication/human_terminology_decisions.tsv",
    "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
    "terminology/adjudication/T1_3_project_owner_disposition.json",
    "schemas/translation_candidate.schema.json",
    "src/spict4all/g2_synthesis.py",
    "src/spict4all/g2_authored.py",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "src/spict4all/hashing.py",
    "tests/conftest.py",
    "tests/test_g1_t1_isolation.py",
    "tests/test_g2_synthesis.py",
    "tests/test_adjudication.py",
    "work/agent-a/candidates.jsonl",
    "work/agent-b/candidates.jsonl",
    "work/agent-b/runs/G1-B-20260908-002/candidates.jsonl",
    "work/synthesis/G2-20260908-001/candidates.jsonl",
    "work/synthesis/G2-20260908-001/synthesis_decisions.jsonl",
    "work/synthesis/G2-20260908-001/run_metadata.json",
    "work/synthesis/G2-20260908-001/G2_SYNTHESIS_REPORT.md",
    "work/synthesis/G2-20260908-001/validation_results.json",
    "scripts/build_g2_synthesis_run.py",
    "scripts/validate_g2_synthesis.py",
    "scripts/create_g2_synthesis_audit.py",
    "scripts/verify_g2_synthesis_audit.py",
    *verify_mod.G1_GATE_SIDECARS,
)
SECRET_PATTERNS = (
    rb"sk-[A-Za-z0-9_-]{24,}",
    rb"gh[pousr]_[A-Za-z0-9]{30,}",
    rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
)


def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_t1_baseline() -> None:
    result = subprocess.run(
        ["git", "--no-pager", "diff", "--exit-code", T1_BASELINE, "--", *T1_FILES],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise ValueError("Historical T1 validator files diverged from baseline 2aa066f")


def later_gate_files(root: Path) -> list[str]:
    found: list[str] = []
    for prefix in verify_mod.LATER_GATE_PREFIXES:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name != ".gitkeep":
                found.append(path.relative_to(root).as_posix())
    return found


def collect() -> dict[str, bytes]:
    selected: set[Path] = set()
    for relative in NAMED_FILES:
        selected.add(ROOT / relative)
    selected.update(path for path in (ROOT / "work").rglob(".gitkeep") if path.is_file())
    for record in json.loads(
        (ROOT / "sources/manifests/source_manifest.json").read_text(encoding="utf-8")
    ):
        selected.add(ROOT / "sources/official" / record["filename"])
    payload: dict[str, bytes] = {}
    for path in sorted(selected):
        if not path.is_file():
            raise ValueError(f"Required input missing: {path.relative_to(ROOT).as_posix()}")
        name = path.relative_to(ROOT).as_posix()
        if any(
            part in {".git", ".firecrawl", "__pycache__", "node_modules", ".venv"}
            for part in name.split("/")
        ):
            raise ValueError(f"Unexpected cache path: {name}")
        if name.lower().endswith((".zip", ".tmp", ".pyc")):
            raise ValueError(f"Excluded artifact selected: {name}")
        data = path.read_bytes()
        if path.suffix in {".py", ".json", ".jsonl", ".md", ".txt", ".yaml", ".tsv", ".csv"}:
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, data):
                    raise ValueError(f"Potential credential material in {name}")
        payload[name] = data
    return payload


def commands() -> list[list[str]]:
    result = [
        ["scripts/validate_g2_synthesis.py"],
        ["-m", "pytest", "-p", "no:cacheprovider"],
    ]
    result += [
        ["-m", "spict4all.cli", "--root", ".", task]
        for task in (
            "verify-sources",
            "validate-requirements",
            "validate-canonical",
            "validate-governance",
            "validate-terminology",
        )
    ]
    result += [
        ["-m", "compileall", "-q", "src", "scripts", "tests"],
        ["-m", "mypy", "--strict", "src/spict4all"],
        ["-m", "ruff", "check", "src", "scripts", "tests"],
    ]
    return result


def validate_tree(tree: Path, label: str) -> dict[str, Any]:
    environment = dict(
        os.environ,
        PYTHONPATH=str(tree / "src"),
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
    )
    records: list[dict[str, Any]] = []
    for arguments in commands():
        process = subprocess.run(
            [sys.executable, *arguments],
            cwd=tree,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        records.append(
            {
                "command": ["python", *arguments],
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        )
        print(label, " ".join(arguments), process.returncode, flush=True)
        if process.returncode:
            print(process.stdout[-5000:], process.stderr[-2000:], flush=True)
            raise ValueError(f"{label} validation failed")
    match = re.search(r"(\d+) passed", records[1]["stdout"])
    if not match:
        raise ValueError("No test pass count")
    return {
        "scope": label,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "tests_passed": int(match.group(1)),
        "all_commands_passed": True,
        "commands": records,
    }


def run_verifier(archive: Path) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(VERIFY_PATH), str(archive)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if process.returncode:
        raise ValueError(process.stderr or process.stdout)
    return json.loads(process.stdout)


def git_state() -> bytes:
    blocks: list[str] = []
    for arguments in (
        ["rev-parse", "HEAD"],
        ["branch", "--show-current"],
        ["status", "--short", "--untracked-files=all"],
    ):
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode:
            raise ValueError("Git state capture failed")
        blocks += ["git " + " ".join(arguments), result.stdout]
    return (
        "\n".join(blocks)
        + "\nNo commit performed. No push performed. G3 was not started.\n"
        "Actual G2 model: Cursor Grok 4.6. Agent A and Agent B evidence were not modified.\n"
    ).encode()


def main() -> None:
    destination = ROOT / "deliverables/audit" / NAME
    companions = [
        destination,
        Path(str(destination) + ".sha256"),
        Path(str(destination) + ".members.sha256"),
        Path(str(destination) + ".verification.json"),
    ]
    if any(path.exists() for path in companions):
        raise FileExistsError("G2 synthesis audit delivery already exists; refusing overwrite")
    require_t1_baseline()
    verify_frozen_inputs(ROOT)
    later = later_gate_files(ROOT)
    if later:
        raise ValueError("G3/later-gate files present: " + ", ".join(later))
    failures = g2_run_failures(ROOT)
    if failures:
        raise ValueError("Live G2 evidence failure: " + "; ".join(failures))
    payload = collect()
    initial_hashes = {name: sha256_bytes(data) for name, data in payload.items()}
    pre = validate_tree(ROOT, "repository_before_sealing")
    for name, expected in FROZEN_INPUT_HASHES.items():
        if sha256_file(ROOT / name) != expected:
            raise ValueError(f"Frozen input changed during validation: {name}")
    run_dir = ROOT / "work/synthesis" / G2_RUN_ID
    candidates, decisions = load_g2_run(run_dir)
    counts = classification_counts(decisions)
    payload[verify_mod.VALIDATION] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "stage": "BEFORE_SEALING",
            "tests_passed": pre["tests_passed"],
            "live_evidence": "PASS",
            "classifications": counts,
            "candidate_count": len(candidates),
            "decision_count": len(decisions),
            "expected_items": EXPECTED_COUNT,
            "exact_ab_agreements": EXPECTED_AGREE,
            "exact_ab_disagreements": EXPECTED_DISAGREE,
            "candidate_sha256": sha256_file(run_dir / "candidates.jsonl"),
            "synthesis_decisions_sha256": sha256_file(run_dir / "synthesis_decisions.jsonl"),
            "frozen_input_hashes": FROZEN_INPUT_HASHES,
            "actual_model": ACTUAL_MODEL,
            "agent_a_model": AGENT_A_MODEL,
            "agent_b_model": AGENT_B_MODEL,
            "same_family_limitation": SAME_FAMILY_LIMITATION,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "g3_started": False,
            "title_authority_unresolved": True,
            "requirement_noncanonical_unresolved": True,
            "later_gate_files": later,
            "t1_baseline": T1_BASELINE,
            "t1_validator_files_unchanged": True,
            "g1_gate_zip_nested": False,
            "repository_validation": pre,
            "post_sealing_results": NAME + ".verification.json",
        }
    )
    payload[verify_mod.GIT_STATE] = git_state()
    names = sorted(set(payload) | {verify_mod.MANIFEST, verify_mod.INDEX})
    payload[verify_mod.MANIFEST] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "g2_run_id": G2_RUN_ID,
            "g2_status": "SYNTHESIS_CANDIDATE_COMPLETE",
            "g3_started": False,
            "actual_model": ACTUAL_MODEL,
            "agent_a_model": AGENT_A_MODEL,
            "agent_b_model": AGENT_B_MODEL,
            "same_family_limitation": SAME_FAMILY_LIMITATION,
            "expected_items": EXPECTED_COUNT,
            "translated_items": EXPECTED_COUNT,
            "canonical_count": 53,
            "source_requirement_count": 1,
            "exact_ab_agreements": EXPECTED_AGREE,
            "exact_ab_disagreements": EXPECTED_DISAGREE,
            "classifications": counts,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "nested_g1_gate_zip": False,
            "g1_gate_zip_sha256": FROZEN_INPUT_HASHES[
                "deliverables/audit/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip"
            ],
            "candidate_sha256": sha256_file(run_dir / "candidates.jsonl"),
            "synthesis_decisions_sha256": sha256_file(run_dir / "synthesis_decisions.jsonl"),
            "members": names,
            "payload_sha256": {
                name: sha256_bytes(data) for name, data in sorted(payload.items())
            },
            "hash_coverage_note": (
                "Internal TSV additionally hashes this manifest. Detached "
                ".members.sha256 hashes every member including both index files; "
                "no recursive/self hash is claimed."
            ),
            "native_source_containers": (
                "Official .docx members are original source documents in native "
                "OOXML format. The G1 gate ZIP is hashed and recorded via sidecar, "
                "not nested."
            ),
        }
    )
    payload[verify_mod.INDEX] = (
        "path\tsha256\tbytes\n"
        + "".join(
            f"{name}\t{sha256_bytes(data)}\t{len(data)}\n"
            for name, data in sorted(payload.items())
        )
    ).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100444 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    digest = sha256_bytes(destination.read_bytes())
    companions[1].write_text(f"{digest}  {NAME}\n", encoding="utf-8")
    companions[2].write_text(
        "".join(
            f"{sha256_bytes(data)}  {name}\n" for name, data in sorted(payload.items())
        ),
        encoding="utf-8",
    )
    independent = run_verifier(destination)
    print(json.dumps(independent, ensure_ascii=False), flush=True)
    post = validate_tree(ROOT, "repository_after_final_zip_sealed")
    require_t1_baseline()
    for name, expected in initial_hashes.items():
        if sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Packaged repository input changed: {name}")
    for name, expected in FROZEN_INPUT_HASHES.items():
        if sha256_file(ROOT / name) != expected:
            raise ValueError(f"Frozen input hash drifted: {name}")
    if sha256_bytes(destination.read_bytes()) != digest:
        raise ValueError("Sealed ZIP changed")
    companions[3].write_bytes(
        encode(
            {
                "archive_verification": independent,
                "post_packaging_repository_validation": post,
                "original_payload_unchanged": True,
                "agent_a_unchanged": True,
                "agent_b_unchanged": True,
                "g1_gate_unchanged": True,
                "t1_evidence_unchanged": True,
                "official_sources_unchanged": True,
                "human_approval_present": False,
                "clinical_validation_claimed": False,
                "g3_started": False,
                "actual_model": ACTUAL_MODEL,
                "secret_screening": (
                    "PASS: explicit allowlisted content, known credential-pattern "
                    "scan; no caches or credential stores included"
                ),
                "git_state_after_packaging": git_state().decode("utf-8"),
            }
        )
    )
    print("COMPLETE", destination, digest, flush=True)


if __name__ == "__main__":
    main()
