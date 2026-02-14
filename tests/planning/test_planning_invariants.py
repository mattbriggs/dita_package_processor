"""
Tests for plan invariant enforcement.
"""

import pytest

from dita_package_processor.planning.invariants import (
    InvariantViolationError,
    validate_invariants,
)


def test_multiple_main_map_selections_fail() -> None:
    plan = {
        "actions": [
            {"id": "select-1", "type": "select_main_map", "target": "a.ditamap"},
            {"id": "select-2", "type": "select_main_map", "target": "b.ditamap"},
        ]
    }

    with pytest.raises(InvariantViolationError):
        validate_invariants(plan)