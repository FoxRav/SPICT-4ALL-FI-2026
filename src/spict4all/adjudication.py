"""T1 preparation only: source evidence, model mapping, and blank human decisions."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .human_terminology_decisions import HUMAN_FILE, historical_human_bytes, parse
from .jsonl import load_jsonl
from .terminology import load_glossary, validate_glossary

BASE = "terminology/adjudication"
QUEUE_FIELDS = (
    "decision_id", "concept_en", "exact_spict_context_en", "source_unit_ids",
    "clinical_risk", "plain_language_risk", "candidate_fi", "candidate_origin",
    "terminology_evidence_ids", "terminology_source_ids", "source_evidence_summary",
    "model_semantic_mapping_note", "conflict_status", "alternative_fi",
    "recommended_for_human_review", "human_decision", "human_decision_note",
    "decided_by", "decision_date",
)
HUMAN_FIELDS = (
    "decision_id", "human_decision", "final_finnish_term", "human_decision_note",
    "decided_by", "decision_date",
)
ORIGINS = {
    "SOURCE_EXPLICIT", "SOURCE_DERIVED_FINNISH_ONLY",
    "MODEL_PROPOSED_FROM_EVIDENCE", "NO_RELIABLE_TERMINOLOGY_EVIDENCE",
}
PRIORITIES = {
    "MUST_DECIDE_BEFORE_G1", "MAY_REMAIN_UNCONTROLLED_FOR_INDEPENDENT_AB",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_index(root: Path) -> dict[str, dict[str, Any]]:
    records = load_jsonl(root / "data/source_units.jsonl")
    for requirement in load_jsonl(root / "data/source_requirements.jsonl"):
        if requirement["translation_evidence_required"]:
            records.append({
                "unit_id": requirement["requirement_id"],
                "source_text_en": requirement["exact_source_text_en"],
                "source_text_sha256": requirement["exact_text_sha256"],
            })
    return {row["unit_id"]: row for row in records}


def verify_input_integrity(root: Path) -> None:
    lock = read_json(root / BASE / "input_integrity.json")
    for relative, expected in lock["protected_files"].items():
        path = root / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise IntegrityError(f"T1 protected input changed: {relative}")
    work = sorted(path.relative_to(root).as_posix() for path in (root / "work").rglob("*")
                  if path.is_file())
    if work != sorted(lock["work_files"]):
        raise IntegrityError("T1 preparation must not create translation work artifacts")
    if validate_glossary(load_glossary(root / "terminology/terms.csv")):
        raise IntegrityError("T1 preparation must not introduce APPROVED terminology")


def validate_plan(root: Path, plan: dict[str, Any]) -> None:
    sources = source_index(root)
    evidence = {row["entry_id"]: row for row in load_jsonl(
        root / "terminology/extracted/terminology_evidence.jsonl")}
    conflicts = {row["conflict_id"]: row for row in load_jsonl(
        root / "terminology/conflicts/terminology_conflicts.jsonl")}
    if plan.get("analysis_type") != "MODEL_SEMANTIC_MAPPING" or plan.get("approval_count") != 0:
        raise IntegrityError("T1 must remain model analysis without approval")
    rows = plan["decisions"]
    ids = [row["decision_id"] for row in rows]
    if len(ids) != len(set(ids)) or ids != [f"T-{n:03}" for n in range(1, len(ids) + 1)]:
        raise IntegrityError("T1 duplicate or unstable decision IDs")
    for row in rows:
        label = row["decision_id"]
        if any(row.get(field, "") != "" for field in HUMAN_FIELDS[1:]):
            raise IntegrityError(f"{label}: human fields must be blank")
        if row.get("status") == "APPROVED":
            raise IntegrityError(f"{label}: no APPROVED terminology in T1")
        if not row["source_unit_ids"] or not set(row["source_unit_ids"]) <= sources.keys():
            raise IntegrityError(f"{label}: unknown source_unit_id")
        refs = row["terminology_evidence_ids"]
        if len(refs) != len(set(refs)) or not set(refs) <= evidence.keys():
            raise IntegrityError(f"{label}: unknown or duplicate evidence reference")
        if row["candidate_origin"] not in ORIGINS:
            raise IntegrityError(f"{label}: candidate origin must be explicit")
        if not row["model_semantic_mapping_note"].startswith("MODEL_SEMANTIC_MAPPING: "):
            raise IntegrityError(f"{label}: model mapping label required")
        if row["clinical_risk"] not in {"HIGH", "MEDIUM", "LOW"} or row["plain_language_risk"] not in {"HIGH", "MEDIUM", "LOW"}:
            raise IntegrityError(f"{label}: invalid risk")
        if row["recommended_for_human_review"] not in PRIORITIES:
            raise IntegrityError(f"{label}: invalid review priority")
        origin = row["candidate_origin"]
        candidate = row["candidate_fi"]
        if origin == "NO_RELIABLE_TERMINOLOGY_EVIDENCE":
            if candidate or refs or row["alternative_fi"]:
                raise IntegrityError(f"{label}: no-evidence item must not invent a candidate")
        elif not refs or not candidate.strip():
            raise IntegrityError(f"{label}: candidate requires traceable evidence")
        if origin == "SOURCE_EXPLICIT":
            if not any(evidence[ref]["term_en_origin"] == "SOURCE_EXPLICIT"
                       and evidence[ref]["term_en"] == row["concept_en"]
                       and evidence[ref]["term_fi"] == candidate for ref in refs):
                raise IntegrityError(f"{label}: inferred English equivalent cannot be SOURCE_EXPLICIT")
        if origin == "SOURCE_DERIVED_FINNISH_ONLY":
            if not any(evidence[ref]["term_en_origin"] == "NOT_PROVIDED"
                       and (candidate == evidence[ref]["term_fi"] or candidate in
                            [part.strip() for part in (evidence[ref]["definition"] or "").split(",")])
                       for ref in refs):
                raise IntegrityError(f"{label}: Finnish-only candidate not in exact source wording")
        for conflict_id in row["conflict_ids"]:
            if conflict_id not in conflicts or not set(conflicts[conflict_id]["source_entry_ids"]) <= set(refs):
                raise IntegrityError(f"{label}: conflict evidence sides must be retained")
    reviews = plan["conflict_review"]
    if len(reviews) != len(conflicts) or {row["conflict_id"] for row in reviews} != set(conflicts):
        raise IntegrityError("T1 must account for all existing conflicts")
    for review in reviews:
        linked = [row["decision_id"] for row in rows if review["conflict_id"] in row["conflict_ids"]]
        if review["decision_ids"] != linked or review["relevance"] != ("RELEVANT" if linked else "NOT_INCLUDED"):
            raise IntegrityError("T1 conflict relevance and queue disagree")
        if review["resolution"] != "" or review["source_conflict_status"] != "HUMAN_REVIEW_REQUIRED":
            raise IntegrityError("T1 conflicts must not be resolved")
        if not review["model_relevance_note"].startswith("MODEL_SEMANTIC_MAPPING: "):
            raise IntegrityError("T1 conflict exclusion needs explicit model reasoning")


def build_tables(root: Path, plan: dict[str, Any]) -> dict[str, list[list[str]]]:
    validate_plan(root, plan)
    sources = source_index(root)
    evidence = {row["entry_id"]: row for row in load_jsonl(
        root / "terminology/extracted/terminology_evidence.jsonl")}
    queue = [list(QUEUE_FIELDS)]
    human = [list(HUMAN_FIELDS)]
    for row in plan["decisions"]:
        record = dict(row)
        record["source_unit_ids"] = "|".join(row["source_unit_ids"])
        record["exact_spict_context_en"] = "\n\n".join(
            sources[unit_id]["source_text_en"] for unit_id in row["source_unit_ids"])
        record["terminology_evidence_ids"] = "|".join(row["terminology_evidence_ids"])
        record["terminology_source_ids"] = "|".join(sorted({evidence[ref]["source_id"] for ref in row["terminology_evidence_ids"]}))
        record["source_evidence_summary"] = " | ".join(
            f"{ref}: {evidence[ref]['term_fi']}; English={evidence[ref]['term_en_origin']}; "
            f"definition={'present' if evidence[ref]['definition'] else 'NOT_PROVIDED'}"
            for ref in row["terminology_evidence_ids"]) or "No reliable correspondence found in the 136-entry set."
        record["conflict_status"] = (
            "UNRESOLVED:" + "|".join(row["conflict_ids"]) if row["conflict_ids"]
            else "NO_REGISTERED_CONFLICT_LINKED; MODEL_MAPPING_UNADJUDICATED")
        queue.append([str(record.get(field, "")) for field in QUEUE_FIELDS])
        human.append([row["decision_id"], "", "", "", "", ""])
    return {"TERMINOLOGY_ADJUDICATION_QUEUE.tsv": queue,
            "human_terminology_decisions.tsv": human}


def counts(plan: dict[str, Any]) -> dict[str, Any]:
    rows = plan["decisions"]
    return {
        "concepts": len(rows), "clinical_risk": dict(Counter(row["clinical_risk"] for row in rows)),
        "candidate_origins": {origin: sum(row["candidate_origin"] == origin for row in rows) for origin in sorted(ORIGINS)},
        "semantic_connections": sum(bool(row["terminology_evidence_ids"]) for row in rows),
        "mapping_edges": sum(len(row["terminology_evidence_ids"]) for row in rows),
        "relevant_conflicts": sum(row["relevance"] == "RELEVANT" for row in plan["conflict_review"]),
        "must_decide": sum(row["recommended_for_human_review"] == "MUST_DECIDE_BEFORE_G1" for row in rows),
        "approved": 0,
    }


def read_tsv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.reader(stream, delimiter="\t"))


def validate_package(root: Path) -> dict[str, Any]:
    verify_input_integrity(root)
    plan = read_json(root / BASE / "model_mapping_plan.json")
    expected = build_tables(root, plan)
    for filename, table in expected.items():
        actual = (parse(historical_human_bytes(root)) if f"{BASE}/{filename}" == HUMAN_FILE
                  else read_tsv(root / BASE / filename))
        if actual != table:
            raise IntegrityError(f"T1 {filename}: source context, evidence, origin or blank decision mismatch")
    evidence = {row["entry_id"]: row for row in load_jsonl(
        root / "terminology/extracted/terminology_evidence.jsonl")}
    mappings = load_jsonl(root / BASE / "terminology_adjudication_evidence.jsonl")
    expected_mappings = mapping_records(root, plan)
    if mappings != expected_mappings:
        raise IntegrityError("T1 mapping provenance or exact evidence differs from registered source")
    inventory = read_json(root / BASE / "semantic_search_scope.json")
    if inventory["searched_entry_ids"] != sorted(evidence) or inventory["search_method"] != "MODEL_SEMANTIC_MAPPING":
        raise IntegrityError("T1 semantic search must cover all 136 registered entries")
    if load_jsonl(root / BASE / "source_screening.jsonl") != screening_records(root, plan):
        raise IntegrityError("T1 screening must cover all 54 translation-evidence sources")
    document = (root / BASE / "TERMINOLOGY_HUMAN_REVIEW.md").read_text(encoding="utf-8")
    if document != render_human_review(root, plan) or "[x]" in document.lower():
        raise IntegrityError("T1 human review must retain exact evidence and unselected choices")
    if (root / BASE / "T1_TERMINOLOGY_ADJUDICATION_REPORT.md").read_text(encoding="utf-8") != render_report(plan):
        raise IntegrityError("T1 report counts or conflict disposition differ from model plan")
    return counts(plan)


def mapping_records(root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = {row["entry_id"]: row for row in load_jsonl(
        root / "terminology/extracted/terminology_evidence.jsonl")}
    sources = source_index(root)
    return [{
        "decision_id": row["decision_id"], "mapping_type": "MODEL_SEMANTIC_MAPPING",
        "concept_en": row["concept_en"], "candidate_origin": row["candidate_origin"],
        "source_unit_hashes": {unit_id: sources[unit_id]["source_text_sha256"] for unit_id in row["source_unit_ids"]},
        "source_provided_evidence": evidence[ref],
        "model_explanation": row["model_semantic_mapping_note"],
        "human_decision": "",
    } for row in plan["decisions"] for ref in row["terminology_evidence_ids"]]


def screening_records(root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for unit_id, unit in source_index(root).items():
        links = [row["decision_id"] for row in plan["decisions"] if unit_id in row["source_unit_ids"]]
        records.append({"unit_id": unit_id, "source_text_en": unit["source_text_en"],
                        "source_text_sha256": unit["source_text_sha256"], "decision_ids": links,
                        "screening_type": "MODEL_SEMANTIC_MAPPING",
                        "note": "Terminology-sensitive scope is covered by the linked decisions." if links else
                        "No additional controlled project term proposed: preserve this heading, identifier or concrete plain-language observation in independent translation. Do not replace observations with inferred diagnoses. This is a model screening judgment, not clinical approval."})
    return records


def quote(text: str | None) -> str:
    if text is None:
        return "NOT_PROVIDED in the extracted evidence."
    return "\n".join("> " + line for line in text.split("\n"))


def render_human_review(root: Path, plan: dict[str, Any]) -> str:
    evidence = {row["entry_id"]: row for row in load_jsonl(
        root / "terminology/extracted/terminology_evidence.jsonl")}
    sources = source_index(root)
    lines = ["# SPICT-4ALL FI — Terminology human review", "",
             "NO TERMINOLOGY DECISION HAS BEEN APPROVED BY THIS RUN", "",
             "This is a terminology decision queue, not a Finnish SPICT translation. English source text defines meaning. Source quotations below are distinct from MODEL INTERPRETATION. Null definitions/context are explicitly marked, never completed by the model.", "",
             "Five scope decisions are proposed for human disposition before G1. The human team may ACCEPT, REVISE, LEAVE UNCONTROLLED or require CLINICAL REVIEW. These priorities are model recommendations and do not change the executable quality gates. No candidate is mandatory for A/B. Only a later attributable human project approval can enter the approved glossary.", "",
             "Read the exact provenance in each item. Source text containing legal or clinical statements is a quotation from the registered, sometimes undated material, not a claim that this run verified current law or clinical guidance. English labels are retained literally. Alternatives marked for contrast are not interchangeable recommendations.", "",
             "Fill human_terminology_decisions.tsv after review. ACCEPT here is a human response, not automatic glossary promotion. Neither this package nor a completed form resolves the title/liver source-authority conflicts.", ""]
    for row in plan["decisions"]:
        lines += [f"### {row['decision_id']} — {row['concept_en']}", "", "SPICT source context:", ""]
        for unit_id in row["source_unit_ids"]:
            lines += [f"**{unit_id}** — source SHA-256 `{sources[unit_id]['source_text_sha256']}`", "",
                      quote(sources[unit_id]["source_text_en"]), ""]
        lines += ["Candidate Finnish wording:", "", row["candidate_fi"] or "No candidate proposed: insufficient reliable terminology evidence.", "",
                  f"Candidate origin: `{row['candidate_origin']}`", "", "Alternative(s):", "",
                  row["alternative_fi"] or "None proposed by this run.", "", "Evidence:", ""]
        for ref in row["terminology_evidence_ids"]:
            entry = evidence[ref]
            lines += [f"**{ref} / {entry['source_id']}**", "",
                      f"Source: `{entry['source_filename']}`", "",
                      f"SHA-256: `{entry['source_sha256']}`; location: `{json.dumps(entry['source_location'], ensure_ascii=False)}`", "",
                      "Exact Finnish source term:", "", quote(entry["term_fi"]), "",
                      f"English label origin: `{entry['term_en_origin']}`", "", quote(entry["term_en"]), "",
                      "Exact source definition:", "", quote(entry["definition"]), "",
                      "Exact source context:", "", quote(entry["context"]), "",
                      "Exact extraction fragment:", "", quote(entry["source_fragment"]), ""]
        if not row["terminology_evidence_ids"]:
            lines += ["The entire 136-entry set was searched. No reliable correspondence was retained. This does not claim the concept is absent from every page of the original references or all Finnish terminology.", ""]
        lines += ["Model interpretation — **MODEL INTERPRETATION**:", "", row["model_semantic_mapping_note"], "",
                  "Existing conflicts: " + (", ".join(row["conflict_ids"]) + " — UNRESOLVED, both source records retained." if row["conflict_ids"] else "No registered conflict linked; the proposed mapping remains unadjudicated."), "",
                  f"Risk: **{row['clinical_risk']}** clinical; **{row['plain_language_risk']}** plain language.", "",
                  f"Review priority (model recommendation): `{row['recommended_for_human_review']}`", "",
                  "Human decision:", "", "- [ ] ACCEPT", "- [ ] REVISE", "- [ ] LEAVE UNCONTROLLED", "- [ ] CLINICAL REVIEW REQUIRED", "",
                  "Final Finnish term:", "____________________", "", "Decision note:", "____________________", "",
                  "Decided by / decision date:", "____________________", ""]
    return "\n".join(lines)


def tsv_text(table: list[list[str]]) -> str:
    """Reference serializer for tests; delivered TSVs are authored with Artifact Tool."""
    output = io.StringIO(newline="")
    csv.writer(output, delimiter="\t", lineterminator="\n").writerows(table)
    return output.getvalue()


def render_report(plan: dict[str, Any]) -> str:
    summary = counts(plan)
    risks = summary["clinical_risk"]
    origins = summary["candidate_origins"]
    lines = ["# T1 terminology adjudication preparation", "",
             "Work package: WP-T1-TERMINOLOGY-ADJUDICATION-PREP-001", "",
             "NO TERMINOLOGY DECISION HAS BEEN APPROVED BY THIS RUN", "",
             "## Scope and counts", "",
             "Inspected all 54 translation-evidence sources: 53 canonical units and S4A-REQ-2026-001. The canonical title and liver requirement retain their separate unresolved source-authority states. Source text and hashes are preserved in source_screening.jsonl and input_integrity.json.", "",
             "All 136 extracted entries from 5 registered references were semantically considered, including 41 entries with explicit English labels and 95 without. semantic_search_scope.json records the entire search inventory. This was model analysis of the extracted evidence; no new translation, clinical validation, source extraction, or external literature search was performed.", "",
             f"- Terminology-sensitive decision concepts found / queue count: {summary['concepts']} / {summary['concepts']}.",
             f"- Clinical risks: HIGH {risks.get('HIGH', 0)}, MEDIUM {risks.get('MEDIUM', 0)}, LOW {risks.get('LOW', 0)}.",
             f"- Direct source-provided English/Finnish relationship for the SPICT concept (SOURCE_EXPLICIT): {origins['SOURCE_EXPLICIT']}.",
             f"- Finnish-only candidate wording with model correspondence (SOURCE_DERIVED_FINNISH_ONLY): {origins['SOURCE_DERIVED_FINNISH_ONLY']}.",
             f"- Model-proposed wording or transferred relationship from evidence (MODEL_PROPOSED_FROM_EVIDENCE): {origins['MODEL_PROPOSED_FROM_EVIDENCE']}.",
             f"- No reliable correspondence in the extracted set (NO_RELIABLE_TERMINOLOGY_EVIDENCE): {origins['NO_RELIABLE_TERMINOLOGY_EVIDENCE']}.",
             f"- Concepts with a retained MODEL_SEMANTIC_MAPPING connection: {summary['semantic_connections']} ({summary['mapping_edges']} evidence edges). This overlaps Finnish-only and model-proposed counts; it is not an additional mutually exclusive category.",
             f"- Relevant existing conflicts: {summary['relevant_conflicts']}; not included: {6-summary['relevant_conflicts']}.",
             "- APPROVED project terminology: 0. Conservative exact-English relevance matches remain 0.", "",
             "A term appearing in Finnish is not proof of an English/Finnish pair. In particular, source-explicit advance care planning is preserved literally; using its Finnish wording for SPICT care plans is a model transfer. Patient and healthcare client labels do not establish an equivalent for person. No direct pair was manufactured to raise the direct-evidence count.", "",
             "No-evidence candidates and alternatives are blank, not model guesses. No-evidence means no reliable correspondence among these 136 extracted records, not absence from all Finnish terminology or every page of the original PDFs. The source terms Dyspnea and Inoperaabeli remain visible alongside the exact Finnish definitions from which the proposed plain wording is taken.", "",
             "## MUST DECIDE BEFORE G1", "",
             f"{summary['must_decide']} proposed human scope dispositions:", ""]
    for row in plan["decisions"]:
        if row["recommended_for_human_review"] == "MUST_DECIDE_BEFORE_G1":
            lines.append(f"- {row['decision_id']} — {row['concept_en']}: see the exact evidence, limitations and alternatives in the human review document.")
    lines += ["", "These five priorities address repeated scope, agency and role risks. A human disposition may explicitly LEAVE UNCONTROLLED or require further clinical review; it need not approve a single Finnish wording. They are preparation recommendations, not a new executable gate or evidence that G1 has been released. No decision has been made by this run.", "",
              "## MAY REMAIN UNCONTROLLED FOR INDEPENDENT A/B TRANSLATION", "",
              "The remaining concepts may remain uncontrolled while A/B independently produce evidence from the English source. High clinical risk still requires later careful review and per-unit human sign-off; it does not by itself justify forcing unapproved terminology into the independent inputs.", ""]
    for row in plan["decisions"]:
        if row["recommended_for_human_review"] != "MUST_DECIDE_BEFORE_G1":
            lines.append(f"- {row['decision_id']} — {row['concept_en']}")
    lines += ["", "## All six existing conflicts", "",
              "The existing conflict ledger remains unchanged and HUMAN_REVIEW_REQUIRED. NOT_INCLUDED below is a model relevance assessment, not a resolution. Some pairs appear to differ in link markup; that observation does not authorize this run to resolve them.", ""]
    for review in plan["conflict_review"]:
        lines += [f"- {review['conflict_id']} — {review['relevance']}; decisions: {', '.join(review['decision_ids']) or 'none'}. {review['model_relevance_note']} Status remains HUMAN_REVIEW_REQUIRED; resolution blank."]
    lines += ["", "## Screening and evidence limits", "",
              "The 29 decisions group closely related source occurrences, not all individual words. source_screening.jsonl contains a row for every inspected unit, including headings and observations without an added control. Ordinary cancer/kidney/liver headings, weight change, oxygen use, infections, and the version identifier receive no invented terminology requirement. Concrete liver observations remain plain observations rather than inferred diagnoses. Power of Attorney is absent from these 54 sources and was not imported from the older glossary's guidance-only item.", "",
              "Review risks and semantic correspondence are model assessments. The quoted original metadata/definitions may be incomplete or dated; human reviewers must assess currency and clinical applicability. This run supplies no treatment advice and no clinical validation.", "",
              "## Files and reproducibility", "",
              "- TERMINOLOGY_ADJUDICATION_QUEUE.tsv: 19 requested columns, one row per decision. Pipe-separated IDs; quoted multiline cells preserve the complete English source text in listed-ID order.",
              "- TERMINOLOGY_HUMAN_REVIEW.md: all decisions, exact source quotations/provenance and unchecked choices.",
              "- human_terminology_decisions.tsv: same IDs; every decision, final-term and attribution field blank.",
              "- terminology_adjudication_evidence.jsonl: exact original evidence record per proposed connection, source hashes, explicit English origin, model explanation and blank human decision.",
              "- model_mapping_plan.json: authored model analysis and six conflict relevance assessments, not source evidence or a human decision.",
              "- source_screening.jsonl, semantic_search_scope.json and input_integrity.json: complete inspection scope and protected-input hashes.", "",
              "Validate with `.venv/Scripts/python.exe scripts/validate_t1_adjudication.py`. Full command outcomes and Git status are recorded in T1_VALIDATION_RESULTS.json after the preparation checks run. Tests cover blank human fields, approval injection, source/evidence references, origin laundering, unresolved conflicts, protected source integrity and absence of translation work artifacts.", "",
              "Preparation does not modify the approved glossary, original evidence, English sources, quality gates or source-authority decisions. A/B receive no mandatory wording from this queue. No Agent A/B run, commit or push was performed.", ""]
    return "\n".join(lines)
