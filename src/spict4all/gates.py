"""Quality-gate enforcement for finalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .errors import GateError


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
