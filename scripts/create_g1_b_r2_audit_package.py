"""Seal an additive G1-B R2 correction audit package. Original 001 is never rewritten."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NAME = "SPICT4ALL-FI-G1-B-R2-forward-translation-audit-20260908.zip"
FIXED_TIME = (2026, 9, 8, 0, 0, 0)
CORRECTED_RUN = "G1-B-20260908-002"
TRANSLATION_HASHES = {
    "work/agent-b/agent_b_translations.json": (
        "1d10eb85a0fbad412148e90c2f890a05c473bcf4165b1b3bca99dfbd185a775e"
    ),
    "work/agent-b/candidates.jsonl": (
        "0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640"
    ),
}
NAMED_FILES = (
    "AGENTS.md",
    "pyproject.toml",
    "requirements-dev.lock",
    "prompts/02-agent-b-forward.md",
    "docs/METHODOLOGY.md",
    "docs/WORKFLOW.md",
    "docs/MODEL_STRATEGY.md",
    "docs/PROJECT_CHARTER.md",
    "docs/OFFICIAL_TRANSLATION_GUIDANCE.md",
    "docs/SOURCE_PROVENANCE.md",
    "data/README.md",
    "data/source_units.jsonl",
    "data/source_units.tsv",
    "data/source_requirements.jsonl",
    "data/canonical_unit_manifest.json",
    "data/canonical_unit_exceptions.jsonl",
    "data/governance_integrity_manifest.json",
    "sources/official/README.md",
    "sources/reference/README.md",
    "work/agent-b/agent_b_translations.json",
    "work/agent-b/candidates.jsonl",
    f"work/agent-b/runs/{CORRECTED_RUN}/agent_b_translations.json",
    f"work/agent-b/runs/{CORRECTED_RUN}/candidates.jsonl",
    f"work/agent-b/runs/{CORRECTED_RUN}/run_metadata.json",
    f"work/agent-b/runs/{CORRECTED_RUN}/CORRECTION_REPORT.md",
    f"work/agent-b/runs/{CORRECTED_RUN}/correction_diff.json",
    f"work/agent-b/runs/{CORRECTED_RUN}/validation_results.json",
    "scripts/build_g1_b_candidates.py",
    "scripts/build_g1_b_correction_run.py",
    "scripts/validate_g1_b_candidates.py",
    "scripts/verify_g1_b_audit_package.py",
    "scripts/create_g1_b_audit_package.py",
    "scripts/verify_g1_b_r2_audit_package.py",
    "scripts/create_g1_b_r2_audit_package.py",
)
SCRIPT_GLOBS = (
    "*g1_b*",
    "*t1*",
    "verify_sources.py",
    "check_translation_coverage.py",
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


def require_unchanged_originals() -> None:
    for relative, expected in TRANSLATION_HASHES.items():
        actual = sha256_bytes((ROOT / relative).read_bytes())
        if actual != expected:
            raise ValueError(
                f"G1-B-20260908-001 translation evidence changed; refusing to package: {relative}"
            )


def collect() -> dict[str, bytes]:
    selected: set[Path] = set()
    for directory in ("terminology", "data/Sanasto", "config", "schemas"):
        selected.update(path for path in (ROOT / directory).rglob("*") if path.is_file())
    selected.update((ROOT / "src/spict4all").glob("*.py"))
    selected.update((ROOT / "tests").glob("*.py"))
    selected.update((ROOT / "data").glob("*.json*"))
    selected.update((ROOT / "data").glob("*.tsv"))
    selected.update((ROOT / "sources/manifests").glob("*.json"))
    selected.update((ROOT / "work").rglob(".gitkeep"))
    selected.update((ROOT / "work/agent-b/runs" / CORRECTED_RUN).rglob("*"))
    for record in json.loads(
        (ROOT / "sources/manifests/source_manifest.json").read_text(encoding="utf-8")
    ):
        selected.add(ROOT / "sources/official" / record["filename"])
    for relative in NAMED_FILES:
        selected.add(ROOT / relative)
    for pattern in SCRIPT_GLOBS:
        selected.update((ROOT / "scripts").glob(pattern))
    for lock in (ROOT / "terminology/adjudication").rglob("*input_integrity.json"):
        protected = json.loads(lock.read_text(encoding="utf-8"))["protected_files"]
        for name in protected:
            path = ROOT / name
            if path.exists():
                selected.add(path)
    payload: dict[str, bytes] = {}
    for path in sorted(selected):
        if not path.is_file():
            continue
        name = path.relative_to(ROOT).as_posix()
        if any(
            part in {".git", ".firecrawl", "__pycache__", "node_modules", ".venv"}
            for part in name.split("/")
        ):
            raise ValueError(f"Unexpected cache path: {name}")
        if name.lower().endswith((".zip", ".tmp", ".pyc")):
            raise ValueError(f"Excluded artifact selected: {name}")
        if name.startswith("deliverables/"):
            raise ValueError(f"Existing delivery selected: {name}")
        if name.startswith("work/agent-a/") and not name.endswith(".gitkeep"):
            raise ValueError(f"Agent A artifact selected: {name}")
        data = path.read_bytes()
        if path.suffix in {".py", ".json", ".jsonl", ".md", ".txt", ".yaml", ".tsv", ".csv"}:
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, data):
                    raise ValueError(f"Potential credential material in {name}")
        payload[name] = data
    for relative, expected in TRANSLATION_HASHES.items():
        if sha256_bytes(payload[relative]) != expected:
            raise ValueError(f"Collected original translation bytes differ: {relative}")
    return payload


def commands() -> list[list[str]]:
    result = [["-m", "pytest", "-p", "no:cacheprovider"]]
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
        ["scripts/validate_g1_b_candidates.py"],
    ]
    return result


def validate_tree(tree: Path, label: str) -> dict[str, Any]:
    environment = dict(
        os.environ,
        PYTHONPATH=str(tree / "src"),
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
    )
    check = subprocess.run(
        [sys.executable, "-c", "import spict4all; print(spict4all.__file__)"],
        cwd=tree,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if str(tree / "src").lower() not in check.stdout.strip().lower():
        raise ValueError("Validation imported code outside the audited tree")
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
    match = re.search(r"(\d+) passed", records[0]["stdout"])
    if not match:
        raise ValueError("No test pass count")
    return {
        "scope": label,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "tests_passed": int(match.group(1)),
        "all_commands_passed": True,
        "imported_package": check.stdout.strip(),
        "commands": records,
    }


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
        + "\nNo commit or push performed. Original G1-B-20260908-001 evidence was not rewritten.\n"
    ).encode()


def summary(tests: int) -> bytes:
    return f"""# SPICT-4ALL FI — G1-B R2 forward-translation correction audit

