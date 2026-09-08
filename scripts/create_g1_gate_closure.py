"""Seal the G1 gate-closure audit package. Translation candidates are never rewritten."""

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

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g1_gate_closure.py"
SPEC = importlib.util.spec_from_file_location("verify_g1_gate_closure", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g1_gate_closure.py")
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
    "docs/OFFICIAL_TRANSLATION_GUIDANCE.md",
    "docs/SOURCE_PROVENANCE.md",
    "data/source_units.jsonl",
    "data/source_units.tsv",
    "data/source_requirements.jsonl",
    "data/canonical_unit_manifest.json",
    "data/canonical_unit_exceptions.jsonl",
    "data/governance_integrity_manifest.json",
    "data/README.md",
    "sources/official/README.md",
    "sources/reference/README.md",
    "sources/manifests/source_manifest.json",
    "config/model_roles.yaml",
    "config/project.yaml",
    "config/quality_gates.yaml",
    "terminology/terms.csv",
    "src/spict4all/g1_t1_isolation.py",
    "src/spict4all/adjudication.py",
    "src/spict4all/terminology_closure.py",
    "src/spict4all/hashing.py",
    "tests/conftest.py",
    "tests/test_g1_t1_isolation.py",
    "tests/test_adjudication.py",
    "work/agent-a/candidates.jsonl",
    "work/agent-a/run_metadata.json",
    "work/agent-b/candidates.jsonl",
    "work/agent-b/runs/G1-B-20260908-002/candidates.jsonl",
    "work/agent-b/runs/G1-B-20260908-002/run_metadata.json",
    "scripts/create_g1_gate_closure.py",
    "scripts/verify_g1_gate_closure.py",
    "scripts/verify_g1_a_audit.py",
    "scripts/verify_g1_b_audit_package.py",
    "scripts/verify_g1_b_r2_audit_package.py",
    *verify_mod.UPSTREAM_SIDECARS,
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
    match = re.search(r"(\d+) passed", records[0]["stdout"])
    if not match:
        raise ValueError("No test pass count")
    return {
        "scope": label,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "tests_passed": int(match.group(1)),
        "all_commands_passed": True,
        "commands": records,
    }


def run_verifier(script: str, archive: Path) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), str(archive)],
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
        + "\nNo push performed. Finnish translation candidates were not rewritten. G2 was not started.\n"
    ).encode()


