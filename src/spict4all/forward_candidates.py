"""Mechanical fidelity checks for independent EN->FI forward-translation candidates.

These checks are deterministic surface checks over frozen source text and the
Finnish candidate. They detect omission, addition, hash drift and loss of
negation, modality, agency and alternative structure. They are not a linguistic,
clinical or plain-language review and carry no approval authority.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .coverage import require_complete_coverage
from .errors import ArtifactValidationError
from .evidence import EvidenceSource, EvidenceSourceKind, FinalInclusionStatus
from .hashing import sha256_text

EXTENSIONS_NAMESPACE = "g1_forward"

REQUIRED_EXTENSION_FIELDS: tuple[str, ...] = (
    "exact_source_text_en",
    "source_kind",
    "source_role",
    "document_part",
    "source_location",
    "final_inclusion_status",
    "eligible_for_document_insertion",
    "translator_role",
    "translator_identity",
    "run_id",
    "run_timestamp_utc",
    "run_prompt_version",
    "human_terminology_decisions_applied",
    "untranslated_verbatim",
)

# English function words that must never survive into a Finnish candidate.
# None of these forms is a Finnish word, so a match is residual English.
ENGLISH_LEAKAGE = re.compile(
    r"\b(the|and|or|with|of|that|this|for|are|is|not|from|their|they|have|has|been)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarkerPair:
    """Bidirectional English/Finnish surface-marker correspondence."""

    name: str
    english: re.Pattern[str]
    finnish: re.Pattern[str]


MARKER_PAIRS: tuple[MarkerPair, ...] = (
    MarkerPair(
        "negation",
        re.compile(r"\b(not|no|never|without|unable|cannot|nor)\b|n't\b", re.IGNORECASE),
        re.compile(
            r"\b(ei|eiv\u00e4t|en|et|emme|ette|eik\u00e4|ettei|jottei|\u00e4l\u00e4"
            r"|\u00e4lk\u00e4\u00e4|ilman)\b|\w+(matta|m\u00e4tt\u00e4)\b",
            re.IGNORECASE,
        ),
    ),
    MarkerPair(
        "inability",
        re.compile(r"\bunable\b|\bnot able\b", re.IGNORECASE),
        re.compile(r"\b(pysty\w*|kykene\w*)", re.IGNORECASE),
    ),
    MarkerPair(
        "possibility",
        re.compile(r"\bpossible\b", re.IGNORECASE),
        re.compile(r"\bmahdolli\w*", re.IGNORECASE),
    ),
    MarkerPair(
        "inclusive_alternative",
        re.compile(r"and/or", re.IGNORECASE),
        re.compile(r"ja/tai", re.IGNORECASE),
    ),
    MarkerPair(
        "first_person_plural_agency",
        re.compile(r"\b(we|us|our)\b", re.IGNORECASE),
        re.compile(r"\b(me|meit\u00e4|meille|meid\u00e4n)\b|\w+mme\b", re.IGNORECASE),
    ),
    MarkerPair(
        # "henkilokunta" (staff) must not count as the person role.
        "person_role",
        re.compile(r"\b(person|people)\b", re.IGNORECASE),
        re.compile(r"\b(henkil\u00f6(?!kun)\w*|ihmis\w*|ihminen)", re.IGNORECASE),
    ),
    MarkerPair(
        "family_role",
        re.compile(r"\bfamily\b", re.IGNORECASE),
        re.compile(r"\bperhe\w*", re.IGNORECASE),
    ),
    MarkerPair(
        "staff_role",
        re.compile(r"\bstaff\b", re.IGNORECASE),
        re.compile(r"\bhenkil\u00f6kun\w*", re.IGNORECASE),
    ),
)

# Characters whose count must be identical in source and candidate. They carry
# segmentation, alternative-list and question structure in this document.
COUNTED_CHARACTERS: tuple[str, ...] = ("\n", ";", ":", "?", ".", "(", ")", "\u2026")

TERMINAL_PUNCTUATION = ".?!:;"

DIGIT_RUN = re.compile(r"\d+")


@dataclass(frozen=True)
class HumanTerminologyBinding:
    """An explicit human terminology decision bound to specific source units."""

    decision_id: str
    unit_ids: frozenset[str]
    required_finnish_stems: tuple[str, ...]


HUMAN_TERMINOLOGY_BINDINGS: tuple[HumanTerminologyBinding, ...] = (
    HumanTerminologyBinding(
        "T-002",
        frozenset({"S4A-2026-001", "S4A-2026-042"}),
        ("elinik\u00e4\u00e4 lyhent", "terveydentil"),
    ),
    HumanTerminologyBinding(
        "T-013",
        frozenset({"S4A-2026-035"}),
        ("hengityskone",),
    ),
    HumanTerminologyBinding(
        "T-016",
        frozenset({"S4A-2026-049"}),
        ("kokonaisvaltai", "hoito"),
    ),
)


@dataclass(frozen=True)
class ProjectOwnerWordingBinding:
    """A pre-G1 Project Owner wording decision without a terminology decision ID."""

    concept_en: str
    required_finnish: str
    unit_ids: frozenset[str]
    additional_finnish_stems: tuple[str, ...] = ()


# Exact T1.2 Project Owner wordings. No invented decision IDs.
PROJECT_OWNER_WORDING_BINDINGS: tuple[ProjectOwnerWordingBinding, ...] = (
    ProjectOwnerWordingBinding(
        "less well",
        "terveydentila on heikentynyt",
        frozenset({"S4A-2026-001", "S4A-2026-042"}),
    ),
    ProjectOwnerWordingBinding(
        "less able to manage usual activities",
        "toimintakyky on heikentynyt",
        frozenset({"S4A-2026-004", "S4A-2026-014"}),
        ("tavanomais",),
    ),
    ProjectOwnerWordingBinding(
        "not well enough for cancer treatment",
        "ei ole riitt\u00e4v\u00e4n hyv\u00e4kuntoinen sy\u00f6p\u00e4hoitoon",
        frozenset({"S4A-2026-017"}),
    ),
)


@dataclass(frozen=True)
class ForwardCandidateReport:
    """Machine-readable outcome of a forward-candidate validation run."""

    expected_source_count: int
    candidate_count: int
    canonical_count: int
    source_requirement_count: int
    unresolved_authority_count: int
    document_insertable_count: int
    untranslated_verbatim_count: int
    issue_counts_by_severity: dict[str, int]
    human_terminology_decisions_applied: dict[str, list[str]]


def _extension(record: dict[str, Any]) -> dict[str, Any] | None:
    extensions = record.get("extensions")
    if not isinstance(extensions, dict):
        return None
    namespaced = extensions.get(EXTENSIONS_NAMESPACE)
    if not isinstance(namespaced, dict):
        return None
    return namespaced


def _source_binding_failures(
    unit_id: str,
    record: dict[str, Any],
    source: EvidenceSource,
    extension: dict[str, Any],
) -> list[str]:
    """Prove every candidate is bound to frozen source text and its frozen hash."""

    failures: list[str] = []
    exact = extension.get("exact_source_text_en")
    if not isinstance(exact, str) or exact != source.exact_source_text_en:
        failures.append(f"{unit_id}: recorded exact_source_text_en differs from frozen source text")
        return failures
    if sha256_text(exact) != source.source_text_sha256:
        failures.append(f"{unit_id}: recorded source text does not hash to the frozen source hash")
    if record.get("source_text_sha256") != source.source_text_sha256:
        failures.append(f"{unit_id}: source_text_sha256 does not match frozen source hash")
    expected_provenance: tuple[tuple[str, object], ...] = (
        ("source_kind", source.source_kind.value),
        ("source_role", source.source_provenance.source_role),
        ("document_part", source.source_provenance.document_part),
        ("final_inclusion_status", source.final_inclusion_status.value),
        ("eligible_for_document_insertion", source.eligible_for_document_insertion),
    )
    for field, expected in expected_provenance:
        if extension.get(field) != expected:
            failures.append(
                f"{unit_id}: {field} is {extension.get(field)!r}, frozen source says {expected!r}"
            )
    if extension.get("source_location") != dict(source.source_provenance.location):
        failures.append(f"{unit_id}: source_location differs from frozen source provenance")
    return failures


def _structure_failures(unit_id: str, source_text: str, candidate: str) -> list[str]:
    """Detect segment, list and sentence omissions or additions."""

    failures: list[str] = []
    for character in COUNTED_CHARACTERS:
        expected = source_text.count(character)
        actual = candidate.count(character)
        if expected != actual:
            failures.append(
                f"{unit_id}: {character!r} count is {actual}, source has {expected}"
            )
    source_tail = source_text.rstrip()[-1:]
    candidate_tail = candidate.rstrip()[-1:]
    if source_tail in TERMINAL_PUNCTUATION:
        if candidate_tail != source_tail:
            failures.append(
                f"{unit_id}: terminal punctuation is {candidate_tail!r}, source has {source_tail!r}"
            )
    elif candidate_tail in TERMINAL_PUNCTUATION:
        failures.append(
            f"{unit_id}: candidate adds terminal punctuation {candidate_tail!r} not in the source"
        )
    if DIGIT_RUN.findall(source_text) != DIGIT_RUN.findall(candidate):
        failures.append(
            f"{unit_id}: digit sequences {DIGIT_RUN.findall(candidate)} do not match "
            f"source {DIGIT_RUN.findall(source_text)}"
        )
    if source_text.count("SPICT") != candidate.count("SPICT"):
        failures.append(f"{unit_id}: number of SPICT name occurrences differs from the source")
    return failures


def _marker_failures(unit_id: str, source_text: str, candidate: str) -> list[str]:
    failures: list[str] = []
    for pair in MARKER_PAIRS:
        in_source = pair.english.search(source_text) is not None
        in_candidate = pair.finnish.search(candidate) is not None
        if in_source != in_candidate:
            failures.append(
                f"{unit_id}: {pair.name} present in source={in_source} but in candidate={in_candidate}"
            )
    return failures


def _candidate_text_failures(
    unit_id: str,
    source_text: str,
    candidate: Any,
    untranslated_verbatim: Any,
) -> list[str]:
    if not isinstance(candidate, str) or not candidate.strip():
        return [f"{unit_id}: candidate_fi is blank"]
    if not isinstance(untranslated_verbatim, bool):
        return [f"{unit_id}: untranslated_verbatim must be a boolean"]
    failures: list[str] = []
    identical = candidate.strip() == source_text.strip()
    if untranslated_verbatim:
        if not identical:
            failures.append(
                f"{unit_id}: declared untranslated_verbatim but differs from the exact source text"
            )
        return failures
    if identical:
        failures.append(
            f"{unit_id}: candidate is identical to the English source "
            "and is not declared untranslated_verbatim"
        )
        return failures
    leaked = sorted({match.lower() for match in ENGLISH_LEAKAGE.findall(candidate)})
    if leaked:
        failures.append(f"{unit_id}: residual English function words in candidate: {leaked}")
    failures.extend(_structure_failures(unit_id, source_text, candidate))
    failures.extend(_marker_failures(unit_id, source_text, candidate))
    return failures


def _human_terminology_failures(
    records_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    """Require recorded human terminology decisions to be visibly applied."""

    failures: list[str] = []
    for binding in HUMAN_TERMINOLOGY_BINDINGS:
        for unit_id in sorted(binding.unit_ids):
            record = records_by_id.get(unit_id)
            if record is None:
                continue
            candidate = record.get("candidate_fi")
            if not isinstance(candidate, str):
                continue
            lowered = candidate.lower()
            missing = [stem for stem in binding.required_finnish_stems if stem not in lowered]
            if missing:
                failures.append(
                    f"{unit_id}: human terminology decision {binding.decision_id} "
                    f"not visible in candidate; missing stems {missing}"
                )
            extension = _extension(record)
            applied = extension.get("human_terminology_decisions_applied") if extension else None
            if not isinstance(applied, list) or binding.decision_id not in applied:
                failures.append(
                    f"{unit_id}: human terminology decision {binding.decision_id} "
                    "is not recorded in human_terminology_decisions_applied"
                )
    return failures


def _project_owner_wording_failures(
    records_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    """Require T1.2 Project Owner wordings to be visible. No invented T-IDs."""

    failures: list[str] = []
    for binding in PROJECT_OWNER_WORDING_BINDINGS:
        for unit_id in sorted(binding.unit_ids):
            record = records_by_id.get(unit_id)
            if record is None:
                continue
            candidate = record.get("candidate_fi")
            if not isinstance(candidate, str):
                continue
            lowered = candidate.lower()
            if binding.required_finnish.lower() not in lowered:
                failures.append(
                    f"{unit_id}: Project Owner wording for {binding.concept_en!r} "
                    f"not visible; required {binding.required_finnish!r}"
                )
            missing = [stem for stem in binding.additional_finnish_stems if stem not in lowered]
            if missing:
                failures.append(
                    f"{unit_id}: Project Owner wording for {binding.concept_en!r} "
                    f"is missing surrounding-scope stems {missing}"
                )
    return failures


def _issue_failures(unit_id: str, record: dict[str, Any], source: EvidenceSource) -> list[str]:
    """Require unresolved source authority to stay visible as a blocker issue."""

    issues = record.get("issues")
    if not isinstance(issues, list):
        return [f"{unit_id}: issues must be a list"]
    if source.final_inclusion_status is not FinalInclusionStatus.UNRESOLVED:
        return []
    for issue in issues:
        if (
            isinstance(issue, dict)
            and issue.get("severity") == "BLOCKER"
            and issue.get("type") == "unresolved_source_authority"
        ):
            return []
    return [
        f"{unit_id}: frozen source is UNRESOLVED but no BLOCKER "
        "unresolved_source_authority issue is recorded"
    ]


REQUIRED_RUN_FIELDS: tuple[str, ...] = (
    "run_id",
    "translator_role",
    "translator_identity",
    "model",
    "prompt_version",
    "run_timestamp_utc",
)


def build_forward_candidate_records(
    sources: list[EvidenceSource],
    run: dict[str, Any],
    authored: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join authored Finnish candidates with frozen source text, hashes and provenance.

    Source text, hashes and provenance are always taken from the frozen evidence
    contract, never from the authored file, so a candidate can never carry a
    hand-copied source hash.
    """

    missing_run = [field for field in REQUIRED_RUN_FIELDS if not run.get(field)]
    if missing_run:
        raise ArtifactValidationError(f"Run metadata missing fields: {missing_run}")
    source_ids = {source.evidence_id for source in sources}
    unknown = sorted(set(authored) - source_ids)
    if unknown:
        raise ArtifactValidationError(f"Authored translations for unknown sources: {unknown}")
    absent = sorted(source_ids - set(authored))
    if absent:
        raise ArtifactValidationError(f"Authored translations missing for sources: {absent}")

    records: list[dict[str, Any]] = []
    for source in sources:
        authored_entry = authored[source.evidence_id]
        records.append(
            {
                "unit_id": source.evidence_id,
                "source_text_sha256": source.source_text_sha256,
                "model": run["model"],
                "prompt_version": run["prompt_version"],
                "candidate_fi": authored_entry["candidate_fi"],
                "decision_note": authored_entry["decision_note"],
                "issues": authored_entry.get("issues", []),
                "status": "READY_FOR_SYNTHESIS",
                "extensions": {
                    EXTENSIONS_NAMESPACE: {
                        "exact_source_text_en": source.exact_source_text_en,
                        "source_kind": source.source_kind.value,
                        "source_role": source.source_provenance.source_role,
                        "document_part": source.source_provenance.document_part,
                        "source_location": dict(source.source_provenance.location),
                        "requires_translation_evidence": source.requires_translation_evidence,
                        "requires_human_signoff": source.requires_human_signoff,
                        "final_inclusion_status": source.final_inclusion_status.value,
                        "eligible_for_document_insertion": (
                            source.eligible_for_document_insertion
                        ),
                        "translator_role": run["translator_role"],
                        "translator_identity": run["translator_identity"],
                        "run_id": run["run_id"],
                        "run_timestamp_utc": run["run_timestamp_utc"],
                        "run_prompt_version": run["prompt_version"],
                        "run_prompt_sha256": run.get("prompt_sha256"),
                        "configured_role_model": run.get("configured_role_model"),
                        "human_terminology_decisions_applied": authored_entry.get(
                            "human_terminology_decisions_applied", []
                        ),
                        "untranslated_verbatim": authored_entry.get(
                            "untranslated_verbatim", False
                        ),
                    }
                },
            }
        )
    return records


