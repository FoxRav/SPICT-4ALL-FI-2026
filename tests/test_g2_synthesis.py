from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from spict4all.g2_authored import DECISIONS
from spict4all.g2_synthesis import (
    ACTUAL_MODEL,
    AGENT_A_ARTIFACT,
    AGENT_B_R2_ARTIFACT,
    EXPECTED_AGREE,
    EXPECTED_COUNT,
    EXPECTED_DISAGREE,
    FROZEN_INPUT_HASHES,
    G2_RUN_DIR,
    HUMAN_TERMINOLOGY_IDS,
    HUMAN_WORDINGS,
    REQUIREMENT_ID,
    SAME_FAMILY_LIMITATION,
    STATUS,
    TITLE_ID,
    classification_counts,
    g2_run_failures,
    load_g2_run,
    verify_frozen_inputs,
)
from spict4all.hashing import sha256_file
from spict4all.jsonl import load_jsonl

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / G2_RUN_DIR
VERIFY_PATH = ROOT / "scripts/verify_g2_synthesis_audit.py"


def test_authored_decisions_cover_frozen_universe() -> None:
    ids = [str(row["unit_id"]) for row in DECISIONS]
    assert len(ids) == EXPECTED_COUNT
    assert len(set(ids)) == EXPECTED_COUNT
    counts = classification_counts(list(DECISIONS))
    assert counts["A_B_AGREE"] == EXPECTED_AGREE
    assert sum(counts[key] for key in counts if key != "A_B_AGREE") == EXPECTED_DISAGREE
    assert counts["NEW_SYNTHESIS"] == 0


def test_frozen_g1_input_hashes_unchanged() -> None:
    verify_frozen_inputs(ROOT)
    for relative, expected in FROZEN_INPUT_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_g2_run_is_complete_when_present() -> None:
    if not (RUN_DIR / "candidates.jsonl").is_file():
        pytest.skip("G2 run has not been built yet")
    failures = g2_run_failures(ROOT)
    assert failures == []
    candidates, decisions = load_g2_run(RUN_DIR)
    assert len(candidates) == EXPECTED_COUNT
    assert len(decisions) == EXPECTED_COUNT
    assert {row["status"] for row in candidates} == {STATUS}
    assert {row["model"] for row in candidates} == {ACTUAL_MODEL}
    assert all("HUMAN_APPROVED" not in json.dumps(row) for row in candidates)
    assert all(row.get("status") != "HUMAN_APPROVED" for row in decisions)
    metadata = json.loads((RUN_DIR / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["actual_model"] == ACTUAL_MODEL
    assert metadata["same_family_limitation"] == SAME_FAMILY_LIMITATION
    report = (RUN_DIR / "G2_SYNTHESIS_REPORT.md").read_text(encoding="utf-8")
    assert ACTUAL_MODEL in report
    assert SAME_FAMILY_LIMITATION in report
    title = next(row for row in candidates if row["unit_id"] == TITLE_ID)
    requirement = next(row for row in candidates if row["unit_id"] == REQUIREMENT_ID)
    assert title["extensions"]["g2_synthesis"]["final_inclusion_status"] == "UNRESOLVED"
    assert title["extensions"]["g2_synthesis"]["eligible_for_document_insertion"] is False
    assert requirement["extensions"]["g2_synthesis"]["final_inclusion_status"] == "UNRESOLVED"
    assert requirement["extensions"]["g2_synthesis"]["eligible_for_document_insertion"] is False
    by_id = {row["unit_id"]: row["candidate_fi"] for row in candidates}
    for unit_id, term_id in HUMAN_TERMINOLOGY_IDS.items():
        refs = next(row for row in decisions if row["unit_id"] == unit_id)["human_decision_refs"]
        assert term_id in refs
    for unit_id, fragments in HUMAN_WORDINGS.items():
        for fragment in fragments:
            assert fragment.casefold() in by_id[unit_id].casefold()


def test_agent_evidence_and_official_sources_untouched() -> None:
    assert sha256_file(ROOT / AGENT_A_ARTIFACT) == FROZEN_INPUT_HASHES[AGENT_A_ARTIFACT]
    assert sha256_file(ROOT / AGENT_B_R2_ARTIFACT) == FROZEN_INPUT_HASHES[AGENT_B_R2_ARTIFACT]
    units = load_jsonl(ROOT / "data/source_units.jsonl")
    assert len(units) == 53
    assert (ROOT / "work/backtranslation").exists()
    later = []
    for prefix in ("work/critics", "work/final", "work/human-review"):
        directory = ROOT / prefix
        if not directory.is_dir():
            continue
        later.extend(
            path.relative_to(ROOT).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
    assert later == []


def test_g2_audit_zip_verifies_when_present() -> None:
    if not VERIFY_PATH.is_file():
        pytest.skip("G2 audit verifier is not present yet")
    spec = importlib.util.spec_from_file_location("verify_g2_synthesis_audit", VERIFY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load G2 audit verifier")
    verify_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify_mod)
    path = ROOT / "deliverables/audit" / verify_mod.NAME
    if not path.exists():
        pytest.skip("G2 synthesis audit ZIP has not been sealed yet")
    result = verify_mod.verify(path)
    assert result["crc"] == "PASS"
    assert result["actual_model"] == ACTUAL_MODEL
    assert result["human_approval_present"] is False
    assert result["clinical_validation_claimed"] is False
    assert result["g3_started"] is False
    assert result["coverage"] == f"PASS ({EXPECTED_COUNT}/{EXPECTED_COUNT})"
    assert result["member_hashes"].startswith("PASS")
    assert result["nested_archives"] == 0
