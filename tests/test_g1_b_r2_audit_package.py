from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from spict4all.g1_b_correction import (
    AUTHORIZED_CORRECTION_UNIT_IDS,
    FROZEN_G1_B_001_HASHES,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g1_b_r2_audit_package.py"
SPEC = importlib.util.spec_from_file_location("verify_g1_b_r2_audit_package", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g1_b_r2_audit_package.py")
verify_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mod)


def test_r2_independence_rejects_agent_a_candidates() -> None:
    names = [
        "work/agent-a/.gitkeep",
        "work/agent-a/candidates.jsonl",
        "work/synthesis/.gitkeep",
        "work/backtranslation/.gitkeep",
        "work/critics/.gitkeep",
    ]
    failures = verify_mod.r1.independence_failures(names)
    assert any("later-gate artifact" in item for item in failures)


def test_original_001_hashes_still_match() -> None:
    for relative, expected in FROZEN_G1_B_001_HASHES.items():
        assert sha256_file(ROOT / relative) == expected
        assert verify_mod.r1.TRANSLATION_HASHES[relative] == expected


def test_authorized_unit_list_is_exactly_five() -> None:
    assert list(AUTHORIZED_CORRECTION_UNIT_IDS) == verify_mod.AUTHORIZED_UNITS
    assert len(verify_mod.AUTHORIZED_UNITS) == 5


def test_r2_delivery_zip_verifies_when_present() -> None:
    path = ROOT / "deliverables/audit" / verify_mod.NAME
    if not path.exists():
        pytest.skip("G1-B R2 audit ZIP has not been sealed yet")
    result = verify_mod.verify(path)
    assert result["crc"] == "PASS"
    assert result["actual_model"] == "Cursor Grok 4.6"
    assert result["original_run_unchanged"] is True
    assert result["corrected_run_id"] == "G1-B-20260908-002"
    assert result["changed_unit_ids"] == list(AUTHORIZED_CORRECTION_UNIT_IDS)
    assert result["human_approval_present"] is False
    assert result["translation_evidence_unchanged"] is True


def test_t1_validator_files_match_baseline_when_git_present() -> None:
    if not (ROOT / ".git").exists():
        pytest.skip("git metadata not present in isolated payload")
    result = subprocess.run(
        [
            "git",
            "--no-pager",
            "diff",
            "--exit-code",
            "2aa066fdba27fa083ff9ad78f285c0751d3f085f",
            "--",
            "src/spict4all/adjudication.py",
            "src/spict4all/terminology_closure.py",
            "tests/test_adjudication.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
