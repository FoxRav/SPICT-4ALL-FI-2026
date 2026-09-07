"""Rebuild deterministic terminology evidence, conflicts, mapping, and report."""

from __future__ import annotations

from pathlib import Path

from spict4all.terminology import (
    build_relevance_rows,
    derive_conflicts,
    extract_terminology,
    load_glossary,
    render_terminology_report,
    serialize_conflicts,
    serialize_extracted_terms,
    serialize_relevance_rows,
    validate_extracted_terms,
    validate_glossary,
    verify_terminology_sources,
)
from spict4all.units import load_source_units


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    sources = verify_terminology_sources(
        repository,
        repository / "terminology/sources/terminology_source_manifest.json",
        repository / "schemas/terminology_source_manifest.schema.json",
    )
    records = extract_terminology(
        repository,
        sources,
        repository / "terminology/sources/pdf_extraction_rules.json",
        repository / "schemas/terminology_pdf_extraction_rule.schema.json",
    )
    validate_extracted_terms(
        records, repository / "schemas/terminology_extracted_entry.schema.json"
    )
    conflicts = derive_conflicts(records)
    glossary_rows = load_glossary(repository / "terminology/terms.csv")
    approved = validate_glossary(glossary_rows)
    relevance = build_relevance_rows(
        load_source_units(repository / "data/source_units.jsonl"),
        records,
        conflicts,
    )

    outputs = {
        repository
        / "terminology/extracted/terminology_evidence.jsonl": serialize_extracted_terms(
            records
        ),
        repository
        / "terminology/conflicts/terminology_conflicts.jsonl": serialize_conflicts(
            conflicts
        ),
        repository
        / "terminology/reports/source_unit_terminology_map.tsv": serialize_relevance_rows(
            relevance
        ),
        repository
        / "terminology/reports/TERMINOLOGY_EVIDENCE_REPORT.md": render_terminology_report(
            sources,
            records,
            conflicts,
            glossary_rows,
            len(approved),
            len(relevance),
        ),
    }
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
