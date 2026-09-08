"""Seal an additive T1 audit package; existing deliverables are never overwritten."""
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

ROOT = Path(__file__).resolve().parents[1]
NAME = "SPICT4ALL-FI-T1-terminology-closure-audit-20260908.zip"
FIXED_TIME = (2026, 9, 8, 0, 0, 0)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def collect():
    selected = set()
    # Runtime, schemas and the complete test suite are dependencies for independent validation.
    for directory in ["terminology", "data/Sanasto", "config", "schemas"]:
        selected.update(p for p in (ROOT / directory).rglob("*") if p.is_file())
    for directory, pattern in [("src/spict4all", "*.py"), ("tests", "*.py"), ("data", "*.json*"), ("scripts", "*t1*.py"), ("scripts", "*t1*.mjs")]:
        selected.update((ROOT / directory).glob(pattern))
    selected.update((ROOT / "sources/manifests").glob("*.json"))
    selected.update((ROOT / "work").rglob(".gitkeep"))
    for record in json.loads((ROOT / "sources/manifests/source_manifest.json").read_text()):
        selected.add(ROOT / "sources/official" / record["filename"])
    for name in ["AGENTS.md", "pyproject.toml", "requirements-dev.lock", "tools.ps1", "data/source_units.tsv",
                 "docs/METHODOLOGY.md", "docs/WORKFLOW.md", "docs/MODEL_STRATEGY.md", "docs/PROJECT_CHARTER.md",
                 "docs/OFFICIAL_TRANSLATION_GUIDANCE.md", "docs/SOURCE_PROVENANCE.md", "scripts/build_terminology_evidence.py"]:
        selected.add(ROOT / name)
    # Include every existing protected validation dependency, respecting recorded path corrections.
    for lock in (ROOT / "terminology/adjudication").rglob("*input_integrity.json"):
        for name in json.loads(lock.read_text(encoding="utf-8"))["protected_files"]:
            path = ROOT / name
            if path.exists():
                selected.add(path)
    payload = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in sorted(selected) if p.is_file()}
    for name, data in payload.items():
        if any(x in name.split("/") for x in [".git", ".firecrawl", "__pycache__", "node_modules"]):
            raise ValueError(f"Unexpected cache path: {name}")
        if name.lower().endswith((".zip", ".tmp", ".pyc")) or name == "README.md":
            raise ValueError(f"Excluded artifact selected: {name}")
        if Path(name).suffix in {".py", ".json", ".jsonl", ".md", ".txt", ".yaml", ".tsv", ".mjs", ".csv"}:
            for pattern in [rb"sk-[A-Za-z0-9_-]{24,}", rb"gh[pousr]_[A-Za-z0-9]{30,}", rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"]:
                if re.search(pattern, data):
                    raise ValueError(f"Potential credential material in {name}; manual review required")
    return payload


def commands():
    result = [["-m", "pytest", "-p", "no:cacheprovider"]]
    result += [["-m", "spict4all.cli", "--root", ".", task] for task in
               ["verify-sources", "validate-requirements", "validate-canonical", "validate-governance", "validate-terminology"]]
    result += [["-m", "compileall", "-q", "src", "scripts", "tests"],
               ["-m", "mypy", "--strict", "src/spict4all"], ["-m", "ruff", "check", "src", "scripts", "tests"]]
    result += [[f"scripts/{name}"] for name in ["validate_t1_adjudication.py", "validate_t1_1_enrichment.py", "validate_t1_2_reduction.py", "validate_t1_3_closure.py"]]
    return result


def validate_tree(tree, label):
    environment = dict(os.environ, PYTHONPATH=str(tree / "src"), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    check = subprocess.run([sys.executable, "-c", "import spict4all; print(spict4all.__file__)"], cwd=tree, env=environment, capture_output=True, text=True)
    if str(tree / "src").lower() not in check.stdout.strip().lower():
        raise ValueError("Validation imported code outside the audited tree")
    records = []
    for arguments in commands():
        process = subprocess.run([sys.executable, *arguments], cwd=tree, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace")
        records.append({"command": ["python", *arguments], "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
        print(label, " ".join(arguments), process.returncode, flush=True)
        if process.returncode:
            print(process.stdout[-5000:], process.stderr[-2000:], flush=True)
            raise ValueError(f"{label} validation failed")
    match = re.search(r"(\d+) passed", records[0]["stdout"])
    if not match:
        raise ValueError("No test pass count")
    return {"scope": label, "completed_at_utc": datetime.now(UTC).isoformat(), "tests_passed": int(match.group(1)),
            "all_commands_passed": True, "imported_package": check.stdout.strip(), "commands": records}


def git_state():
    blocks = []
    for arguments in [["rev-parse", "HEAD"], ["branch", "--show-current"], ["status", "--short", "--untracked-files=all"]]:
        result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            raise ValueError("Git state capture failed")
        blocks += ["git " + " ".join(arguments), result.stdout]
    return ("\n".join(blocks) + "\nREADME.md working-tree content is deliberately excluded. No commit or push performed.\n").encode()


def summary(tests):
    return f"""# SPICT-4ALL FI — T1 terminology closure audit

Project: rigorous, evidence-traceable Finnish adaptation of official SPICT-4ALL 2026.
Package: WP-T1-AUDIT-PACKAGE-001, 2026-09-08.
T1 purpose: terminology evidence collection, human-review preparation, review reduction and pre-G1 closure. This is not a translation stage.

**Final T1 status: READY_FOR_G1. 29 concepts reviewed. 0 pre-G1 terminology blockers. 0 active Sami-review items.**

## Explicit human decisions

- T-002: elinikää lyhentävät terveydentilat — Project Owner.
- T-013: hengityskone — Project Owner.
- T-016: kokonaisvaltainen hoito — Sami / domain expert, as reported by Project Owner.

These three ACCEPT records preserve explicit human project decisions, with original decision dates unprovided. No AI suggestion became APPROVED merely because a model proposed it. The controlled glossary still contains 0 APPROVED entries. No G1 translation was performed. Unresolved stylistic/non-material wording may proceed to independent A/B translation and synthesis.

The Project Owner removed T-003, T-018 and T-027 from mandatory pre-G1 review. Frailty (T-009) remains already discussed, without invented final wording; its missing disposition is not a pre-G1 blocker. T1_3_project_owner_disposition.json and T1_TERMINOLOGY_CLOSURE_REPORT.md supersede historical review-priority recommendations.

## Exact validation results and independent reproduction

The isolated payload snapshot passed **{tests} tests** and all 13 commands: pytest; official sources; source requirements; canonical units; governance; terminology; compileall; strict mypy; ruff; T1, T1.1, T1.2 and T1.3 validators. Full command outputs are in T1_AUDIT_VALIDATION_RESULTS.json. The isolated test run explicitly imported src/spict4all from the copied payload, not the original checkout.

Use Python 3.12+ in a new virtual environment. Install requirements-dev.lock, then install this tree with `python -m pip install --no-deps -e .`. Run the commands in T1_AUDIT_VALIDATION_RESULTS.json from the extracted root. No API key, Firecrawl access, Node.js, .git directory or original checkout is required for the Python tests and validators. Existing test-generated synthetic candidates are test fixtures only, not G1 work.

The delivered ZIP is verified independently after sealing. All repository commands are then rerun. These post-sealing results are in the detached `.verification.json` companion, bound to the final ZIP SHA-256; an immutable archive cannot embed a later result about its own final bytes without changing those bytes.

## Scope and preserved limitations

All terminology/adjudication files (including enrichment, historical queues and ledgers) are included byte-for-byte. Five original terminology reference files and four frozen official source documents are included for recomputation. Current sources, schemas, tests and their required runtime modules are included; older unrelated audit builders, archives, caches and the unrelated root README.md worktree artifact are excluded. The three frozen data/source README files are included because existing integrity checks require their exact bytes; the unchanged terminology/README.md explains the evidence layer. DOCX source documents retain their native OOXML ZIP-container format; there is no nested .zip/archive deliverable.

Source-authority bookkeeping for the normalized title and liver-transplant requirement remains unresolved and publication-blocking where recorded. READY_FOR_G1 is terminology readiness, not publication approval or proof that every workflow gate passed. Three further explicit phrase decisions (less well; less able to manage usual activities; not well enough for cancer treatment) are preserved in T1.2 without invented decision IDs. Frailty's exact final human wording remains unrecorded.

The T1.1 short source fragments, URLs, identifiers, retrieval timestamps and hashes are retained unchanged. Raw Firecrawl response caches are deliberately excluded. All 28 quoted fragments were matched to article markdown in the original T1.1 run; offline reviewers can inspect the retained evidence but cannot independently recompute the excluded raw-response hashes. A fresh fetch may differ. The historical Firecrawl builder requires external retrieval receipts; it is not an offline evidence-regeneration command. Historical artifact-tool TSV builders require the originally documented Node/@oai/artifact-tool runtime. These authoring dependencies are not needed to validate the delivered TSVs.

The T1.1 initial snapshot has two filename-encoding corrections documented in its separate correction record. Original snapshots and all prior decisions are unchanged. The package contains no new terminology research, questions or decisions.

## Hash coverage and immutability

Members are sorted and ZIP timestamps/permissions fixed. T1_AUDIT_MANIFEST.json lists every member and hashes all payload members except itself and T1_AUDIT_FILE_HASHES.tsv. The internal TSV hashes every member except itself, including the manifest. The detached `.members.sha256` hashes **every** ZIP member, including both index files, avoiding an impossible self-hash cycle. The `.zip.sha256` file hashes the ZIP itself.

Verify with `python scripts/verify_t1_audit_package.py /path/to/{NAME}` while keeping the .sha256 and .members.sha256 companions alongside it. The verifier independently checks membership, every hash, CRC, frozen official and terminology files, final closure status and zero active Sami items. Creation refuses to overwrite an existing delivery. Cryptographic hashes detect modification; this is not a digital signature or write-once storage guarantee.

T1_GIT_STATE.txt records the actual dirty/untracked state, not a commit claim. No unrelated README worktree content, credentials, .git, temporary files, caches or earlier audit ZIPs are included. No commit or push was performed.
""".encode()


def main():
    destination = ROOT / "deliverables/audit" / NAME
    companions = [destination, Path(str(destination) + ".sha256"), Path(str(destination) + ".members.sha256"), Path(str(destination) + ".verification.json")]
    if any(p.exists() for p in companions):
        raise FileExistsError("Audit delivery already exists; refusing overwrite")
    payload = collect()
    initial_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    with tempfile.TemporaryDirectory(prefix="spict-t1-audit-") as scratch:
        stage = Path(scratch)
        for name, data in payload.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        pre = validate_tree(stage, "isolated_payload_before_sealing")
    for name, digest in initial_hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Input changed during validation: {name}")
    payload["T1_AUDIT_SUMMARY.md"] = summary(pre["tests_passed"])
    payload["T1_AUDIT_VALIDATION_RESULTS.json"] = encode(pre)
    payload["T1_GIT_STATE.txt"] = git_state()
    names = sorted(set(payload) | {"T1_AUDIT_MANIFEST.json", "T1_AUDIT_FILE_HASHES.tsv"})
    payload["T1_AUDIT_MANIFEST.json"] = encode({
        "work_package": "WP-T1-AUDIT-PACKAGE-001", "t1_status": "READY_FOR_G1", "concepts": 29,
        "active_sami_items": 0, "pre_g1_terminology_blockers": 0, "members": names,
        "payload_sha256": {n: hashlib.sha256(d).hexdigest() for n, d in sorted(payload.items())},
        "hash_coverage_note": "Internal TSV additionally hashes this manifest. Detached .members.sha256 hashes every member including both index files; no recursive/self hash is claimed.",
        "native_source_containers": "The three .docx members are original source documents in native OOXML format, not nested audit archives."})
    payload["T1_AUDIT_FILE_HASHES.tsv"] = ("path\tsha256\tbytes\n" + "".join(
        f"{n}\t{hashlib.sha256(d).hexdigest()}\t{len(d)}\n" for n, d in sorted(payload.items()))).encode()
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100444 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    companions[1].write_text(f"{digest}  {NAME}\n", encoding="utf-8")
    companions[2].write_text("".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(payload.items())), encoding="utf-8")
    verifier = subprocess.run([sys.executable, str(ROOT / "scripts/verify_t1_audit_package.py"), str(destination)], capture_output=True, text=True, encoding="utf-8")
    if verifier.returncode:
        raise ValueError(verifier.stderr)
    independent = json.loads(verifier.stdout)
    print(json.dumps(independent), flush=True)
    # Validate the sealed archive's extracted contents without untracked local resources.
    with tempfile.TemporaryDirectory(prefix="spict-t1-sealed-") as scratch:
        extracted = Path(scratch)
        with zipfile.ZipFile(destination) as archive:
            archive.extractall(extracted)  # All names independently checked above.
        environment = dict(os.environ, PYTHONPATH=str(extracted / "src"), PYTHONIOENCODING="utf-8")
        check = subprocess.run([sys.executable, "scripts/validate_t1_3_closure.py"], cwd=extracted, env=environment, capture_output=True, text=True, encoding="utf-8")
        if check.returncode:
            raise ValueError(check.stderr)
    post = validate_tree(ROOT, "repository_after_final_zip_sealed")
    for name, expected in initial_hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Packaged repository input changed: {name}")
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise ValueError("Sealed ZIP changed")
    companions[3].write_bytes(encode({"archive_verification": independent, "sealed_extracted_closure_validation": {
        "exit_code": check.returncode, "stdout": check.stdout, "stderr": check.stderr},
        "post_packaging_repository_validation": post, "original_payload_unchanged": True,
        "secret_screening": "PASS: explicit allowlisted content, known credential-pattern scan; no caches or credential stores included",
        "git_state_after_packaging": git_state().decode()}))
    print("COMPLETE", destination, digest, flush=True)


if __name__ == "__main__":
    main()
