from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.errors import ArtifactValidationError, ImmutableRunError
from spict4all.g1_b_correction import (
    AUTHORIZED_CORRECTION_UNIT_IDS,
    CORRECTED_CANDIDATE_FI,
    FROZEN_G1_B_001_HASHES,
    G1_B_002_RUN_ID,
    build_correction_diff,
    load_jsonl_records,
    refuse_frozen_overwrite,
    verify_frozen_g1_b_001,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "work/agent-b/runs" / G1_B_002_RUN_ID


def test_frozen_original_hashes_match_sealed_values() -> None:
    verify_frozen_g1_b_001(ROOT)
    for relative, expected in FROZEN_G1_B_001_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_refuse_overwrite_of_frozen_001() -> None:
    with pytest.raises(ImmutableRunError, match="Refusing to overwrite"):
        refuse_frozen_overwrite(ROOT / "work/agent-b/candidates.jsonl", ROOT)
    with pytest.raises(ImmutableRunError, match="Refusing to overwrite"):
        refuse_frozen_overwrite(ROOT / "work/agent-b/agent_b_translations.json", ROOT)


def test_correction_run_changes_only_five_candidate_fi_fields() -> None:
    original = load_jsonl_records(ROOT / "work/agent-b/candidates.jsonl")
    corrected = load_jsonl_records(RUN_DIR / "candidates.jsonl")
    diff = build_correction_diff(original, corrected)
    assert diff["changed_unit_ids"] == list(AUTHORIZED_CORRECTION_UNIT_IDS)
    assert diff["unchanged_candidate_fi_count"] == 49
    assert [item["unit_id"] for item in diff["changes"]] == list(AUTHORIZED_CORRECTION_UNIT_IDS)
    for item in diff["changes"]:
        assert item["after"] == CORRECTED_CANDIDATE_FI[item["unit_id"]]
        assert item["before"] != item["after"]
    original_by_id = {row["unit_id"]: row for row in original}
    corrected_by_id = {row["unit_id"]: row for row in corrected}
    assert set(original_by_id) == set(corrected_by_id)
    for unit_id, before in original_by_id.items():
        after = corrected_by_id[unit_id]
        assert after["source_text_sha256"] == before["source_text_sha256"]
        assert after["decision_note"] == before["decision_note"]
        assert after["issues"] == before["issues"]
        if unit_id in AUTHORIZED_CORRECTION_UNIT_IDS:
            assert after["candidate_fi"] != before["candidate_fi"]
            continue
        assert after["candidate_fi"] == before["candidate_fi"]


def test_correction_diff_rejects_unauthorized_change() -> None:
    original = load_jsonl_records(ROOT / "work/agent-b/candidates.jsonl")
    mutated = load_jsonl_records(ROOT / "work/agent-b/candidates.jsonl")
    mutated[0]["candidate_fi"] = "unauthorized change"
    with pytest.raises(ArtifactValidationError, match="Unauthorized candidate_fi"):
        build_correction_diff(original, mutated)


def test_corrected_run_has_no_human_approval() -> None:
    records = load_jsonl_records(RUN_DIR / "candidates.jsonl")
    assert len(records) == 54
    assert {row["status"] for row in records} == {"READY_FOR_SYNTHESIS"}
    metadata = (RUN_DIR / "run_metadata.json").read_text(encoding="utf-8")
    assert "HUMAN_APPROVED" not in metadata
    authored = (RUN_DIR / "agent_b_translations.json").read_text(encoding="utf-8")
    assert "HUMAN_APPROVED" not in authored
