"""Seal the G4 independent-critics audit package. Frozen JSONL is never rewritten."""

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

from spict4all.g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_ACTUAL_MODEL,
    CRITIC_A_RELATIVE,
    CRITIC_B_ACTUAL_MODEL,
    CRITIC_B_RELATIVE,
    EXPECTED_B_ONLY,
    EXPECTED_CORROBORATED,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    G4_RUN_ID,
    G4_STATUS,
    INDEPENDENCE_STATEMENT,
    REVIEW_INPUT_RELATIVE,
    SAME_FAMILY_LIMITATION,
    WORK_PACKAGE,
    g4_run_failures,
    verify_frozen_g4_bytes,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g4_critics_audit.py"
SPEC = importlib.util.spec_from_file_location("verify_g4_critics_audit", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g4_critics_audit.py")
verify_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mod)

NAME = verify_mod.NAME
FIXED_TIME = (2026, 9, 8, 0, 0, 0)
NAMED_FILES = (
    "AGENTS.md",
    "README.md",
    "config/model_roles.yaml",
    "config/quality_gates.yaml",
    "data/source_requirements.jsonl",
    "data/canonical_unit_exceptions.jsonl",
    "terminology/adjudication/human_terminology_decisions.tsv",
    "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
    "src/spict4all/g4_critics.py",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/forward_candidates.py",
    "src/spict4all/review_reduction.py",
    "scripts/write_g4_critics_metadata.py",
    "scripts/validate_g4_critics.py",
    "scripts/create_g4_critics_audit.py",
    "scripts/verify_g4_critics_audit.py",
    "tests/test_g4_critics.py",
    REVIEW_INPUT_RELATIVE,
    CRITIC_A_RELATIVE,
    CRITIC_B_RELATIVE,
    COMBINED_RELATIVE,
    f"{verify_mod.RUN_PREFIX}/run_metadata.json",
    f"{verify_mod.RUN_PREFIX}/G4_REVIEW_REPORT.md",
    f"{verify_mod.RUN_PREFIX}/validation_results.json",
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    "work/critics/.gitkeep",
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


def collect() -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for relative in NAMED_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"Required input missing: {relative}")
        name = path.relative_to(ROOT).as_posix()
        if name.lower().endswith((".zip", ".tmp", ".pyc")):
            raise ValueError(f"Excluded artifact selected: {name}")
        data = path.read_bytes()
        if path.suffix in {".py", ".json", ".jsonl", ".md", ".txt", ".yaml", ".tsv"}:
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, data):
                    raise ValueError(f"Potential credential material in {name}")
        payload[name] = data
    return payload


def commands() -> list[list[str]]:
    result = [
        ["scripts/validate_g4_critics.py"],
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
        + "\nNo commit performed. No push performed. G5 was not created.\n"
        "No Finnish candidate was changed. No G3 output was changed. "
        "No critic output was changed. No human adjudication.\n"
        f"{INDEPENDENCE_STATEMENT}\n"
        f"{SAME_FAMILY_LIMITATION}\n"
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
        raise FileExistsError("G4 audit delivery already exists; refusing overwrite")
    verify_frozen_g4_bytes(
        {relative: (ROOT / relative).read_bytes() for relative in EXPECTED_HASHES}
    )
    failures = g4_run_failures(ROOT)
    if failures:
        raise ValueError("Live G4 evidence failure: " + "; ".join(failures))
    payload = collect()
    initial_hashes = {name: sha256_bytes(data) for name, data in payload.items()}
    pre = validate_tree(ROOT, "repository_before_sealing")
    for relative, expected in EXPECTED_HASHES.items():
        if sha256_file(ROOT / relative) != expected:
            raise ValueError(f"Frozen artifact changed during validation: {relative}")
    payload[verify_mod.VALIDATION] = encode(
        {
            "work_package": WORK_PACKAGE,
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "stage": "BEFORE_SEALING",
            "tests_passed": pre["tests_passed"],
            "live_evidence": "PASS",
            "review_input_count": EXPECTED_COUNT,
            "critic_a_count": EXPECTED_COUNT,
            "critic_b_count": EXPECTED_COUNT,
            "combined_count": EXPECTED_COUNT,
            "id_order_match": True,
            "corroborated": list(EXPECTED_CORROBORATED),
            "critic_a_only": [],
            "critic_b_only": list(EXPECTED_B_ONLY),
            "frozen_hashes": EXPECTED_HASHES,
            "critic_a_actual_model": CRITIC_A_ACTUAL_MODEL,
            "critic_b_actual_model": CRITIC_B_ACTUAL_MODEL,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "finnish_revised": False,
            "g5_created": False,
            "g4_pass_claimed": False,
            "repository_validation": pre,
            "post_sealing_results": NAME + ".verification.json",
        }
    )
    payload[verify_mod.GIT_STATE] = git_state()
    names = sorted(set(payload) | {verify_mod.MANIFEST, verify_mod.INDEX})
    payload[verify_mod.MANIFEST] = encode(
        {
            "work_package": WORK_PACKAGE,
            "g4_run_id": G4_RUN_ID,
            "g4_status": G4_STATUS,
            "g5_created": False,
            "critic_a_actual_model": CRITIC_A_ACTUAL_MODEL,
            "critic_b_actual_model": CRITIC_B_ACTUAL_MODEL,
            "expected_items": EXPECTED_COUNT,
            "combined_items": EXPECTED_COUNT,
            "corroborated": list(EXPECTED_CORROBORATED),
            "critic_a_only": [],
            "critic_b_only": list(EXPECTED_B_ONLY),
            "g2_candidates_sha256": EXPECTED_HASHES[G2_CANDIDATES_RELATIVE],
            "g3_back_translation_sha256": EXPECTED_HASHES[G3_BACK_RELATIVE],
            "critic_a_sha256": EXPECTED_HASHES[CRITIC_A_RELATIVE],
            "critic_b_sha256": EXPECTED_HASHES[CRITIC_B_RELATIVE],
            "review_input_sha256": EXPECTED_HASHES[REVIEW_INPUT_RELATIVE],
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "finnish_revised": False,
            "nested_archives": False,
            "members": names,
            "payload_sha256": {
                name: sha256_bytes(data) for name, data in sorted(payload.items())
            },
            "hash_coverage_note": (
                "Internal TSV additionally hashes this manifest. Detached "
                ".members.sha256 hashes every member including both index files; "
                "no recursive/self hash is claimed."
            ),
            "independence_note": INDEPENDENCE_STATEMENT,
            "same_family_limitation": SAME_FAMILY_LIMITATION,
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
    for name, expected in initial_hashes.items():
        if sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Packaged repository input changed: {name}")
    for relative, expected in EXPECTED_HASHES.items():
        if sha256_file(ROOT / relative) != expected:
            raise ValueError(f"Frozen artifact hash drifted: {relative}")
    if sha256_bytes(destination.read_bytes()) != digest:
        raise ValueError("Sealed ZIP changed")
    companions[3].write_bytes(
        encode(
            {
                "archive_verification": independent,
                "post_packaging_repository_validation": post,
                "original_payload_unchanged": True,
                "critic_outputs_unchanged": True,
                "g2_finnish_unchanged": True,
                "g3_back_translation_unchanged": True,
                "human_approval_present": False,
                "clinical_validation_claimed": False,
                "finnish_revised": False,
                "g5_created": False,
                "g4_pass_claimed": False,
                "critic_a_actual_model": CRITIC_A_ACTUAL_MODEL,
                "critic_b_actual_model": CRITIC_B_ACTUAL_MODEL,
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