def summary(tests: int, upstream: dict[str, Any]) -> bytes:
    agent_a = upstream[verify_mod.G1_A_ZIP]
    agent_b = upstream[verify_mod.G1_B_R2_ZIP]
    return f"""# SPICT-4ALL FI — G1 gate closure

Work package: **{verify_mod.WORK_PACKAGE}**
Packaged: 2026-09-08
Status: **G1 independent forward translations complete. G2 not started.**

This package closes G1 after both independent forward translations and the
main-branch G1/T1 isolation integration fix. It is not a translation task and
does not start synthesis, back-translation, or critic review.

## Independent runs

| Role | Authoritative artifact | Actual model | Configured / planned role model |
| --- | --- | --- | --- |
| Forward Translator A | `work/agent-a/candidates.jsonl` | **GPT-6** | GPT-5.6 Sol Medium |
| Forward Translator B R2 | `work/agent-b/runs/G1-B-20260908-002/candidates.jsonl` | **Cursor Grok 4.6** | Claude Fable 5.1 High |

The planned/configured identities in `config/model_roles.yaml` differ from the
actual models used. That discrepancy is preserved. Exact GPT-6 backend variant
and effort were not exposed in the Agent A run record.

Original Agent B run `work/agent-b/candidates.jsonl` remains byte-for-byte
preserved as G1-B-20260908-001. R2 is the authoritative B wording for G1 close.

## Coverage

- Agent A: **54/54** (53 canonical + 1 source requirement). IDs unique. No blank Finnish.
- Agent B R2: **54/54** (53 canonical + 1 source requirement). IDs unique. No blank Finnish.
- A and B share the identical frozen source universe, exact English, and source SHA-256 per ID.
- Schema states remain non-approval: Agent A `DRAFT`, Agent B R2 `READY_FOR_SYNTHESIS`.
- No `HUMAN_APPROVED` status is inferred. No clinical validation is claimed.

## Unresolved authority preserved

- `S4A-2026-000` remains unresolved and non-insertable.
- `S4A-REQ-2026-001` remains noncanonical, unresolved, and publication-blocking.

## Upstream audit ZIPs

The A and B-R2 audit ZIPs are **not nested** in this archive. They were hashed
and independently verified in place. Sidecars are included.

- `{verify_mod.G1_A_ZIP}`: {agent_a["sha256"]} ({agent_a["bytes"]} bytes) — {agent_a["verification_status"]}
- `{verify_mod.G1_B_R2_ZIP}`: {agent_b["sha256"]} ({agent_b["bytes"]} bytes) — {agent_b["verification_status"]}

## Frozen candidate hashes

- `work/agent-a/candidates.jsonl`: `{verify_mod.EXPECTED_CANDIDATE_HASHES[verify_mod.AGENT_A_CANDIDATES]}`
- `work/agent-b/candidates.jsonl`: `{verify_mod.EXPECTED_CANDIDATE_HASHES[verify_mod.AGENT_B_ORIGINAL_CANDIDATES]}`
- `work/agent-b/runs/G1-B-20260908-002/candidates.jsonl`: `{verify_mod.EXPECTED_CANDIDATE_HASHES[verify_mod.AGENT_B_R2_CANDIDATES]}`

## Integration isolation

Historical T1 tests continue to validate a pre-G1 view. G1 tests validate the
current G1 view. `src/spict4all/g1_t1_isolation.py`, `tests/conftest.py`, and
`tests/test_g1_t1_isolation.py` hide both `work/agent-a/**` and `work/agent-b/**`
except `.gitkeep` while T1 inventory is evaluated. Historical T1 validator files
`src/spict4all/adjudication.py`, `src/spict4all/terminology_closure.py`, and
`tests/test_adjudication.py` match baseline `{T1_BASELINE}`.

## Validation

The live repository passed **{tests} tests** plus official-source, requirement,
canonical, governance, terminology, compileall, strict mypy, and ruff checks
before sealing. Full command outputs are in `G1_GATE_VALIDATION_RESULTS.json`.
Those checks are mechanical integrity results, not clinical validation.

Verify with `python scripts/verify_g1_gate_closure.py /path/to/{NAME}` while
keeping the companion hash files alongside the ZIP.

No Finnish candidate was changed while creating this closure. G2 was not started.
""".encode()


def write_closure(name: str, data: bytes) -> None:
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Closure source already exists: {name}")
    path.write_bytes(data)


