"""Create and verify the SPICT-4ALL FI bootstrap audit ZIP."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ROOT_FILES = (
    ".editorconfig",
    ".gitignore",
    "AGENTS.md",
    "BOOTSTRAP_CODEX.md",
    "NOTICE.md",
    "PACKAGE_MANIFEST.json",
    "README.md",
    "pyproject.toml",
    "requirements-dev.lock",
    "tools.ps1",
)
ROOT_DIRECTORIES = (
    "config",
    "data",
    "docs",
    "prompts",
    "schemas",
    "scripts",
    "sources",
    "src",
    "templates",
    "terminology",
    "tests",
    ".cursor/rules",
)
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "cache",
    "caches",
    "tmp",
    "temp",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".temp", ".zip"}
OFFICIAL_SOURCE_DIRECTORY = "sources/official"
INDEX_NAME = "AUDIT_INDEX.txt"
RESULTS_NAME = "AUDIT_RESULTS.txt"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run_check(command: list[str], cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.rstrip()


def is_excluded(path: Path, repository: Path) -> bool:
    relative = path.relative_to(repository)
    if any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in relative.parts[:-1]):
        return True
    if path.name.startswith("~$") or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return False


def collect_payload(repository: Path) -> dict[str, bytes]:
    paths: set[Path] = set()
    for relative in ROOT_FILES:
        path = repository / relative
        if not path.is_file():
            raise RuntimeError(f"Required audit file is missing: {relative}")
        paths.add(path)
    for relative in ROOT_DIRECTORIES:
        directory = repository / relative
        if not directory.is_dir():
            raise RuntimeError(f"Required audit directory is missing: {relative}")
        for path in directory.rglob("*"):
            if path.is_file() and not is_excluded(path, repository):
                paths.add(path)

    payload: dict[str, bytes] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(repository).as_posix()):
        archive_path = path.relative_to(repository).as_posix()
        if archive_path in {INDEX_NAME, RESULTS_NAME}:
            raise RuntimeError(f"Reserved archive path present in repository: {archive_path}")
        payload[archive_path] = path.read_bytes()

    required_official = {
        "20260130-Using-SPICT-4ALL-2025.docx",
        "20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx",
        "20260521-Word-template-SPICT-4ALL-translations-2026.docx",
        "20260521-Word-template-SPICT-4ALL-translations-2026.pdf",
    }
    packaged_official = {
        PurePosixPath(name).name
        for name in payload
        if str(PurePosixPath(name).parent) == OFFICIAL_SOURCE_DIRECTORY
        and PurePosixPath(name).suffix.lower() in {".docx", ".pdf"}
    }
    if packaged_official != required_official:
        raise RuntimeError(
            "Official audit payload mismatch: "
            f"expected={sorted(required_official)}, actual={sorted(packaged_official)}"
        )
    return payload


def build_index(payload: dict[str, bytes], results: bytes) -> bytes:
    lines = [
        "# SPICT-4ALL FI audit archive index",
        "# Columns: relative_path, byte_size, sha256",
        "# AUDIT_INDEX.txt is the sole exception: a file cannot contain its own archived SHA-256 without a circular definition.",
        "relative_path\tbyte_size\tsha256",
    ]
    indexed = dict(payload)
    indexed[RESULTS_NAME] = results
    for path in sorted(indexed):
        data = indexed[path]
        lines.append(f"{path}\t{len(data)}\t{sha256_bytes(data)}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def official_hash_lines(repository: Path) -> list[str]:
    manifest = json.loads(
        (repository / "sources/manifests/source_manifest.json").read_text(encoding="utf-8")
    )
    lines: list[str] = []
    for item in sorted(manifest, key=lambda value: value["filename"]):
        path = repository / OFFICIAL_SOURCE_DIRECTORY / item["filename"]
        data = path.read_bytes()
        digest = sha256_bytes(data)
        if digest != item["sha256"] or len(data) != item["bytes"]:
            raise RuntimeError(f"Official source changed after verification: {item['filename']}")
        lines.append(
            f"{item['filename']} | bytes={len(data)} | sha256={digest} | role={item['role']}"
        )
    return lines


def build_results(
    *,
    repository: Path,
    created_utc: datetime,
    created_local: datetime,
    test_output: str,
    source_output: str,
    compile_output: str,
    test_pass: int,
    source_pass: int,
    git_status: str,
    official_hashes: list[str],
    total_file_count: int,
    zip_size: int,
) -> bytes:
    lines = [
        "SPICT-4ALL FI BOOTSTRAP AUDIT RESULTS",
        "",
        f"UTC creation timestamp: {created_utc.isoformat().replace('+00:00', 'Z')}",
        f"Local creation timestamp: {created_local.isoformat()}",
        f"Repository path: {repository}",
        f"Total archived file count: {total_file_count}",
        f"Total ZIP size (bytes): {zip_size}",
        "",
        "CHECK COUNTS",
        f"Pytest: PASS={test_pass} FAIL=0",
        f"Source verification: PASS={source_pass} FAIL=0",
        "Python compileall: PASS=1 FAIL=0",
        f"Mandatory checks total: PASS={test_pass + source_pass + 1} FAIL=0",
        "",
        "OFFICIAL SOURCE HASHES",
        *official_hashes,
        "",
        "UNRESOLVED BLOCKERS",
        "1. The official change specification contains the liver-problem line 'A liver transplant is not possible.', which is absent from the canonical 2026 template and source-unit index. Source-authority resolution is required before translation.",
        "2. Source unit S4A-2026-000 requires an authority decision for the document title.",
        "3. Page-image inspection of the new official DOCX remains pending because the provided workspace runtime has no bundled LibreOffice executable; structural inspection completed.",
        "",
        "GIT STATUS",
        git_status or "(clean)",
        "",
        "TRANSLATION STATEMENT",
        "No SPICT-4ALL content was translated and no Finnish translation candidate was created during bootstrap audit packaging.",
        "",
        "AUDIT INDEX NOTE",
        "AUDIT_INDEX.txt hashes every archived file except itself. Including the archived hash of the index inside that same index would be a circular cryptographic definition.",
        "",
        "EXACT TEST OUTPUT",
        test_output,
        "",
        "EXACT SOURCE VERIFICATION OUTPUT",
        source_output,
        "",
        "EXACT PYTHON COMPILEALL OUTPUT",
        compile_output or "(no output; exit code 0)",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def write_member(
    archive: zipfile.ZipFile,
    name: str,
    data: bytes,
    timestamp: tuple[int, int, int, int, int, int],
    compression: int,
) -> None:
    info = zipfile.ZipInfo(name, date_time=timestamp)
    info.compress_type = compression
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def write_zip(
    output: Path,
    payload: dict[str, bytes],
    results: bytes,
    index: bytes,
    timestamp: tuple[int, int, int, int, int, int],
) -> None:
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for name in sorted(payload):
            write_member(archive, name, payload[name], timestamp, zipfile.ZIP_DEFLATED)
        write_member(archive, RESULTS_NAME, results, timestamp, zipfile.ZIP_STORED)
        write_member(archive, INDEX_NAME, index, timestamp, zipfile.ZIP_STORED)


def verify_zip(path: Path, expected_names: set[str]) -> tuple[int, int]:
    with zipfile.ZipFile(path, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC verification failed")
        names = set(archive.namelist())
        if names != expected_names:
            raise RuntimeError(
                f"ZIP member mismatch: missing={sorted(expected_names - names)}, "
                f"extra={sorted(names - expected_names)}"
            )
        index_text = archive.read(INDEX_NAME).decode("utf-8")
        rows = csv.DictReader(
            (line for line in io.StringIO(index_text) if not line.startswith("#")),
            delimiter="\t",
        )
        verified = 0
        for row in rows:
            name = row["relative_path"]
            data = archive.read(name)
            if len(data) != int(row["byte_size"]):
                raise RuntimeError(f"Indexed byte-size mismatch: {name}")
            if sha256_bytes(data) != row["sha256"]:
                raise RuntimeError(f"Indexed SHA-256 mismatch: {name}")
            verified += 1
        if verified != len(expected_names) - 1:
            raise RuntimeError(
                f"Index coverage mismatch: verified={verified}, expected={len(expected_names) - 1}"
            )
        results_text = archive.read(RESULTS_NAME).decode("utf-8")
        size_match = re.search(r"^Total ZIP size \(bytes\): (\d+)$", results_text, re.MULTILINE)
        if size_match is None or int(size_match.group(1)) != path.stat().st_size:
            raise RuntimeError("AUDIT_RESULTS.txt does not contain the final ZIP byte size")
    return len(expected_names), verified


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    output = repository / "deliverables/audit/SPICT4ALL-FI-bootstrap-audit-20260907.zip"
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite existing audit artifact: {output}")

    powershell = os.environ.get("COMSPEC", "").lower()
    powershell_exe = "powershell.exe" if powershell.endswith("cmd.exe") else "powershell.exe"
    test_command = [
        powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(repository / "tools.ps1"), "-Task", "Test",
    ]
    source_command = [
        powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(repository / "tools.ps1"), "-Task", "VerifySources",
    ]
    compile_command = [
        sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests",
    ]

    test_exit, test_output = run_check(test_command, repository)
    source_exit, source_output = run_check(source_command, repository)
    compile_exit, compile_output = run_check(compile_command, repository)
    if test_exit or source_exit or compile_exit:
        print(test_output)
        print(source_output)
        print(compile_output)
        raise RuntimeError(
            f"Mandatory check failure: test={test_exit}, sources={source_exit}, compileall={compile_exit}"
        )

    test_match = re.search(r"(\d+) passed", test_output)
    if test_match is None or re.search(r"\d+ failed", test_output):
        raise RuntimeError("Could not establish an all-PASS pytest count")
    test_pass = int(test_match.group(1))
    source_pass = sum(1 for line in source_output.splitlines() if line.startswith("PASS "))
    if source_pass == 0 or any(line.startswith("FAIL ") for line in source_output.splitlines()):
        raise RuntimeError("Could not establish an all-PASS source verification count")

    git_exit, git_status = run_check(["git", "status", "--short"], repository)
    if git_exit:
        raise RuntimeError(f"git status failed:\n{git_status}")

    payload = collect_payload(repository)
    official_hashes = official_hash_lines(repository)
    created_utc = datetime.now(UTC).replace(microsecond=0)
    created_local = created_utc.astimezone()
    zip_timestamp = (
        created_local.year,
        created_local.month,
        created_local.day,
        created_local.hour,
        created_local.minute,
        created_local.second - (created_local.second % 2),
    )
    total_file_count = len(payload) + 2
    expected_names = set(payload) | {RESULTS_NAME, INDEX_NAME}

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="spict-audit-", dir=output.parent) as temporary:
        temporary_zip = Path(temporary) / output.name
        predicted_size = 0
        for _ in range(10):
            results = build_results(
                repository=repository,
                created_utc=created_utc,
                created_local=created_local,
                test_output=test_output,
                source_output=source_output,
                compile_output=compile_output,
                test_pass=test_pass,
                source_pass=source_pass,
                git_status=git_status,
                official_hashes=official_hashes,
                total_file_count=total_file_count,
                zip_size=predicted_size,
            )
            index = build_index(payload, results)
            write_zip(temporary_zip, payload, results, index, zip_timestamp)
            actual_size = temporary_zip.stat().st_size
            if actual_size == predicted_size:
                break
            predicted_size = actual_size
        else:
            raise RuntimeError("Could not stabilize the embedded final ZIP size")

        member_count, indexed_count = verify_zip(temporary_zip, expected_names)
        temporary_zip.rename(output)

    member_count, indexed_count = verify_zip(output, expected_names)
    print(test_output)
    print(source_output)
    print(compile_output or "compileall: no output")
    print(f"ZIP_OPEN_PASS=1 ZIP_OPEN_FAIL=0 MEMBERS={member_count}")
    print(f"INDEX_HASH_PASS={indexed_count} INDEX_HASH_FAIL=0")
    print(f"ZIP_BYTES={output.stat().st_size}")
    print(f"ZIP_SHA256={sha256_bytes(output.read_bytes())}")
    print(f"ZIP_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
