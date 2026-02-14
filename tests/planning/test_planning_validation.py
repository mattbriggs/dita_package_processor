"""
Tests for execution-time action validation utilities.

These tests verify that:
- required parameters are enforced
- filesystem preconditions are checked
- validation failures raise ActionValidationError
- valid inputs pass without error

No filesystem mutation is performed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest

from dita_package_processor.planning.models import PlanAction
from dita_package_processor.planning.validation import (
    ActionValidationError,
    validate_copy_map_parameters,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_action(parameters: Dict[str, str]) -> PlanAction:
    """
    Create a copy_map PlanAction for validation testing.

    :param parameters: Action parameters.
    :return: PlanAction instance.
    """
    return PlanAction(
        id="copy-001",
        type="copy_map",
        target="maps/Main.ditamap",
        reason="Validation test",
        parameters=parameters,
        derived_from_evidence=[],
    )


# ---------------------------------------------------------------------------
# Tests: missing parameters
# ---------------------------------------------------------------------------


def test_validation_fails_when_source_path_missing() -> None:
    """
    Missing source_path must raise ActionValidationError.
    """
    action = make_action(
        {
            "target_path": "/tmp/target.ditamap",
        }
    )

    with pytest.raises(ActionValidationError) as exc:
        validate_copy_map_parameters(action)

    assert "source_path" in str(exc.value)


def test_validation_fails_when_target_path_missing() -> None:
    """
    Missing target_path must raise ActionValidationError.
    """
    action = make_action(
        {
            "source_path": "/tmp/source.ditamap",
        }
    )

    with pytest.raises(ActionValidationError) as exc:
        validate_copy_map_parameters(action)

    assert "target_path" in str(exc.value)


# ---------------------------------------------------------------------------
# Tests: filesystem preconditions
# ---------------------------------------------------------------------------


def test_validation_fails_when_source_does_not_exist(
    tmp_path: Path,
) -> None:
    """
    Nonexistent source_path must be rejected.
    """
    source = tmp_path / "missing.ditamap"
    target = tmp_path / "target.ditamap"

    action = make_action(
        {
            "source_path": str(source),
            "target_path": str(target),
        }
    )

    with pytest.raises(ActionValidationError) as exc:
        validate_copy_map_parameters(action)

    assert "Source does not exist" in str(exc.value)


def test_validation_fails_when_target_already_exists(
    tmp_path: Path,
) -> None:
    """
    Existing target_path must be rejected to prevent overwrite.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "target.ditamap"

    source.write_text("<map/>", encoding="utf-8")
    target.write_text("<map/>", encoding="utf-8")

    action = make_action(
        {
            "source_path": str(source),
            "target_path": str(target),
        }
    )

    with pytest.raises(ActionValidationError) as exc:
        validate_copy_map_parameters(action)

    assert "Target already exists" in str(exc.value)


# ---------------------------------------------------------------------------
# Positive test
# ---------------------------------------------------------------------------


def test_validation_passes_for_valid_parameters(
    tmp_path: Path,
) -> None:
    """
    Valid source and non-existent target must pass validation.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "target.ditamap"

    source.write_text("<map/>", encoding="utf-8")

    action = make_action(
        {
            "source_path": str(source),
            "target_path": str(target),
        }
    )

    # Should not raise
    validate_copy_map_parameters(action)