from __future__ import annotations

import csv
import json
from pathlib import Path

from spict4all.g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_RELATIVE,
    CRITIC_B_RELATIVE,
    EXPECTED_HASHES,
    FRAILTY_ID,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    REQUIREMENT_ID,
    TITLE_ID,
)
from spict4all.g5_human_dispositions import (
    BATCH_BY_ID,
    BATCH_IDS,
    COMPLETED_DISPOSITIONS,
    HUMAN_TSV_FIELDS,
    PARTIAL_STATUS,
    REMAINING_DISPOSITIONS,
    SAMI_REVIEW_IDS,
    SUPERSEDED_AT_G5,
)
from spict4all.g5_human_review import (
    CHECKED_BOX,
    DISPOSITION_OPTIONS,
    DOMAIN_EXPERT_REASONS,
    EXPECTED_COUNT,
    EXPECTED_TIER_1,
    EXPECTED_TIER_2,
    G5_RUN_DIR,
    G5_RUN_ID,
    REQUIRED_OUTPUTS,
    TSV_COLUMNS,
    g5_run_failures,
    load_dispositions,
    load_packet_units,
    render_required_artifacts,
    tier_ids,
)
from spict4all.hashing import sha256_file
from spict4all.jsonl import load_jsonl

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / G5_RUN_DIR
README = ROOT / "README.md"


def test_frozen_g2_g3_g4_inputs_unchanged() -> None:
    for relative, expected in EXPECTED_HASHES.items():
        assert sha256_file(ROOT / relative) == expected
    assert sha256_file(ROOT / COMBINED_RELATIVE) == (
        "29d8ec2a0f8588de7a331088be0181eb169c84337e390d273957f2b86e1e5f19"
    )


def test_packet_units_cover_canonical_order() -> None:
    units = load_packet_units(ROOT)
    g2 = load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)
    assert len(units) == EXPECTED_COUNT
    assert [unit.unit_id for unit in units] == [row["unit_id"] for row in g2]
    assert len({unit.unit_id for unit in units}) == EXPECTED_COUNT
    assert tuple(tier_ids(units, "TIER_1")) == EXPECTED_TIER_1
    assert tuple(tier_ids(units, "TIER_2")) == EXPECTED_TIER_2
    assert len(tier_ids(units, "TIER_3")) == (
        EXPECTED_COUNT - len(EXPECTED_TIER_1) - len(EXPECTED_TIER_2)
    )


