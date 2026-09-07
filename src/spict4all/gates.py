"""Quality-gate enforcement for finalization."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .errors import GateError
from .evidence import FinalInclusionStatus
from .requirements import (
    CanonicalUnitVerification,
    ConflictStatus,
    SourceRequirement,
)


def required_generation_gates(quality_gates_path: Path) -> tuple[str, ...]:
    try:
        config = yaml.safe_load(quality_gates_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise GateError(f"Cannot load quality gates {quality_gates_path}: {exc}") from exc
    gates = config.get("quality_gates", {}) if isinstance(config, dict) else {}
    required = [name for name, value in gates.items() if isinstance(value, dict) and value.get("required")]
    if not required:
        raise GateError("No required quality gates found")
    return tuple(required)


def load_gate_results(path: Path) -> dict[str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"Cannot load gate results {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("gates"), dict):
        raise GateError("Gate results must contain an object named 'gates'")
    return {str(name): str(status).upper() for name, status in value["gates"].items()}


def assert_finalizable(
    artifact_status: str,
    gate_results: dict[str, str],
    required_gates: tuple[str, ...],
) -> None:
    if artifact_status.upper() != "FINAL":
        raise GateError("Artifact is still a draft; FINAL status is required")
    missing = [name for name in required_gates if gate_results.get(name) != "PASS"]
    if missing:
        raise GateError(f"Cannot mark artifact final; gates not passed: {missing}")


def source_reconciliation_blockers(
    canonical_verification: CanonicalUnitVerification,
    requirements: list[SourceRequirement],
) -> tuple[str, ...]:
    """Return authority decisions still required for the final source set."""

    requirement_blockers = [
        requirement.requirement_id
        for requirement in requirements
        if requirement.source_authority_confirmation_required
        and requirement.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
    ]
    canonical_blockers = [
        str(resolution.unit["unit_id"])
        for resolution in canonical_verification.resolutions
        if resolution.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
    ]
    return tuple(sorted(requirement_blockers + canonical_blockers))


def publication_blockers(
    canonical_verification: CanonicalUnitVerification,
    requirements: list[SourceRequirement],
) -> tuple[str, ...]:
    """Return unresolved authority issues that prohibit publication."""

    requirement_blockers = [
        requirement.requirement_id
        for requirement in requirements
        if requirement.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
        and (
            requirement.publication_blocking
            or requirement.conflict_status
            is ConflictStatus.UNRESOLVED_CANONICAL_OMISSION
        )
    ]
    canonical_blockers = [
        str(resolution.unit["unit_id"])
        for resolution in canonical_verification.resolutions
        if resolution.final_inclusion_status is FinalInclusionStatus.UNRESOLVED
        and resolution.exception is not None
        and resolution.exception.publication_blocking
    ]
    return tuple(sorted(requirement_blockers + canonical_blockers))


def assert_source_reconciliation_resolved(
    canonical_verification: CanonicalUnitVerification,
    requirements: list[SourceRequirement],
) -> None:
    blockers = source_reconciliation_blockers(canonical_verification, requirements)
    if blockers:
        raise GateError(f"Final source reconciliation is unresolved: {list(blockers)}")


def assert_publication_allowed(
    canonical_verification: CanonicalUnitVerification,
    requirements: list[SourceRequirement],
) -> None:
    blockers = publication_blockers(canonical_verification, requirements)
    if blockers:
        raise GateError(f"Publication is blocked by unresolved source authority: {list(blockers)}")
