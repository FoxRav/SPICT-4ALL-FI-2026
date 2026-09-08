"""Seal the G3 blind back-translation audit package. G3 JSONL is never rewritten."""

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

from spict4all.g3_backtranslation import (
    ACTUAL_MODEL,
    BACK_TRANSLATION_RELATIVE,
    BLIND_INPUT_RELATIVE,
    BLINDING_CLAIM,
    ENVIRONMENT,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_RUN_ID,
    REASONING_EFFORT,
    finnish_only_extract,
    g3_run_failures,
    load_jsonl_records,
    verify_frozen_g3_bytes,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g3_backtranslation_audit.py"
SPEC = importlib.util.spec_from_file_location("verify_g3_backtranslation_audit", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g3_backtranslation_audit.py")
verify_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mod)

NAME = verify_mod.NAME
FIXED_TIME = (2026, 9, 8, 0, 0, 0)
NAMED_FILES = (
    "AGENTS.md",
    "config/model_roles.yaml",
    "src/spict4all/g3_backtranslation.py",
    "src/spict4all/g1_t1_isolation.py",
    "scripts/write_g3_backtranslation_metadata.py",
    "scripts/validate_g3_backtranslation.py",
    "scripts/create_g3_backtranslation_audit.py",
    "scripts/verify_g3_backtranslation_audit.py",
    "tests/test_g3_backtranslation.py",
    BLIND_INPUT_RELATIVE,
    BACK_TRANSLATION_RELATIVE,
    f"{verify_mod.RUN_PREFIX}/run_metadata.json",
    f"{verify_mod.RUN_PREFIX}/G3_BACKTRANSLATION_REPORT.md",
    f"{verify_mod.RUN_PREFIX}/validation_results.json",
    "work/backtranslation/.gitkeep",
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
        if path.suffix in {".py", ".json", ".jsonl", ".md", ".txt", ".yaml"}:
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, data):
                    raise ValueError(f"Potential credential material in {name}")
        payload[name] = data
    g2 = load_jsonl_records((ROOT / G2_CANDIDATES_RELATIVE).read_text(encoding="utf-8"))
    extract_lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in finnish_only_extract(g2)
    ]
    payload[verify_mod.FI_EXTRACT] = "".join(extract_lines).encode("utf-8")
    return payload


def commands() -> list[list[str]]:
    result = [
        ["scripts/validate_g3_backtranslation.py"],
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
        + "\nNo commit performed. No push performed. G4 was not started.\n"
        "G3 JSONL was not rewritten. No semantic comparison with original English was performed.\n"
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
        raise FileExistsError("G3 audit delivery already exists; refusing overwrite")
    verify_frozen_g3_bytes(
        {relative: (ROOT / relative).read_bytes() for relative in EXPECTED_HASHES}
    )
    failures = g3_run_failures(ROOT)
    if failures:
        raise ValueError("Live G3 evidence failure: " + "; ".join(failures))
    payload = collect()
    initial_hashes = {name: sha256_bytes(data) for name, data in payload.items()}
    pre = validate_tree(ROOT, "repository_before_sealing")
    for relative, expected in EXPECTED_HASHES.items():
        if sha256_file(ROOT / relative) != expected:
            raise ValueError(f"Frozen artifact changed during validation: {relative}")
    payload[verify_mod.VALIDATION] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "stage": "BEFORE_SEALING",
            "tests_passed": pre["tests_passed"],
            "live_evidence": "PASS",
            "blind_input_count": EXPECTED_COUNT,
            "back_translation_count": EXPECTED_COUNT,
            "id_order_match": True,
            "g2_candidate_fi_derivation": "PASS",
            "frozen_hashes": EXPECTED_HASHES,
            "actual_model": ACTUAL_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "environment": ENVIRONMENT,
            "blinding_claim": BLINDING_CLAIM,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "semantic_comparison_with_source_performed": False,
            "g4_started": False,
            "jsonl_rewritten": False,
            "g2_candidates_packaged": False,
            "repository_validation": pre,
            "post_sealing_results": NAME + ".verification.json",
        }
    )
    payload[verify_mod.GIT_STATE] = git_state()
    names = sorted(set(payload) | {verify_mod.MANIFEST, verify_mod.INDEX})
    payload[verify_mod.MANIFEST] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "g3_run_id": G3_RUN_ID,
            "g3_status": "BLIND_BACKTRANSLATION_COMPLETE",
            "g4_started": False,
            "actual_model": ACTUAL_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "environment": ENVIRONMENT,
            "expected_items": EXPECTED_COUNT,
            "translated_items": EXPECTED_COUNT,
            "id_order_match": True,
            "g2_candidate_fi_derivation": "PASS",
            "g2_candidates_sha256": EXPECTED_HASHES[G2_CANDIDATES_RELATIVE],
            "blind_input_sha256": EXPECTED_HASHES[BLIND_INPUT_RELATIVE],
            "back_translation_sha256": EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE],
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "semantic_comparison_with_source_performed": False,
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
            "blinding_note": (
                "Full G2 candidates, A/B translations, original English source "
                "units, and G1/G2 audit ZIPs are not nested or packaged. "
                "G3_G2_CANDIDATE_FI_ONLY.jsonl is a Finnish-only extract used by "
                "audit tooling to prove blind-input derivation."
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
    for name, expected in initial_hashes.items():
        if name == verify_mod.FI_EXTRACT:
            continue
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
                "g3_jsonl_unchanged": True,
                "g2_finnish_candidates_unchanged": True,
                "human_approval_present": False,
                "clinical_validation_claimed": False,
                "semantic_comparison_with_source_performed": False,
                "g4_started": False,
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
