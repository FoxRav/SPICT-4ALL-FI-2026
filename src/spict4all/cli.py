"""Command-line interface for integrity, validation, and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import validate_jsonl_artifact
from .coverage import check_coverage, require_complete_coverage
from .errors import SpictError
from .gates import (
    assert_finalizable,
    assert_publication_allowed,
    assert_source_reconciliation_resolved,
    load_gate_results,
    required_generation_gates,
)
from .governance import GovernanceFileCheck, verify_governance_manifest
from .jsonl import load_jsonl
from .reports import generate_discrepancy_report
from .requirements import (
    CanonicalUnitVerification,
    SourceRequirementVerification,
    build_translation_evidence_sources,
    requirement_identity_summary,
    verify_canonical_units_against_source,
    verify_source_requirements,
)
from .reviews import load_human_reviews, validate_human_reviews
from .runs import build_run_metadata, create_immutable_run
from .sources import require_verified_sources
from .terminology import validate_terminology_evidence
from .units import load_source_units


def _root_path(root: Path, relative: str) -> Path:
    return (root / relative).resolve()


def _load_canonical_units(
    root: Path,
    canonical_units: list[dict[str, object]],
) -> CanonicalUnitVerification:
    _verify_governance(root)
    return verify_canonical_units_against_source(
        _root_path(root, "sources/manifests/source_manifest.json"),
        _root_path(root, "sources/official"),
        canonical_units,
        _root_path(root, "data/canonical_unit_exceptions.jsonl"),
        _root_path(root, "schemas/canonical_unit_exception.schema.json"),
    )


def _verify_governance(root: Path) -> tuple[GovernanceFileCheck, ...]:
    return verify_governance_manifest(
        root,
        _root_path(root, "data/governance_integrity_manifest.json"),
        _root_path(root, "schemas/governance_integrity_manifest.schema.json"),
    )


def _load_requirements(
    root: Path,
    canonical_verification: CanonicalUnitVerification,
) -> SourceRequirementVerification:
    return verify_source_requirements(
        _root_path(root, "data/source_requirements.jsonl"),
        _root_path(root, "schemas/source_requirement.schema.json"),
        _root_path(root, "sources/manifests/source_manifest.json"),
        _root_path(root, "sources/official"),
        canonical_verification,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spict4all")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("verify-sources", help="verify manifest, files, and source units")
    subparsers.add_parser(
        "validate-requirements", help="validate official source requirements"
    )
    subparsers.add_parser(
        "validate-canonical", help="validate canonical units and exceptions"
    )
    subparsers.add_parser(
        "validate-governance", help="verify mutable governance data hashes"
    )
    subparsers.add_parser(
        "validate-terminology", help="validate terminology evidence readiness"
    )

    artifact = subparsers.add_parser("validate-artifact", help="validate a JSONL artifact")
    artifact.add_argument("artifact", type=Path)
    artifact.add_argument("--schema", type=Path, required=True)
    artifact.add_argument("--require-coverage", action="store_true")

    coverage = subparsers.add_parser("check-coverage", help="check JSONL unit coverage")
    coverage.add_argument("artifact", type=Path)

    review = subparsers.add_parser("validate-review", help="validate human-review TSV")
    review.add_argument("review", type=Path)

    run = subparsers.add_parser("create-run", help="create an immutable run directory")
    run.add_argument("--runs-root", type=Path, default=Path("work/runs"))
    run.add_argument("--run-id", required=True)
    run.add_argument("--role", required=True)
    run.add_argument("--input", type=Path, action="append", default=[])

    report = subparsers.add_parser("report-discrepancies", help="compare A/B artifacts mechanically")
    report.add_argument("--agent-a", type=Path, required=True)
    report.add_argument("--agent-b", type=Path, required=True)
    report.add_argument("--schema", type=Path, default=Path("schemas/translation_candidate.schema.json"))
    report.add_argument("--output", type=Path, required=True)

    final = subparsers.add_parser("check-final", help="enforce finalization gates and human review")
    final.add_argument("--status", required=True)
    final.add_argument("--gate-results", type=Path, required=True)
    final.add_argument("--review", type=Path, required=True)
    return parser


def run_command(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    source_units_path = _root_path(root, "data/source_units.jsonl")
    if args.command == "verify-sources":
        checks = require_verified_sources(
            _root_path(root, "sources/manifests/source_manifest.json"),
            _root_path(root, "sources/official"),
        )
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        governance = _verify_governance(root)
        for check in checks:
            print(f"PASS {check.filename} {check.actual_sha256} {check.actual_bytes} bytes")
        print(
            f"PASS canonical units: {len(canonical.resolutions)} unique, contiguous, "
            f"hash-matched, source-resolved; exceptions={len(canonical.exceptions)}"
        )
        print(
            f"PASS source requirements: {len(verification.requirements)} unique, "
            "schema-valid, provenance-linked, exact-text and change-spec completeness "
            "verified; marked paragraph elements="
            f"{len(verification.completeness.census.marked_paragraphs)}, "
            f"yellow runs={verification.completeness.census.yellow_highlighted_runs}, "
            f"green runs={verification.completeness.census.green_highlighted_runs}, "
            f"accent6 runs={verification.completeness.census.accent6_font_runs}; "
            f"{requirement_identity_summary(verification.requirements)} "
            "(derived from data, not a Python allow-list)"
        )
        print(f"PASS governance data: {len(governance)} files hash-matched")
        return 0

    if args.command == "validate-governance":
        governance = _verify_governance(root)
        print(f"PASS governance data: {len(governance)} files hash-matched")
        return 0

    if args.command == "validate-terminology":
        terminology_result = validate_terminology_evidence(root)
        print(
            "PASS terminology evidence: "
            f"sources={terminology_result.source_count}, "
            f"extracted={terminology_result.extracted_count}, "
            f"source_provided_english={terminology_result.source_provided_english_count}, "
            f"conflicts={terminology_result.conflict_count}, "
            f"approved={terminology_result.approved_count}, "
            f"relevance_matches={terminology_result.relevance_count}"
        )
        return 0

    if args.command == "validate-requirements":
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        print(
            f"PASS source requirements: {len(verification.requirements)} unique, "
            "schema-valid, provenance-linked, exact-text and change-spec completeness "
            "verified; marked paragraph elements="
            f"{len(verification.completeness.census.marked_paragraphs)}, "
            f"yellow runs={verification.completeness.census.yellow_highlighted_runs}, "
            f"green runs={verification.completeness.census.green_highlighted_runs}, "
            f"accent6 runs={verification.completeness.census.accent6_font_runs}; "
            f"{requirement_identity_summary(verification.requirements)} "
            "(derived from data, not a Python allow-list)"
        )
        return 0

    if args.command == "validate-canonical":
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        print(
            f"PASS canonical units: {len(canonical.resolutions)} source-resolved; "
            f"direct={sum(item.direct_location is not None for item in canonical.resolutions)}, "
            "normalized="
            f"{sum(item.normalized_location is not None for item in canonical.resolutions)}, "
            f"exceptions={len(canonical.exceptions)}"
        )
        return 0

    if args.command == "validate-artifact":
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        evidence_sources = build_translation_evidence_sources(
            canonical, verification.requirements
        )
        records = validate_jsonl_artifact(
            args.artifact.resolve(),
            args.schema.resolve(),
            source_records=evidence_sources,
        )
        if args.require_coverage:
            require_complete_coverage(evidence_sources, records)
        print(f"PASS artifact records: {len(records)}")
        return 0

    if args.command == "check-coverage":
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        evidence_sources = build_translation_evidence_sources(
            canonical, verification.requirements
        )
        coverage_result = check_coverage(
            evidence_sources, load_jsonl(args.artifact.resolve())
        )
        print(json.dumps(coverage_result.__dict__, ensure_ascii=False, indent=2))
        return 0 if coverage_result.complete else 1

    if args.command == "validate-review":
        reviews = load_human_reviews(args.review.resolve())
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        evidence_sources = build_translation_evidence_sources(
            canonical, verification.requirements
        )
        validate_human_reviews(reviews, evidence_sources)
        print(f"PASS human reviews: {len(reviews)}")
        return 0

    if args.command == "create-run":
        runs_root = args.runs_root if args.runs_root.is_absolute() else root / args.runs_root
        inputs = [path if path.is_absolute() else root / path for path in args.input]
        metadata = build_run_metadata(args.run_id, args.role, inputs)
        path = create_immutable_run(runs_root, metadata)
        print(path)
        return 0

    if args.command == "report-discrepancies":
        schema = args.schema if args.schema.is_absolute() else root / args.schema
        source_units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, source_units)
        verification = _load_requirements(root, canonical)
        evidence_sources = build_translation_evidence_sources(
            canonical, verification.requirements
        )
        agent_a = validate_jsonl_artifact(
            args.agent_a.resolve(), schema, source_records=evidence_sources
        )
        agent_b = validate_jsonl_artifact(
            args.agent_b.resolve(), schema, source_records=evidence_sources
        )
        output = args.output if args.output.is_absolute() else root / args.output
        generate_discrepancy_report(evidence_sources, agent_a, agent_b, output)
        print(output)
        return 0

    if args.command == "check-final":
        units = load_source_units(source_units_path)
        canonical = _load_canonical_units(root, units)
        verification = _load_requirements(root, canonical)
        requirements = list(verification.requirements)
        assert_publication_allowed(canonical, requirements)
        assert_source_reconciliation_resolved(canonical, requirements)
        evidence_sources = build_translation_evidence_sources(
            canonical, verification.requirements
        )
        validate_human_reviews(
            load_human_reviews(args.review.resolve()),
            evidence_sources,
            require_release_ready=True,
        )
        required = required_generation_gates(_root_path(root, "config/quality_gates.yaml"))
        assert_finalizable(args.status, load_gate_results(args.gate_results.resolve()), required)
        print("PASS finalization prerequisites")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        return run_command(parser.parse_args(argv))
    except SpictError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
