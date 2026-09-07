from __future__ import annotations

import pytest

from spict4all.coverage import check_coverage, require_complete_coverage
from spict4all.errors import CoverageError


def test_complete_coverage_passes(make_unit) -> None:
    units = [make_unit(0), make_unit(1)]
    result = require_complete_coverage(units, [{"unit_id": unit["unit_id"]} for unit in units])
    assert result.complete


def test_missing_artifact_unit_fails(make_unit) -> None:
    units = [make_unit(0), make_unit(1)]
    with pytest.raises(CoverageError, match="S4A-2026-001"):
        require_complete_coverage(units, [{"unit_id": "S4A-2026-000"}])


def test_extra_artifact_unit_is_reported(make_unit) -> None:
    result = check_coverage(
        [make_unit(0)],
        [{"unit_id": "S4A-2026-000"}, {"unit_id": "S4A-2026-999"}],
    )
    assert result.extra == ("S4A-2026-999",)


def test_duplicate_artifact_unit_fails(make_unit) -> None:
    with pytest.raises(CoverageError, match="Duplicate artifact unit IDs"):
        check_coverage(
            [make_unit(0)],
            [{"unit_id": "S4A-2026-000"}, {"unit_id": "S4A-2026-000"}],
        )
