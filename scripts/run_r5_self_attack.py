"""Reproduce the four acceptance attacks in disposable repository copies.

This is a second executable attack path, separate from the R5 pytest cases.
Outputs are append-only: an existing evidence output is never overwritten.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from spict4all.governance import (
    build_governance_manifest,
    serialize_governance_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    output = ROOT / "docs/R5_SELF_ATTACK_RESULTS.json"
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite {output}")
    results = []
    for attack, command, reason in (
        (
            "canonical_identity_and_membership",
            "check-final",
            "frozen canonical identity",
        ),
        (
            "publisher_as_title",
            "validate-terminology",
            "title field-specific evidence binding",
        ),
        ("official_role_substitution", "verify-sources", "Unsupported official role"),
        ("nested_unmanifested_file", "verify-sources", "unmanifested official files"),
    ):
        with tempfile.TemporaryDirectory(prefix="spict-r5-self-attack-") as temp:
            scratch = Path(temp)
            for directory in ("sources", "data", "schemas", "config", "terminology"):
                shutil.copytree(ROOT / directory, scratch / directory)
            if attack == "canonical_identity_and_membership":
                path = scratch / "data/source_units.jsonl"
                units = [
                    json.loads(line)
                    for line in path.read_text(encoding="utf-8").splitlines()
                ]
                units[0] = {**units[1], "unit_id": "S4A-2026-000"}
                path.write_text(
                    "".join(
                        json.dumps(row, ensure_ascii=False) + "\n" for row in units
                    ),
                    encoding="utf-8",
                )
                (scratch / "data/canonical_unit_exceptions.jsonl").write_text(
                    "\n", encoding="utf-8"
                )
                (scratch / "data/governance_integrity_manifest.json").write_text(
                    serialize_governance_manifest(build_governance_manifest(scratch)),
                    encoding="utf-8",
                )
            elif attack == "publisher_as_title":
                path = scratch / "terminology/sources/terminology_source_manifest.json"
                manifest = json.loads(path.read_text(encoding="utf-8"))
                metadata = manifest["sources"][0]["source_verified_metadata"]
                metadata["title"] = copy.deepcopy(metadata["publisher_organisation"])
                path.write_text(
                    json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
                )
            elif attack == "official_role_substitution":
                path = scratch / "sources/manifests/source_manifest.json"
                manifest = json.loads(path.read_text(encoding="utf-8"))
                next(row for row in manifest if "Using-SPICT" in row["filename"])[
                    "role"
                ] = "TERMINOLOGY_REFERENCE"
                path.write_text(json.dumps(manifest), encoding="utf-8")
            else:
                path = scratch / "sources/official/review-probe/test.txt"
                path.parent.mkdir()
                path.write_text("unexpected", encoding="utf-8")
            args = [
                sys.executable,
                "-m",
                "spict4all.cli",
                "--root",
                str(scratch),
                command,
            ]
            if command == "check-final":
                args.extend(
                    [
                        "--status",
                        "FINAL",
                        "--gate-results",
                        "absent.json",
                        "--review",
                        "absent.tsv",
                    ]
                )
            result = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", cwd=ROOT
            )
            if result.returncode != 1 or reason not in result.stderr:
                raise RuntimeError(
                    f"Attack did not fail for intended reason: {attack}: {result.stderr}"
                )
            results.append(
                {
                    "attack": attack,
                    "unsafe_input_rejected": True,
                    "exit_code": result.returncode,
                    "diagnostic": result.stderr.strip(),
                }
            )
    previous = [
        "tests/test_canonical_units.py::test_liver_canonical_unit_with_approved_exception_fails",
        "tests/test_canonical_units.py::test_arbitrary_fabricated_text_with_approved_exception_fails",
        "tests/test_authority_attribution.py::test_canonical_disposition_rejects_blank_attribution_fields",
        "tests/test_authority_attribution.py::test_requirement_disposition_rejects_blank_attribution_fields",
        "tests/test_reviews_and_gates.py::test_multirow_review_validation_is_per_unit_and_order_independent",
        "tests/test_artifacts.py::test_whitespace_completed_candidate_fails",
        "tests/test_terminology.py::test_unapproved_term_cannot_enter_mandatory_glossary",
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *previous],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    evidence = {
        "r5_scratch_attacks": results,
        "prior_security_regressions": {
            "test_nodes": previous,
            "exit_code": result.returncode,
            "stdout": result.stdout,
        },
    }
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(evidence, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
