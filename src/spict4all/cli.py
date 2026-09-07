"""Command-line interface for integrity, validation, and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import validate_jsonl_artifact
from .coverage import check_coverage, require_complete_coverage
from .errors import SpictError
from .gates import assert_finalizable, load_gate_results, required_generation_gates
from .jsonl import load_jsonl
from .reports import generate_discrepancy_report
from .reviews import load_human_reviews, validate_human_reviews
from .runs import build_run_metadata, create_immutable_run
from .sources import require_verified_sources
from .units import load_source_units


def _root_path(root: Path, relative: str) -> Path:
    return (root / relative).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spict4all")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("verify-sources", help="verify manifest, files, and source units")

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
        for check in checks:
            print(f"PASS {check.filename} {check.actual_sha256} {check.actual_bytes} bytes")
        print(f"PASS source units: {len(units)} unique, contiguous, hash-matched")
        return 0

    if args.command == "validate-artifact":
        records = validate_jsonl_artifact(args.artifact.resolve(), args.schema.resolve(), source_units_path)
        if args.require_coverage:
            require_complete_coverage(load_source_units(source_units_path), records)
        print(f"PASS artifact records: {len(records)}")
        return 0

    if args.command == "check-coverage":
        result = check_coverage(load_source_units(source_units_path), load_jsonl(args.artifact.resolve()))
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0 if result.complete else 1

    if args.command == "validate-review":
        reviews = load_human_reviews(args.review.resolve())
        validate_human_reviews(reviews, load_source_units(source_units_path))
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
        agent_a = validate_jsonl_artifact(args.agent_a.resolve(), schema, source_units_path)
        agent_b = validate_jsonl_artifact(args.agent_b.resolve(), schema, source_units_path)
        output = args.output if args.output.is_absolute() else root / args.output
        generate_discrepancy_report(source_units, agent_a, agent_b, output)
        print(output)
        return 0

    if args.command == "check-final":
        units = load_source_units(source_units_path)
        validate_human_reviews(
            load_human_reviews(args.review.resolve()), units, require_release_ready=True
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