Work package: **WP-G1-B-CORRECTION-R2-001**
Packaged: 2026-09-08
Original run: **G1-B-20260908-001** (byte-for-byte unchanged)
Corrected run: **G1-B-20260908-002**
Role: **Forward Translator B**

## Model provenance

- **Actual model used: Cursor Grok 4.6**
- Configured / planned role model in `config/model_roles.yaml`: Claude Fable 5.1 High
- These two identities differ. The discrepancy is preserved and is not rewritten.

## Correction

Independent audit found that the original B run did not apply three explicit
Project Owner wording decisions from `terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md`.
Those decisions pre-date G1 and are authorized input. They are not Agent A evidence.

Exactly five `candidate_fi` fields were changed:

- S4A-2026-001, S4A-2026-042: `terveydentila on heikentynyt`
- S4A-2026-004, S4A-2026-014: `toimintakyky on heikentynyt` (usual/tavanomaiset activities kept)
- S4A-2026-017: `ei ole riittävän hyväkuntoinen syöpähoitoon`

No terminology decision IDs were invented. T-002, T-013 and T-016 remain applied.
No other Finnish candidate was changed. This is not synthesis.

## Coverage

- Expected translation-evidence items: **54**
- Canonical source units: **53** + source requirement **1**
- Original 001 hashes unchanged
- Schema `status`: `READY_FOR_SYNTHESIS` (not human approval)
- No `HUMAN_APPROVED` state

## Independence

- Agent A was not inspected.
- No Agent A translation files are packaged.
- No synthesis was performed.
- No G2 was performed.

## T1 validators

Historical T1 files `src/spict4all/adjudication.py`, `src/spict4all/terminology_closure.py`
and `tests/test_adjudication.py` match baseline commit `2aa066f`. T1 was not weakened
to accommodate G1 evidence. Pytest T1 inventory checks use an isolated G1 hide/restore
fixture. The T1.3 CLI correctly rejects a live work tree that already contains G1 files;
that CLI is therefore not run against a tree that includes G1 evidence.

## Validation

The isolated payload snapshot passed **{tests} tests** plus source, requirement, canonical,
governance, terminology, compileall, strict mypy, ruff, and G1-B candidate validators.

