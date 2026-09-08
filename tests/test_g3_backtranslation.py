from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from spict4all.g2_synthesis import FROZEN_INPUT_HASHES as G1_FROZEN
from spict4all.g3_backtranslation import (
    ACTUAL_MODEL,
    BACK_TRANSLATION_RELATIVE,
    BLIND_INPUT_RELATIVE,
    ENVIRONMENT,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_RUN_DIR,
    G3_RUN_ID,
    REASONING_EFFORT,
    REQUIREMENT_ID,
    TITLE_ID,
    derivation_failures,
    g2_fi_by_id,
    g3_pair_failures,
    g3_run_failures,
)
from spict4all.hashing import sha256_file
from spict4all.jsonl import load_jsonl

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / G3_RUN_DIR
VERIFY_PATH = ROOT / "scripts/verify_g3_backtranslation_audit.py"


def test_frozen_g3_jsonl_hashes() -> None:
    for relative, expected in EXPECTED_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_g1_and_g2_inputs_unchanged() -> None:
    for relative, expected in G1_FROZEN.items():
        assert sha256_file(ROOT / relative) == expected
    assert sha256_file(ROOT / G2_CANDIDATES_RELATIVE) == EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]


def test_blind_and_backtranslation_coverage() -> None:
    blind = load_jsonl(ROOT / BLIND_INPUT_RELATIVE)
    back = load_jsonl(ROOT / BACK_TRANSLATION_RELATIVE)
    failures = g3_pair_failures(blind, back)
    assert failures == []
    assert len(blind) == EXPECTED_COUNT
    assert [row["unit_id"] for row in blind] == [row["unit_id"] for row in back]
    assert {row["unit_id"] for row in blind} >= {TITLE_ID, REQUIREMENT_ID}


def test_blind_input_derives_from_g2_candidate_fi() -> None:
    blind = load_jsonl(ROOT / BLIND_INPUT_RELATIVE)
    g2 = load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)
    assert derivation_failures(blind, g2_fi_by_id(g2)) == []


def test_g3_metadata_when_present() -> None:
    if not (RUN_DIR / "run_metadata.json").is_file():
        pytest.skip("G3 metadata has not been written yet")
    failures = g3_run_failures(ROOT)
    assert failures == []
    metadata = json.loads((RUN_DIR / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["actual_model"] == ACTUAL_MODEL
    assert metadata["reasoning_effort"] == REASONING_EFFORT
    assert metadata["environment"] == ENVIRONMENT
    assert metadata["run_id"] == G3_RUN_ID
    report = (RUN_DIR / "G3_BACKTRANSLATION_REPORT.md").read_text(encoding="utf-8")
    assert "54/54" in report
    assert "no semantic comparison" in report.lower()
    validation = json.loads((RUN_DIR / "validation_results.json").read_text(encoding="utf-8"))
    assert validation["semantic_comparison_with_source_performed"] is False
    assert validation["g4_started"] is False
    assert validation["human_approval_present"] is False


def test_g3_audit_zip_verifies_when_present() -> None:
    if not VERIFY_PATH.is_file():
        pytest.skip("G3 audit verifier is not present yet")
    spec = importlib.util.spec_from_file_location("verify_g3_backtranslation_audit", VERIFY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load G3 audit verifier")
    verify_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify_mod)
    path = ROOT / "deliverables/audit" / verify_mod.NAME
    if not path.exists():
        pytest.skip("G3 audit ZIP has not been sealed yet")
    result = verify_mod.verify(path)
    assert result["crc"] == "PASS"
    assert result["actual_model"] == ACTUAL_MODEL
    assert result["g2_candidate_fi_derivation"] == "PASS"
    assert result["semantic_comparison_with_source_performed"] is False
    assert result["g4_started"] is False
    assert result["nested_archives"] == 0
    assert result["member_hashes"].startswith("PASS")
    assert result["coverage"] == f"PASS ({EXPECTED_COUNT}/{EXPECTED_COUNT})"