def main() -> None:
    destination = ROOT / "deliverables/audit" / NAME
    companions = [
        destination,
        Path(str(destination) + ".sha256"),
        Path(str(destination) + ".members.sha256"),
        Path(str(destination) + ".verification.json"),
    ]
    if any(path.exists() for path in companions):
        raise FileExistsError("G1 gate-closure delivery already exists; refusing overwrite")
    require_t1_baseline()
    later = verify_mod.later_gate_files(ROOT)
    if later:
        raise ValueError("G2/later-gate files present: " + ", ".join(later))
    live = verify_mod.live_evidence_payload(ROOT)
    evidence = verify_mod.evidence_failures(live)
    if evidence:
        raise ValueError("Live G1 evidence failure: " + "; ".join(evidence))
    upstream = verify_mod.verify_upstream_zip_files(ROOT)
    upstream_a = run_verifier(
        "verify_g1_a_audit.py",
        ROOT / "deliverables/audit" / verify_mod.G1_A_ZIP,
    )
    upstream_b = run_verifier(
        "verify_g1_b_r2_audit_package.py",
        ROOT / "deliverables/audit" / verify_mod.G1_B_R2_ZIP,
    )
    payload = collect()
    initial_hashes = {name: sha256_bytes(data) for name, data in payload.items()}
    pre = validate_tree(ROOT, "repository_before_sealing")
    if pre["tests_passed"] != 341:
        raise ValueError(f"Expected 341 tests, got {pre['tests_passed']}")
    for name, expected in verify_mod.EXPECTED_CANDIDATE_HASHES.items():
        if sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Candidate changed during validation: {name}")
    payload[verify_mod.REPORT] = summary(pre["tests_passed"], upstream)
    payload[verify_mod.VALIDATION] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "stage": "BEFORE_SEALING",
            "tests_passed": pre["tests_passed"],
            "live_evidence": "PASS",
            "source_universe_equality": "PASS",
            "candidate_hashes": verify_mod.EXPECTED_CANDIDATE_HASHES,
            "upstream_zip_hashes": upstream,
            "upstream_g1_a_verification": upstream_a,
            "upstream_g1_b_r2_verification": upstream_b,
            "later_gate_files": later,
            "t1_baseline": T1_BASELINE,
            "t1_validator_files_unchanged": True,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "g2_started": False,
            "repository_validation": pre,
            "post_sealing_results": NAME + ".verification.json",
        }
    )
    payload[verify_mod.GIT_STATE] = git_state()
    for generated in (verify_mod.REPORT, verify_mod.VALIDATION, verify_mod.GIT_STATE):
        write_closure(generated, payload[generated])
    names = sorted(set(payload) | {verify_mod.MANIFEST, verify_mod.INDEX})
    payload[verify_mod.MANIFEST] = encode(
        {
            "work_package": verify_mod.WORK_PACKAGE,
            "g1_status": "INDEPENDENT_FORWARD_TRANSLATIONS_COMPLETE",
            "g2_started": False,
            "agent_a_model": verify_mod.AGENT_A_MODEL,
            "agent_b_model": verify_mod.AGENT_B_MODEL,
            "expected_items": 54,
            "agent_a_translated_items": 54,
            "agent_b_r2_translated_items": 54,
            "canonical_count": 53,
            "source_requirement_count": 1,
            "source_universe_equal": True,
            "human_approval_present": False,
            "clinical_validation_claimed": False,
            "nested_upstream_zips": False,
            "upstream_zip_hashes": {
                name: record["sha256"] for name, record in upstream.items()
            },
            "candidate_sha256": verify_mod.EXPECTED_CANDIDATE_HASHES,
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
                "OOXML format. Upstream G1-A and G1-B-R2 audit ZIPs are hashed "
                "and recorded, not nested."
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
    write_closure(verify_mod.MANIFEST, payload[verify_mod.MANIFEST])
    write_closure(verify_mod.INDEX, payload[verify_mod.INDEX])
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
    independent = run_verifier("verify_g1_gate_closure.py", destination)
    print(json.dumps(independent, ensure_ascii=False), flush=True)
    post = validate_tree(ROOT, "repository_after_final_zip_sealed")
    if post["tests_passed"] != 341:
        raise ValueError(f"Expected 341 tests after sealing, got {post['tests_passed']}")
    require_t1_baseline()
    for name, expected in initial_hashes.items():
        if name in verify_mod.EXPECTED_CANDIDATE_HASHES:
            if sha256_bytes((ROOT / name).read_bytes()) != expected:
                raise ValueError(f"Translation candidate changed: {name}")
        elif sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Packaged repository input changed: {name}")
    for name, expected in verify_mod.EXPECTED_CANDIDATE_HASHES.items():
        if sha256_bytes((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Candidate hash drifted: {name}")
    if sha256_bytes(destination.read_bytes()) != digest:
        raise ValueError("Sealed ZIP changed")
    companions[3].write_bytes(
        encode(
            {
                "archive_verification": independent,
                "post_packaging_repository_validation": post,
                "original_payload_unchanged": True,
                "translation_candidates_unchanged": True,
                "g2_started": False,
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