Verify with `python scripts/verify_g1_b_r2_audit_package.py /path/to/{NAME}` while keeping
the companion hash files alongside the ZIP.

No commit or push was performed.
""".encode()


def main() -> None:
    destination = ROOT / "deliverables/audit" / NAME
    companions = [
        destination,
        Path(str(destination) + ".sha256"),
        Path(str(destination) + ".members.sha256"),
        Path(str(destination) + ".verification.json"),
    ]
    if any(path.exists() for path in companions):
        raise FileExistsError("R2 audit delivery already exists; refusing overwrite")
    require_unchanged_originals()
    payload = collect()
    initial_hashes = {name: sha256_bytes(data) for name, data in payload.items()}
    with tempfile.TemporaryDirectory(prefix="spict-g1b-r2-audit-") as scratch:
        stage = Path(scratch)
        for name, data in payload.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        pre = validate_tree(stage, "isolated_payload_before_sealing")
    require_unchanged_originals()
    for name, digest in initial_hashes.items():
        if sha256_bytes((ROOT / name).read_bytes()) != digest:
            raise ValueError(f"Input changed during validation: {name}")
    payload["G1_B_R2_AUDIT_SUMMARY.md"] = summary(pre["tests_passed"])
    payload["G1_B_R2_AUDIT_VALIDATION_RESULTS.json"] = encode(pre)
    payload["G1_B_R2_GIT_STATE.txt"] = git_state()
    names = sorted(
        set(payload)
        | {
            "G1_B_R2_AUDIT_MANIFEST.json",
            "G1_B_R2_AUDIT_FILE_HASHES.tsv",
        }
    )
    payload["G1_B_R2_AUDIT_MANIFEST.json"] = encode(
        {
            "work_package": "WP-G1-B-CORRECTION-R2-001",
            "original_run_id": "G1-B-20260908-001",
            "corrected_run_id": CORRECTED_RUN,
            "translator_role": "forward_translation_B",
            "actual_model": "Cursor Grok 4.6",
            "configured_role_model": "Claude Fable 5.1 High",
            "model_discrepancy_preserved": True,
            "expected_items": 54,
            "translated_items": 54,
            "canonical_count": 53,
            "source_requirement_count": 1,
            "changed_unit_ids": [
                "S4A-2026-001",
                "S4A-2026-004",
                "S4A-2026-014",
                "S4A-2026-017",
                "S4A-2026-042",
            ],
            "approved_glossary_rows": 0,
            "recorded_schema_status": "READY_FOR_SYNTHESIS",
            "human_approval_present": False,
            "agent_a_inspected": False,
            "synthesis_performed": False,
            "g2_performed": False,
            "original_translation_evidence_rewritten": False,
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
                "OOXML format, not nested audit archives."
            ),
        }
    )
    payload["G1_B_R2_AUDIT_FILE_HASHES.tsv"] = (
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
    verifier = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_g1_b_r2_audit_package.py"), str(destination)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if verifier.returncode:
        raise ValueError(verifier.stderr or verifier.stdout)
    independent = json.loads(verifier.stdout)
    print(json.dumps(independent, ensure_ascii=False), flush=True)
    with tempfile.TemporaryDirectory(prefix="spict-g1b-r2-sealed-") as scratch:
        extracted = Path(scratch)
        with zipfile.ZipFile(destination) as archive:
            archive.extractall(extracted)
        environment = dict(
            os.environ,
            PYTHONPATH=str(extracted / "src"),
            PYTHONIOENCODING="utf-8",
        )
        check = subprocess.run(
            [sys.executable, "scripts/validate_g1_b_candidates.py"],
            cwd=extracted,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if check.returncode:
            raise ValueError(check.stderr or check.stdout)
    post = validate_tree(ROOT, "repository_after_final_zip_sealed")
    require_unchanged_originals()
    for name, expected in initial_hashes.items():
        if sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Packaged repository input changed: {name}")
    if sha256_bytes(destination.read_bytes()) != digest:
        raise ValueError("Sealed ZIP changed")
    companions[3].write_bytes(
        encode(
            {
                "archive_verification": independent,
                "sealed_extracted_g1_b_validation": {
                    "exit_code": check.returncode,
                    "stdout": check.stdout,
                    "stderr": check.stderr,
                },
                "post_packaging_repository_validation": post,
                "original_payload_unchanged": True,
                "original_translation_evidence_unchanged": True,
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
