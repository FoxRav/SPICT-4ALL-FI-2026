"""Build review documents and table payload; never overwrite differing artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from spict4all.adjudication import (
    BASE,
    build_tables,
    mapping_records,
    read_json,
    render_human_review,
    render_report,
    screening_records,
    verify_input_integrity,
)
from spict4all.jsonl import load_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-payload", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    verify_input_integrity(root)
    plan = read_json(root / BASE / "model_mapping_plan.json")
    tables = build_tables(root, plan)
    evidence = load_jsonl(root / "terminology/extracted/terminology_evidence.jsonl")
    outputs = {
        "TERMINOLOGY_HUMAN_REVIEW.md": render_human_review(root, plan),
        "T1_TERMINOLOGY_ADJUDICATION_REPORT.md": render_report(plan),
        "terminology_adjudication_evidence.jsonl": "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in mapping_records(root, plan)),
        "source_screening.jsonl": "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in screening_records(root, plan)),
        "semantic_search_scope.json": json.dumps({
            "search_method": "MODEL_SEMANTIC_MAPPING",
            "searched_entry_ids": sorted(row["entry_id"] for row in evidence),
            "decision_ids": [row["decision_id"] for row in plan["decisions"]],
            "scope_note": "Each decision was considered against the full registered 136-entry set, including Finnish definitions and context. Retained edges are model proposals, not source-provided bilingual assertions.",
        }, ensure_ascii=False, indent=2) + "\n",
    }
    for name, text in outputs.items():
        path = root / BASE / name
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"Refusing to overwrite differing preparation artifact: {path}")
    for name, text in outputs.items():
        path = root / BASE / name
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    args.table_payload.write_text(json.dumps(tables, ensure_ascii=False), encoding="utf-8")
    verify_input_integrity(root)
    print(f"Built {len(plan['decisions'])} human-review decisions; no approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
