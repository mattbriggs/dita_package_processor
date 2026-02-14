"""
Tests for materialization validation failures.

These tests ensure that unsafe or meaningless materialization attempts
fail loudly and deterministically.
"""

from datetime import datetime, UTC
from pathlib import Path

import pytest

from dita_package_processor.materialization.validation import (
    MaterializationValidator,
    MaterializationValidationError,
)
from dita_package_processor.planning.models import Plan


# ---------------------------------------------------------------------------
# Test factories
# ---------------------------------------------------------------------------

def _plan_with_actions() -> Plan:
    return Plan(
        plan_version=1,
        generated_at=datetime.now(UTC),
        source_discovery={},
        intent={},
        actions=[{"id": "a1"}],  # minimal placeholder
    )


def _empty_plan() -> Plan:
    return Plan(
        plan_version=1,
        generated_at=datetime.now(UTC),
        source_discovery={},
        intent={},
        actions=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_fails_when_plan_has_no_actions(tmp_path: Path) -> None:
    validator = MaterializationValidator(
        plan=_empty_plan(),
        target_root=tmp_path / "target",
    )

    with pytest.raises(MaterializationValidationError):
        validator.validate()


def test_allows_nonexistent_target_directory(tmp_path: Path) -> None:
    validator = MaterializationValidator(
        plan=_plan_with_actions(),
        target_root=tmp_path / "target",
    )

    # Should not raise
    validator.validate()


def test_fails_if_target_root_exists_and_is_file(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("not a directory", encoding="utf-8")

    validator = MaterializationValidator(
        plan=_plan_with_actions(),
        target_root=target,
    )

    with pytest.raises(MaterializationValidationError):
        validator.validate()


def test_allows_existing_target_directory(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    validator = MaterializationValidator(
        plan=_plan_with_actions(),
        target_root=target,
    )

    # Should not raise
    validator.validate()