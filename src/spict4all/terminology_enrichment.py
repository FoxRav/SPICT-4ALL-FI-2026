"""Read-only authority boundary and reproducible T1.1 review artifacts."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .adjudication import BASE, read_json, read_tsv, tsv_text, validate_package
from .errors import IntegrityError
from .human_terminology_decisions import HUMAN_FILE, historical_human_bytes
from .jsonl import load_jsonl

ENRICHMENT = f"{BASE}/enrichment"
EVIDENCE = "TERM-SRC-006-terveyskirjasto-evidence.jsonl"
QUEUE = "T1_1_UPDATED_ADJUDICATION_QUEUE.tsv"
EXTRA = ["terveyskirjasto_evidence_ids", "terveyskirjasto_terms",
         "terveyskirjasto_evidence_status", "evidence_after_enrichment",
         "remaining_uncertainty"]


def valid_url(value: str) -> bool:
    url = urlsplit(value)
    return (url.scheme == "https" and url.hostname == "www.terveyskirjasto.fi"
            and url.username is None and url.password is None and url.port is None)


def counts(root: Path) -> dict[str, Any]:
    plan = read_json(root / ENRICHMENT / "model_interpretations.json")
    rows = plan["decisions"]
    original = read_tsv(root / BASE / "TERMINOLOGY_ADJUDICATION_QUEUE.tsv")
    baseline = [dict(zip(original[0], row, strict=True)) for row in original[1:]]
    new = {row["decision_id"]: row for row in rows}
    lacking = [row["decision_id"] for row in baseline
               if row["candidate_origin"] == "NO_RELIABLE_TERMINOLOGY_EVIDENCE"
               and new[row["decision_id"]]["coverage"] != "CORE_TERM_SUPPORTED"]
    evidence = load_jsonl(root / ENRICHMENT / EVIDENCE)
    searches = load_jsonl(root / ENRICHMENT / "search_receipts.jsonl")
    pages = load_jsonl(root / ENRICHMENT / "page_receipts.jsonl")
    return {
        "concepts_searched": len({x["decision_id"] for x in searches}),
        "search_attempts": len(searches),
        "unique_search_results_screened": len({u["url"] for x in searches for u in x["results"]}),
        "unique_pages_scraped": len({x["url"] for x in pages}),
        "useful_evidence_records": len(evidence),
        "concepts_enriched": sum(bool(x["evidence_ids"]) for x in rows),
        "no_sufficient_evidence_before": 16,
        "no_sufficient_evidence_after": len(lacking),
        "still_insufficient_ids": lacking,
        "original_no_evidence_now_with_zero_useful_evidence": sum(
            not new[x["decision_id"]]["evidence_ids"] for x in baseline
            if x["candidate_origin"] == "NO_RELIABLE_TERMINOLOGY_EVIDENCE"),
        "high_risk_enriched": sum(bool(new[x["decision_id"]]["evidence_ids"])
                                  for x in baseline if x["clinical_risk"] == "HIGH"),
        "must_review_with_sami": sum(x["must_review_with_sami"] for x in rows),
        "external_human_review_required": 29,
        "new_scope_conflicts": len(plan["new_scope_conflicts"]),
        "original_conflicts_resolved": 0,
        "approved": 0,
    }


def build_table(root: Path) -> list[list[str]]:
    table = read_tsv(root / BASE / "TERMINOLOGY_ADJUDICATION_QUEUE.tsv")
    plan = read_json(root / ENRICHMENT / "model_interpretations.json")
    interpretations = {x["decision_id"]: x for x in plan["decisions"]}
    evidence = {x["evidence_id"]: x for x in load_jsonl(root / ENRICHMENT / EVIDENCE)}
    result = [table[0] + EXTRA]
    for row in table[1:]:
        item = interpretations[row[0]]
        terms = list(dict.fromkeys(evidence[x]["source_evidence"]["headword_fi"]
                                  for x in item["evidence_ids"]))
        result.append(row + [";".join(item["evidence_ids"]), ";".join(terms),
                             item["coverage"], item["after_status"], item["uncertainty"]])
    return result


def human_review(root: Path) -> str:
    table = build_table(root)
    plan = read_json(root / ENRICHMENT / "model_interpretations.json")
    interpretations = {x["decision_id"]: x for x in plan["decisions"]}
    evidence = {x["evidence_id"]: x for x in load_jsonl(root / ENRICHMENT / EVIDENCE)}
    out = ["# T1.1 terminology human review", "",
           "Evidence collection only. APPROVED = 0. No SPICT translation produced.",
           "All Finnish terms below are source headwords or tentative model mappings, not accepted translations.",
           "The original human decision file remains unchanged. No choice is preselected.", ""]
    for values in table[1:]:
        row = dict(zip(table[0], values, strict=True))
        item = interpretations[row["decision_id"]]
        out += [f"## {row['decision_id']} — {row['concept_en']}", "", "### SOURCE EVIDENCE", "",
                "Exact SPICT context (unchanged; requirement text is not canonical authority):", "",
                "```text", row["exact_spict_context_en"], "```", "",
                f"Source unit IDs: {row['source_unit_ids']}", "",
                f"Existing evidence IDs: {row['terminology_evidence_ids'] or 'None'}", "",
                row["source_evidence_summary"], "", "Terveyskirjasto:", ""]
        for ref in item["evidence_ids"]:
            source = evidence[ref]["source_evidence"]
            out += [f"- {ref}: [{source['page_title']}]({source['url']}); "
                    f"headword/usage: **{source['headword_fi']}**; {source['locator']}; "
                    f"accessed {source['accessed_at_utc']}", "",
                    "> " + source["fragment"].replace("\n", "\n> "), ""]
        if not item["evidence_ids"]:
            out += ["No useful source fragment retained from the targeted searches.", ""]
        out += ["### MODEL INTERPRETATION", "", row["model_semantic_mapping_note"], "",
                "MODEL_SEMANTIC_MAPPING: " + item["uncertainty"], "",
                f"Original tentative candidates: {row['candidate_fi'] or 'None'}", "",
                f"Original alternatives: {row['alternative_fi'] or 'None'}", "",
                f"New source terms for comparison only: {row['terveyskirjasto_terms'] or 'None'}", "",
                f"Coverage: {item['coverage']}. Original conflicts: {row['conflict_status']}", "",
                f"Clinical risk: {row['clinical_risk']}; plain-language risk: {row['plain_language_risk']}.", "",
                "### HUMAN DECISION", "", "- [ ] Accept a term after reviewing context", "- [ ] Modify / propose another term",
                "- [ ] Reject proposed equivalence", "- [ ] Request external/domain evidence", "",
                "Final term: __________  Decision note: __________  Reviewer/date: __________", ""]
    return "\n".join(out)


def validate_enrichment(root: Path) -> dict[str, Any]:
    lock = read_json(root / ENRICHMENT / "T1_1_input_integrity.json")
    corrections = read_json(root / ENRICHMENT / "T1_1_integrity_path_corrections.json")["path_corrections"]
    original_lock = read_json(root / BASE / "input_integrity.json")["protected_files"]
    for name, digest in lock["protected_files"].items():
        resolved = corrections.get(name, name)
        if resolved != name and original_lock.get(resolved) != digest:
            raise IntegrityError("Invalid input path correction")
        path = root / resolved
        content = historical_human_bytes(root) if resolved == HUMAN_FILE else path.read_bytes() if path.is_file() else b""
        if not path.is_file() or hashlib.sha256(content).hexdigest() != digest:
            raise IntegrityError(f"T1.1 protected input changed: {name}")
    validate_package(root)  # includes source hashes, blank decisions, glossary and work inventory
    table = read_tsv(root / BASE / "TERMINOLOGY_ADJUDICATION_QUEUE.tsv")
    baseline = {x[0]: dict(zip(table[0], x, strict=True)) for x in table[1:]}
    registry = read_json(root / ENRICHMENT / "web_source_manifest.json")
    if (registry["source_id"] != "TERM-SRC-006"
            or registry["classification"] != "TERMINOLOGY_REFERENCE"
            or registry["evidence_type"] != "WEB_TERMINOLOGY_REFERENCE"
            or registry["can_satisfy_spict_source_requirements"] is not False
            or registry["retrieval_method"] != "FIRECRAWL"):
        raise IntegrityError("Web reference cannot satisfy SPICT source authority")
    if not valid_url(registry["root_url"]):
        raise IntegrityError("Invalid reference domain")
    plan = read_json(root / ENRICHMENT / "model_interpretations.json")
    rows = plan["decisions"]
    if (Counter(x["decision_id"] for x in rows) != Counter(baseline.keys())
            or plan["type"] != "MODEL_SEMANTIC_MAPPING" or plan["approved"] != 0):
        raise IntegrityError("Invalid model decisions or approval")
    evidence = load_jsonl(root / ENRICHMENT / EVIDENCE)
    ids = [x["evidence_id"] for x in evidence]
    if len(ids) != len(set(ids)):
        raise IntegrityError("Duplicate evidence ID")
    for record in evidence:
        if set(record) != {"evidence_id", "decision_id", "concept_en", "source_id",
                           "source_evidence", "model_interpretation"}:
            raise IntegrityError("Unexpected evidence fields; source/model boundary")
        decision = record["decision_id"]
        if decision not in baseline or record["concept_en"] != baseline[decision]["concept_en"]:
            raise IntegrityError("Unknown decision reference or altered English concept")
        source, model = record["source_evidence"], record["model_interpretation"]
        if (record["source_id"] != "TERM-SRC-006" or not valid_url(source["url"])
                or source["retrieval_method"] != "FIRECRAWL"):
            raise IntegrityError("Invalid evidence source/domain")
        if set(source) != {"page_title", "url", "accessed_at_utc", "headword_fi", "fragment",
                          "article_id", "locator", "article_date", "retrieval_method",
                          "retrieval_metadata", "cache_path", "cache_sha256", "fragment_sha256"}:
            raise IntegrityError("Source/model separation violated")
        if (not source["fragment"] or len(source["fragment"].split()) > 25
                or hashlib.sha256(source["fragment"].encode()).hexdigest() != source["fragment_sha256"]):
            raise IntegrityError("Invalid short source fragment/hash")
        if (set(model) != {"relationship", "relevance_note", "confidence", "coverage"}
                or model["relationship"] != "MODEL_SEMANTIC_MAPPING"):
            raise IntegrityError("Source/model separation violated")
        cache = root / source["cache_path"]
        if cache.exists():
            raw = read_json(cache)
            if hashlib.sha256(cache.read_bytes()).hexdigest() != source["cache_sha256"]:
                raise IntegrityError("Retrieval cache hash mismatch")
            content = raw["markdown"] if source["locator"] == "markdown article fragment" else raw["metadata"]["description"]
            if source["fragment"] not in content:
                raise IntegrityError("Quote absent from Firecrawl response")
    by_id = {x["evidence_id"]: x for x in evidence}
    for row in rows:
        if set(row) != {"decision_id", "evidence_ids", "coverage", "after_status", "uncertainty", "must_review_with_sami"}:
            raise IntegrityError("Model rows cannot populate human decisions")
        expected = [x["evidence_id"] for x in evidence if x["decision_id"] == row["decision_id"]]
        if row["evidence_ids"] != expected or not set(row["evidence_ids"]) <= by_id.keys():
            raise IntegrityError("Missing or invalid evidence links")
        if row["coverage"] not in {"CORE_TERM_SUPPORTED", "PARTIAL_OR_CONTEXTUAL", "NO_USEFUL_EVIDENCE"}:
            raise IntegrityError("Unknown evidence coverage")
        if bool(expected) != (row["coverage"] != "NO_USEFUL_EVIDENCE"):
            raise IntegrityError("Coverage without evidence")
    searches = load_jsonl(root / ENRICHMENT / "search_receipts.jsonl")
    if {x["decision_id"] for x in searches if x["exit_code"] == 0} != set(baseline):
        raise IntegrityError("Missing successful targeted search for a concept")
    actual = (root / ENRICHMENT / QUEUE).read_text(encoding="utf-8")
    if actual != tsv_text(build_table(root)):
        raise IntegrityError("Updated queue mismatch; original/human fields must stay unchanged")
    if (root / ENRICHMENT / "TERMINOLOGY_HUMAN_REVIEW_T1_1.md").read_text(encoding="utf-8") != human_review(root):
        raise IntegrityError("Human review mismatch or preselected choice")
    return counts(root)