def test_g5_run_when_present() -> None:
    if not (RUN_DIR / "human_dispositions.tsv").is_file():
        return
    failures = g5_run_failures(ROOT)
    assert failures == []
    rows = load_dispositions(RUN_DIR / "human_dispositions.tsv")
    assert len(rows) == EXPECTED_COUNT
    assert [row["unit_id"] for row in rows] == [
        unit.unit_id for unit in load_packet_units(ROOT)
    ]
    populated = [
        row["unit_id"]
        for row in rows
        if any(row.get(field, "") for field in HUMAN_TSV_FIELDS)
    ]
    assert tuple(populated) == BATCH_IDS
    blank = 0
    for row in rows:
        decision = BATCH_BY_ID.get(row["unit_id"])
        if decision is None:
            for field in HUMAN_TSV_FIELDS:
                assert row[field] == ""
            blank += 1
            continue
        assert row["human_disposition"] == decision["human_disposition"]
        assert row["final_finnish"] == decision["final_finnish"]
        assert row["reviewer"] == "Project Owner"
        assert row["reviewer_role"] == "Project Owner / human adjudicator"
        assert row["decision_date"] == "2026-09-08"
    assert blank == REMAINING_DISPOSITIONS
    packet = (RUN_DIR / "G5_HUMAN_REVIEW_PACKET.md").read_text(encoding="utf-8")
    assert CHECKED_BOX.search(packet) is None
    for option in DISPOSITION_OPTIONS:
        assert f"[ ] {option}" in packet
    summary = json.loads((RUN_DIR / "G5_REVIEW_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["run_id"] == G5_RUN_ID
    assert summary["total_units"] == EXPECTED_COUNT
    assert summary["tier_1_count"] == len(EXPECTED_TIER_1)
    assert summary["tier_2_count"] == len(EXPECTED_TIER_2)
    assert summary["status"] == PARTIAL_STATUS
    assert summary["completed_human_dispositions"] == COMPLETED_DISPOSITIONS
    assert summary["remaining_human_dispositions"] == REMAINING_DISPOSITIONS
    assert summary["human_adjudication_complete"] is False
    assert summary["g5_gate_passed"] is False
    assert summary["g6_started"] is False
    assert summary["source_authority_resolved"] is False
    assert summary["clinical_validation_claimed"] is False
    assert summary["source_authority_blocker_ids"] == [TITLE_ID, REQUIREMENT_ID]
    assert summary["existing_human_decision_conflict_ids"] == [
        unit.unit_id
        for unit in load_packet_units(ROOT)
        if unit.human_decision_conflict
    ]
    assert summary["domain_expert_review_recommended_ids"] == [
        unit.unit_id
        for unit in load_packet_units(ROOT)
        if unit.domain_expert_review_recommended
    ]
    assert summary["domain_expert_review_recommended_ids"] == list(DOMAIN_EXPERT_REASONS)
    title = next(unit for unit in load_packet_units(ROOT) if unit.unit_id == TITLE_ID)
    requirement = next(
        unit for unit in load_packet_units(ROOT) if unit.unit_id == REQUIREMENT_ID
    )
    frailty = next(unit for unit in load_packet_units(ROOT) if unit.unit_id == FRAILTY_ID)
    assert title.source_authority_status == "UNRESOLVED"
    assert requirement.source_authority_status == "NONCANONICAL"
    assert frailty.frailty_human_wording_status == (
        "NO_FINAL_RECORDED_HUMAN_WORDING_DECISION"
    )
    assert frailty.human_decision_conflict == ""
    highlight = (RUN_DIR / "G5_PRIORITY_REVIEW.md").read_text(encoding="utf-8")
    assert "S4A-2026-025" in highlight
    assert "S4A-2026-045" in highlight
    assert "No option is recommended as authoritative." in highlight
    for unit_id in EXPECTED_TIER_1:
        assert unit_id in highlight
    clean = (RUN_DIR / "G5_CLEAN_UNITS.md").read_text(encoding="utf-8")
    for unit in load_packet_units(ROOT):
        if unit.review_tier == "TIER_3":
            assert unit.unit_id in clean
        elif unit.review_tier == "TIER_1":
            assert f"## {unit.unit_id}" not in clean
    readme = README.read_text(encoding="utf-8")
    assert "| **G4** | Independent critics and adversarial review | **PASS** |" in readme
    assert (
        "| **G5** | Human adjudication and final source reconciliation | **IN PROGRESS** |"
        in readme
    )
    assert "| **G6** | Target-user testing and external review | Pending |" in readme


def test_g5_finnish_matches_g2_and_backtranslation_matches_g3() -> None:
    units = {unit.unit_id: unit for unit in load_packet_units(ROOT)}
    g2 = {row["unit_id"]: row["candidate_fi"] for row in load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)}
    back = {
        row["unit_id"]: row["back_translation_en"]
        for row in load_jsonl(ROOT / G3_BACK_RELATIVE)
    }
    for unit_id, unit in units.items():
        assert unit.current_candidate_fi == g2[unit_id]
        assert unit.back_translation_en == back[unit_id]


def test_render_is_deterministic() -> None:
    units = load_packet_units(ROOT)
    first = render_required_artifacts(units, ROOT, "2026-09-08T00:00:00Z")
    second = render_required_artifacts(units, ROOT, "2026-09-08T00:00:00Z")
    assert first == second
    assert set(first) == set(REQUIRED_OUTPUTS)
    reader = csv.DictReader(first["human_dispositions.tsv"].splitlines(), delimiter="\t")
    assert reader.fieldnames == list(TSV_COLUMNS)


def test_no_g5_audit_zip_or_document_generation() -> None:
    final = ROOT / "work/final"
    if final.is_dir():
        leftover = [
            path
            for path in final.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        ]
        assert leftover == []
    audit = ROOT / "deliverables/audit"
    if audit.is_dir():
        forbidden = [
            path.name
            for path in audit.rglob("*")
            if path.is_file() and ("G5" in path.name.upper() or "G6" in path.name.upper())
        ]
        assert forbidden == []


def test_critic_outputs_untouched_paths() -> None:
    assert (ROOT / CRITIC_A_RELATIVE).is_file()
    assert (ROOT / CRITIC_B_RELATIVE).is_file()
    assert sha256_file(ROOT / CRITIC_A_RELATIVE) == EXPECTED_HASHES[CRITIC_A_RELATIVE]
    assert sha256_file(ROOT / CRITIC_B_RELATIVE) == EXPECTED_HASHES[CRITIC_B_RELATIVE]


def test_recorded_batch_events_and_sami_packet() -> None:
    events = load_jsonl(RUN_DIR / "human_decision_events.jsonl")
    assert len(events) == COMPLETED_DISPOSITIONS
    assert [row["unit_id"] for row in events] == list(BATCH_IDS)
    for event in events:
        decision = BATCH_BY_ID[str(event["unit_id"])]
        assert event["final_finnish"] == decision["final_finnish"]
        assert event["human_disposition"] == decision["human_disposition"]
        assert event["reviewer"] == "Project Owner"
        assert event["decision_source"] == (
            "explicit Project Owner decision in ChatGPT project session"
        )
        assert event["source_authority_resolved"] is False
    superseded = {
        row["unit_id"]
        for row in events
        if row["prior_human_decision_status"] == SUPERSEDED_AT_G5
    }
    assert superseded == {"S4A-2026-001", "S4A-2026-042"}
    rows = {row["unit_id"]: row for row in load_dispositions(RUN_DIR / "human_dispositions.tsv")}
    g2 = {
        row["unit_id"]: row["candidate_fi"]
        for row in load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)
    }
    assert rows["S4A-2026-008"]["final_finnish"] == g2["S4A-2026-008"]
    sami = (RUN_DIR / "G5_SAMI_DOMAIN_REVIEW.md").read_text(encoding="utf-8")
    assert CHECKED_BOX.search(sami) is None
    for unit_id in SAMI_REVIEW_IDS:
        assert f"## {unit_id}" in sami
    assert "being referred for domain-expert reconsideration" in sami
    assert "No final human frailty wording exists" in sami
    assert "Critic A HIGH, Critic B HIGH" in sami
    assert "Critic A BLOCKER, Critic B HIGH" in sami
    assert "did NOT decide how 'spiritual' should be translated" in sami
    assert "No critic wording is recommended as authoritative." in sami