def validate_forward_candidates(
    sources: list[EvidenceSource],
    records: list[dict[str, Any]],
    *,
    expected_translator_role: str,
) -> ForwardCandidateReport:
    """Validate membership, source binding and mechanical fidelity of candidates."""

    require_complete_coverage(sources, records)
    sources_by_id = {source.evidence_id: source for source in sources}
    records_by_id: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    severity_counts: dict[str, int] = {}
    decisions_applied: dict[str, list[str]] = {}
    untranslated_verbatim_count = 0

    for record in records:
        unit_id = record.get("unit_id")
        if not isinstance(unit_id, str):
            failures.append("record without a string unit_id")
            continue
        records_by_id[unit_id] = record
        source = sources_by_id[unit_id]
        extension = _extension(record)
        if extension is None:
            failures.append(f"{unit_id}: missing extensions.{EXTENSIONS_NAMESPACE} object")
            continue
        missing_fields = [field for field in REQUIRED_EXTENSION_FIELDS if field not in extension]
        if missing_fields:
            failures.append(f"{unit_id}: missing extension fields {missing_fields}")
            continue
        if extension.get("translator_role") != expected_translator_role:
            failures.append(
                f"{unit_id}: translator_role is {extension.get('translator_role')!r}, "
                f"expected {expected_translator_role!r}"
            )
        if not isinstance(record.get("model"), str) or not record["model"].strip():
            failures.append(f"{unit_id}: model identity is missing")
        failures.extend(_source_binding_failures(unit_id, record, source, extension))
        failures.extend(
            _candidate_text_failures(
                unit_id,
                source.exact_source_text_en,
                record.get("candidate_fi"),
                extension.get("untranslated_verbatim"),
            )
        )
        failures.extend(_issue_failures(unit_id, record, source))
        if extension.get("untranslated_verbatim") is True:
            untranslated_verbatim_count += 1
        note = record.get("decision_note")
        if not isinstance(note, str) or not note.strip():
            failures.append(f"{unit_id}: decision_note is missing")
        for issue in record.get("issues", []):
            if isinstance(issue, dict) and isinstance(issue.get("severity"), str):
                severity = issue["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        applied = extension.get("human_terminology_decisions_applied")
        if isinstance(applied, list) and applied:
            decisions_applied[unit_id] = [str(item) for item in applied]

    failures.extend(_human_terminology_failures(records_by_id))
    failures.extend(_project_owner_wording_failures(records_by_id))
    if failures:
        raise ArtifactValidationError(
            "Forward-candidate validation failed: " + "; ".join(sorted(failures))
        )

    return ForwardCandidateReport(
        expected_source_count=len(sources),
        candidate_count=len(records),
        canonical_count=sum(
            source.source_kind is EvidenceSourceKind.CANONICAL_SOURCE_UNIT for source in sources
        ),
        source_requirement_count=sum(
            source.source_kind is EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT
            for source in sources
        ),
        unresolved_authority_count=sum(
            source.final_inclusion_status is FinalInclusionStatus.UNRESOLVED for source in sources
        ),
        document_insertable_count=sum(
            source.eligible_for_document_insertion for source in sources
        ),
        untranslated_verbatim_count=untranslated_verbatim_count,
        issue_counts_by_severity=dict(sorted(severity_counts.items())),
        human_terminology_decisions_applied=dict(sorted(decisions_applied.items())),
    )
