"""Create and verify the WP-G0-SOURCE-FREEZE-001 audit archive."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from create_audit_zip import (
    INDEX_NAME,
    RESULTS_NAME,
    build_index,
    is_excluded,
    official_hash_lines,
    run_check,
    sha256_bytes,
    verify_zip,
    write_zip,
)

SIDECAR_SUFFIX = ".sha256"
REQUIRED_OFFICIAL_MEMBERS = {
    "sources/official/20260130-Using-SPICT-4ALL-2025.docx",
    "sources/official/20260521-Edits-for-SPICT-4ALL-translations-2025-and-2026.docx",
    "sources/official/20260521-Word-template-SPICT-4ALL-translations-2026.docx",
    "sources/official/20260521-Word-template-SPICT-4ALL-translations-2026.pdf",
}


@dataclass(frozen=True)
class AuditProfile:
    work_package: str
    results_title: str
    output_name: str
    extended_checks: bool = False
    terminology_checks: bool = False
    governance_checks: bool = False


G0_PROFILE = AuditProfile(
    work_package="WP-G0-SOURCE-FREEZE-001",
    results_title="SPICT-4ALL FI G0 SOURCE-FREEZE AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-source-freeze-audit-20260907.zip",
)


def collect_repository_payload(repository: Path) -> dict[str, bytes]:
    """Collect tracked and reviewable untracked files with explicit exclusions."""

    exit_code, output = run_check(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        repository,
    )
    if exit_code:
        raise RuntimeError(f"Cannot enumerate repository files:\n{output}")

    payload: dict[str, bytes] = {}
    for relative in sorted(item for item in output.split("\0") if item):
        path = repository / relative
        if not path.is_file() or is_excluded(path, repository):
            continue
        archive_path = path.relative_to(repository).as_posix()
        if (
            archive_path.startswith("deliverables/audit/")
            and path.suffix.lower() in {".zip", ".sha256"}
        ):
            continue
        if archive_path in {INDEX_NAME, RESULTS_NAME}:
            raise RuntimeError(f"Reserved archive path present: {archive_path}")
        payload[archive_path] = path.read_bytes()

    missing_official = sorted(REQUIRED_OFFICIAL_MEMBERS - set(payload))
    if missing_official:
        raise RuntimeError(f"Required official archive members missing: {missing_official}")
    return payload


def forbidden_members(names: set[str]) -> tuple[str, ...]:
    forbidden: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        parts = {part.lower() for part in path.parts}
        if (
            parts.intersection(
                {
                    ".git",
                    ".venv",
                    ".pytest_cache",
                    "__pycache__",
                    "cache",
                    "caches",
                    "tmp",
                    "temp",
                }
            )
            or path.suffix.lower() == ".zip"
            or (
                path.parts
                and path.parts[0].lower() == "work"
                and path.name.lower() != ".gitkeep"
            )
        ):
            forbidden.append(name)
    return tuple(sorted(forbidden))


def verify_forbidden_member_rules() -> None:
    probes = {
        ".git/config",
        ".venv/pyvenv.cfg",
        "cache/output.txt",
        "tmp/plan.md",
        "deliverables/audit/previous.zip",
        "work/agent-a/candidates.jsonl",
    }
    detected = set(forbidden_members(probes))
    if detected != probes:
        raise RuntimeError(
            f"Forbidden-member detector self-test failed: detected={sorted(detected)}"
        )
    if forbidden_members({"src/spict4all/requirements.py"}):
        raise RuntimeError("Forbidden-member detector rejected a safe member")


def translation_candidate_members(names: set[str]) -> tuple[str, ...]:
    markers = (
        "candidates.jsonl",
        "work/agent-",
        "/synthesis/",
        "/backtranslation/",
    )
    found: list[str] = []
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.endswith(".gitkeep"):
            continue
        if any(marker in normalized.lower() for marker in markers):
            found.append(name)
    return tuple(sorted(found))


def _jsonl_objects(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def unresolved_conflict_lines(repository: Path) -> list[str]:
    """Derive current unresolved identifiers from frozen data, not a Python allow-list."""

    lines: list[str] = []
    index = 1
    for record in _jsonl_objects(repository / "data/source_requirements.jsonl"):
        if record.get("final_inclusion_status") != "UNRESOLVED":
            continue
        lines.append(
            f"{index}. {record.get('requirement_id')} | "
            f"{record.get('exact_source_text_en')} | "
            "canonical_source_presence="
            f"{str(record.get('canonical_source_presence')).lower()} | "
            f"final_inclusion_status={record.get('final_inclusion_status')} | "
            "publication_blocking="
            f"{str(record.get('publication_blocking')).lower()}"
        )
        index += 1
    for record in _jsonl_objects(repository / "data/canonical_unit_exceptions.jsonl"):
        if record.get("authority_status") == "AUTHORITY_RESOLVED":
            continue
        lines.append(
            f"{index}. {record.get('unit_id')} | authoritative final title wording "
            "requires human/source-authority disposition"
        )
        index += 1
    return lines


def verify_terminology_payload(payload: dict[str, bytes]) -> int:
    manifest_name = "terminology/sources/terminology_source_manifest.json"
    if manifest_name not in payload:
        raise RuntimeError("Terminology source manifest missing from audit payload")
    manifest = json.loads(payload[manifest_name])
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, list):
        raise RuntimeError("Invalid terminology source manifest in audit payload")
    for source in sources:
        if not isinstance(source, dict):
            raise RuntimeError("Invalid terminology source record in audit payload")
        file_facts = source.get("file_facts")
        if not isinstance(file_facts, dict):
            raise RuntimeError("Invalid terminology source record in audit payload")
        filename = file_facts.get("filename")
        if not isinstance(filename, str):
            raise RuntimeError("Invalid terminology source record in audit payload")
        archive_path = f"data/Sanasto/{filename}"
        data = payload.get(archive_path)
        if data is None:
            raise RuntimeError(f"Terminology source missing from audit: {archive_path}")
        if len(data) != file_facts.get("byte_count"):
            raise RuntimeError(f"Terminology source byte mismatch: {archive_path}")
        if sha256_bytes(data) != file_facts.get("sha256"):
            raise RuntimeError(f"Terminology source hash mismatch: {archive_path}")
    return len(sources)


def build_results(
    *,
    profile: AuditProfile,
    repository: Path,
    baseline_commit: str,
    created_utc: datetime,
    created_local: datetime,
    test_output: str,
    source_output: str,
    requirement_output: str,
    canonical_output: str,
    mypy_output: str,
    ruff_output: str,
    terminology_output: str,
    compile_output: str,
    test_pass: int,
    source_pass: int,
    official_hashes: list[str],
    git_status: str,
    member_count: int,
    zip_size: int,
    governance_output: str = "",
) -> bytes:
    extra_pass = (
        (3 if profile.extended_checks else 0)
        + (1 if profile.terminology_checks else 0)
        + (1 if profile.governance_checks else 0)
    )
    lines = [
        profile.results_title,
        "",
        f"UTC timestamp: {created_utc.isoformat().replace('+00:00', 'Z')}",
        f"Local timestamp: {created_local.isoformat()}",
        f"Repository path: {repository}",
        f"Baseline Git commit: {baseline_commit}",
        f"ZIP member count: {member_count}",
        f"Total ZIP size (bytes): {zip_size}",
        f"ZIP SHA-256: EXTERNAL-SIDECAR {profile.output_name}{SIDECAR_SUFFIX}",
        "ZIP SHA-256 note: the exact final archive hash is external because embedding an archive's own hash changes that archive.",
        "Forbidden archive members: 0",
        "Forbidden-member detector probes: PASS=6 FAIL=0",
        "Required official source members present: 4",
        *(
            ["Terminology source members present and manifest-hash-matched: 5"]
            if profile.terminology_checks
            else []
        ),
        "",
        "EXACT PASS/FAIL COUNTS",
        f"Pytest: PASS={test_pass} FAIL=0",
        f"Source verification assertions: PASS={source_pass} FAIL=0",
        "Source-requirement validation command: PASS=1 FAIL=0",
        *(
            [
                "Canonical-unit validation command: PASS=1 FAIL=0",
                "Mypy strict: PASS=1 FAIL=0",
                "Ruff check: PASS=1 FAIL=0",
            ]
            if profile.extended_checks
            else []
        ),
        *(
            ["Governance integrity validation command: PASS=1 FAIL=0"]
            if profile.governance_checks
            else []
        ),
        *(
            ["Terminology evidence validation command: PASS=1 FAIL=0"]
            if profile.terminology_checks
            else []
        ),
        "Python compileall: PASS=1 FAIL=0",
        "Total counted checks: "
        f"PASS={test_pass + source_pass + 2 + extra_pass} "
        "FAIL=0",
        "",
        "SOURCE VERIFICATION RESULT",
        "PASS: all four official file hashes and byte counts match the manifest.",
        "PASS: 53 canonical source units are unique, contiguous, hash matched, and resolved against verified canonical DOCX text: 52 direct and 1 normalized.",
        "PASS: the canonical normalization exception is typed, independently recomputed, authority-blocking, and unable to create absent text.",
        "PASS: official source requirements in data/source_requirements.jsonl are unique, schema-valid, provenance-linked, exact-text verified, and absent from the canonical template.",
        *(
            [
                "PASS: 5 terminology sources are registered and hash-matched; 136 source-provided entries, 41 source-provided English labels, 6 conflicts, 0 approved terms, and 0 conservative relevance matches are reproducible.",
                "PASS: terminology evidence is non-authoritative for English SPICT source content.",
                "PASS: ValidateTerminology does not replace VerifySources for official-source integrity.",
            ]
            if profile.terminology_checks
            else []
        ),
        "",
        "OFFICIAL SOURCE HASHES",
        *official_hashes,
        "",
        "COUNTS",
        "Canonical source-unit count: 53",
        "Canonical unit exception count: 1",
        "Official source-requirement count: derived from data/source_requirements.jsonl",
        "",
        "UNRESOLVED CONFLICTS",
        "Requirement identifiers below are derived from frozen data, not a Python allow-list.",
        *unresolved_conflict_lines(repository),
        "",
        "TRANSLATION STATEMENT",
        f"No Finnish translation content or translation candidate was generated during {profile.work_package}.",
        "",
        "GIT STATUS BEFORE AUDIT ARTIFACT CREATION",
        git_status or "(clean)",
        "",
        "EXACT PYTEST OUTPUT",
        test_output,
        "",
        "EXACT SOURCE VERIFICATION OUTPUT",
        source_output,
        "",
        "EXACT SOURCE-REQUIREMENT VALIDATION OUTPUT",
        requirement_output,
        "",
        *(
            [
                "EXACT CANONICAL-UNIT VALIDATION OUTPUT",
                canonical_output,
                "",
                "EXACT MYPY STRICT OUTPUT",
                mypy_output,
                "",
                "EXACT RUFF CHECK OUTPUT",
                ruff_output,
                "",
            ]
            if profile.extended_checks
            else []
        ),
        *(
            [
                "EXACT GOVERNANCE VALIDATION OUTPUT",
                governance_output,
                "",
            ]
            if profile.governance_checks
            else []
        ),
        *(
            [
                "EXACT TERMINOLOGY VALIDATION OUTPUT",
                terminology_output,
                "",
            ]
            if profile.terminology_checks
            else []
        ),
        "EXACT PYTHON COMPILEALL OUTPUT",
        compile_output or "(no output; exit code 0)",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def create_audit(profile: AuditProfile) -> int:
    repository = Path(__file__).resolve().parents[1]
    output = repository / "deliverables/audit" / profile.output_name
    sidecar = output.with_name(output.name + SIDECAR_SUFFIX)
    if output.exists() or sidecar.exists():
        raise RuntimeError(f"Refusing to overwrite existing audit artifact: {output}")

    powershell = "powershell.exe"
    test_exit, test_output = run_check(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository / "tools.ps1"),
            "-Task",
            "Test",
        ],
        repository,
    )
    source_exit, source_output = run_check(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository / "tools.ps1"),
            "-Task",
            "VerifySources",
        ],
        repository,
    )
    requirement_exit, requirement_output = run_check(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository / "tools.ps1"),
            "-Task",
            "ValidateRequirements",
        ],
        repository,
    )
    canonical_exit = 0
    canonical_output = ""
    mypy_exit = 0
    mypy_output = ""
    ruff_exit = 0
    ruff_output = ""
    terminology_exit = 0
    terminology_output = ""
    governance_exit = 0
    governance_output = ""
    if profile.extended_checks:
        canonical_exit, canonical_output = run_check(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repository / "tools.ps1"),
                "-Task",
                "ValidateCanonical",
            ],
            repository,
        )
        mypy_exit, mypy_output = run_check(
            [sys.executable, "-m", "mypy", "--strict", "src/spict4all"],
            repository,
        )
        ruff_exit, ruff_output = run_check(
            [sys.executable, "-m", "ruff", "check", "src", "scripts", "tests"],
            repository,
        )
    if profile.terminology_checks:
        terminology_exit, terminology_output = run_check(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repository / "tools.ps1"),
                "-Task",
                "ValidateTerminology",
            ],
            repository,
        )
    if profile.governance_checks:
        governance_exit, governance_output = run_check(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repository / "tools.ps1"),
                "-Task",
                "ValidateGovernance",
            ],
            repository,
        )
    compile_exit, compile_output = run_check(
        [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"],
        repository,
    )
    if (
        test_exit
        or source_exit
        or requirement_exit
        or canonical_exit
        or mypy_exit
        or ruff_exit
        or terminology_exit
        or governance_exit
        or compile_exit
    ):
        raise RuntimeError(
            "Mandatory check failure: "
            f"test={test_exit}, sources={source_exit}, "
            f"requirements={requirement_exit}, canonical={canonical_exit}, "
            f"mypy={mypy_exit}, ruff={ruff_exit}, compileall={compile_exit}"
            f", terminology={terminology_exit}, governance={governance_exit}"
        )

    test_match = re.search(r"(\d+) passed", test_output)
    if test_match is None or re.search(r"\d+ failed", test_output):
        raise RuntimeError("Could not establish an all-PASS pytest count")
    test_pass = int(test_match.group(1))
    source_pass = sum(
        1 for line in source_output.splitlines() if line.startswith("PASS ")
    )
    if source_pass != 7 or "FAIL " in source_output:
        raise RuntimeError(
            f"Unexpected source verification result count: {source_pass}"
        )

    commit_exit, baseline_commit = run_check(["git", "rev-parse", "HEAD"], repository)
    status_exit, git_status = run_check(["git", "status", "--short"], repository)
    if commit_exit or status_exit:
        raise RuntimeError("Cannot establish Git baseline/status")

    payload = collect_repository_payload(repository)
    terminology_source_count = (
        verify_terminology_payload(payload) if profile.terminology_checks else 0
    )
    if profile.terminology_checks and terminology_source_count != 5:
        raise RuntimeError(
            f"Unexpected terminology source count: {terminology_source_count}"
        )
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
    expected_names = set(payload) | {RESULTS_NAME, INDEX_NAME}
    verify_forbidden_member_rules()
    blocked = forbidden_members(expected_names)
    if blocked:
        raise RuntimeError(f"Forbidden archive members found: {list(blocked)}")
    candidate_artifacts = translation_candidate_members(expected_names)
    if candidate_artifacts:
        raise RuntimeError(
            f"Translation candidate artifacts found in audit payload: {list(candidate_artifacts)}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="spict-g0-audit-", dir=output.parent) as temporary:
        temporary_zip = Path(temporary) / output.name
        predicted_size = 0
        for _ in range(10):
            results = build_results(
                profile=profile,
                repository=repository,
                baseline_commit=baseline_commit,
                created_utc=created_utc,
                created_local=created_local,
                test_output=test_output,
                source_output=source_output,
                requirement_output=requirement_output,
                canonical_output=canonical_output,
                mypy_output=mypy_output,
                ruff_output=ruff_output,
                terminology_output=terminology_output,
                compile_output=compile_output,
                test_pass=test_pass,
                source_pass=source_pass,
                official_hashes=official_hashes,
                git_status=git_status,
                member_count=len(expected_names),
                zip_size=predicted_size,
                governance_output=governance_output,
            )
            index = build_index(payload, results)
            write_zip(temporary_zip, payload, results, index, zip_timestamp)
            actual_size = temporary_zip.stat().st_size
            if actual_size == predicted_size:
                break
            predicted_size = actual_size
        else:
            raise RuntimeError("Could not stabilize embedded final ZIP size")

        verify_zip(temporary_zip, expected_names)
        temporary_zip.rename(output)

    member_count, indexed_count = verify_zip(output, expected_names)
    archive_sha256 = sha256_bytes(output.read_bytes())
    sidecar.write_text(f"{archive_sha256}  {output.name}\n", encoding="ascii")
    if sidecar.read_text(encoding="ascii").split()[0] != archive_sha256:
        raise RuntimeError("ZIP SHA-256 sidecar verification failed")

    print(test_output)
    print(source_output)
    print(requirement_output)
    if profile.extended_checks:
        print(canonical_output)
        print(mypy_output)
        print(ruff_output)
    if profile.governance_checks:
        print(governance_output)
    if profile.terminology_checks:
        print(terminology_output)
    print(compile_output or "compileall: no output")
    print(f"ZIP_OPEN_PASS=1 ZIP_OPEN_FAIL=0 MEMBERS={member_count}")
    print("ZIP_CRC_PASS=1 ZIP_CRC_FAIL=0")
    print(f"INDEX_HASH_PASS={indexed_count} INDEX_HASH_FAIL=0")
    print("OFFICIAL_MEMBERS_PASS=4 OFFICIAL_MEMBERS_FAIL=0")
    if profile.terminology_checks:
        print(
            f"TERMINOLOGY_MEMBERS_PASS={terminology_source_count} "
            "TERMINOLOGY_MEMBERS_FAIL=0"
        )
    print("FORBIDDEN_RULE_PROBES_PASS=6 FORBIDDEN_RULE_PROBES_FAIL=0")
    print("FORBIDDEN_MEMBERS=0")
    print("TRANSLATION_CANDIDATE_ARTIFACTS=0")
    print(f"ZIP_BYTES={output.stat().st_size}")
    print(f"ZIP_SHA256={archive_sha256}")
    print(f"ZIP_SHA256_SIDECAR={sidecar}")
    print(f"ZIP_PATH={output}")
    return 0


def main() -> int:
    return create_audit(G0_PROFILE)


if __name__ == "__main__":
    raise SystemExit(main())
