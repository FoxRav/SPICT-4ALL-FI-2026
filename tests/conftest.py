from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from spict4all.g1_t1_isolation import hide_g1_work_files
from spict4all.hashing import sha256_text

REPO_ROOT = Path(__file__).resolve().parents[1]
T1_WORK_INVENTORY_FILES = frozenset(
    {
        "test_adjudication.py",
        "test_terminology_enrichment.py",
        "test_review_reduction.py",
        "test_terminology_closure.py",
    }
)


@pytest.fixture(autouse=True)
def isolate_g1_work_from_t1_inventory(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[None]:
    """Keep historical T1 inventory exact without weakening T1 validators.

    G1 Agent A/B and G2 synthesis work files stay on disk for later-stage tests.
    T1 tests that scan `work/` see only the T1 placeholder lock, via an isolated
    hide/restore fixture. Scratch copies of `work/` inherit that pre-G1 view.
    """

    if Path(request.path).name not in T1_WORK_INVENTORY_FILES:
        yield
        return
    aside = tmp_path_factory.mktemp("g1_t1_isolation")
    with hide_g1_work_files(REPO_ROOT, aside):
        yield


@pytest.fixture
def make_unit():
    def factory(number: int = 0, text: str = "Exact English source") -> dict[str, Any]:
        return {
            "unit_id": f"S4A-2026-{number:03d}",
            "section": "test",
            "source_text_en": text,
            "source_text_sha256": sha256_text(text),
            "source_location": {"test": True},
            "source_style": "Normal",
            "translation_status": "UNTRANSLATED",
            "target_fi": "",
            "requires_human_signoff": True,
        }
    return factory


@pytest.fixture
def write_jsonl():
    def writer(path: Path, records: list[dict[str, Any]]) -> Path:
        path.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        return path
    return writer


@pytest.fixture
def make_candidate():
    def factory(unit: dict[str, Any], **overrides: Any) -> dict[str, Any]:
        value = {
            "unit_id": unit["unit_id"],
            "source_text_sha256": unit["source_text_sha256"],
            "model": "manual-test-session",
            "candidate_fi": "test candidate",
            "decision_note": "Fixture only.",
            "issues": [],
            "status": "DRAFT",
        }
        value.update(overrides)
        return value
    return factory
