"""Repository-wired build and validation entry points for a G1 forward run."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .artifacts import validate_jsonl_artifact
from .errors import ArtifactValidationError
from .evidence import EvidenceSource
from .forward_candidates import (
    ForwardCandidateReport,
    build_forward_candidate_records,
    validate_forward_candidates,
)
from .governance import verify_governance_manifest
from .requirements import (
    build_translation_evidence_sources,
    verify_canonical_units_against_source,
    verify_source_requirements,
)
from .sources import require_verified_sources
from .units import load_source_units

CANDIDATE_SCHEMA = "schemas/translation_candidate.schema.json"


def load_evidence_sources(root: Path) -> list[EvidenceSource]:
    """Rebuild the frozen evidence universe after full source-integrity verification."""

    require_verified_sources(
        root / "sources/manifests/source_manifest.json", root / "sources/official"
    )
    verify_governance_manifest(
        root,
        root / "data/governance_integrity_manifest.json",
        root / "schemas/governance_integrity_manifest.schema.json",
    )
    units = load_source_units(root / "data/source_units.jsonl")
    canonical = verify_canonical_units_against_source(
        root / "sources/manifests/source_manifest.json",
        root / "sources/official",
        units,
        root / "data/canonical_unit_exceptions.jsonl",
        root / "schemas/canonical_unit_exception.schema.json",
    )
    verification = verify_source_requirements(
        root / "data/source_requirements.jsonl",
        root / "schemas/source_requirement.schema.json",
        root / "sources/manifests/source_manifest.json",
        root / "sources/official",
        canonical,
    )
    return list(build_translation_evidence_sources(canonical, verification.requirements))


def load_authored_translations(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"Cannot load authored translations {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ArtifactValidationError(f"Authored translations must be an object: {path}")
    run = payload.get("run")
    candidates = payload.get("candidates")
    if not isinstance(run, dict) or not isinstance(candidates, dict):
        raise ArtifactValidationError(
            f"Authored translations must contain 'run' and 'candidates' objects: {path}"
        )
    return run, candidates


def write_candidates(records: list[dict[str, Any]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def build_run(root: Path, authored_path: Path, destination: Path) -> list[dict[str, Any]]:
    sources = load_evidence_sources(root)
    run, authored = load_authored_translations(authored_path)
    records = build_forward_candidate_records(sources, run, authored)
    write_candidates(records, destination)
    return records


def validate_run(root: Path, candidates_path: Path, *, translator_role: str) -> dict[str, Any]:
    sources = load_evidence_sources(root)
    records = validate_jsonl_artifact(
        candidates_path, root / CANDIDATE_SCHEMA, source_records=sources
    )
    report: ForwardCandidateReport = validate_forward_candidates(
        sources, records, expected_translator_role=translator_role
    )
    try:
        artifact = str(candidates_path.resolve().relative_to(root.resolve()).as_posix())
    except ValueError:
        artifact = str(candidates_path.resolve())
    return {
        "artifact": artifact,
        "translator_role": translator_role,
        "schema_valid": True,
        "coverage_complete": True,
        **asdict(report),
    }
