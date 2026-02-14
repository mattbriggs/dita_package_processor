"""
Tests for filesystem mutation policies.

These tests lock the behavior of MutationPolicy:

- New files are always allowed.
- Existing files are controlled by OverwritePolicy.
- DENY blocks overwrite with a classified PolicyViolationError.
- REPLACE allows overwrite.
- SKIP blocks overwrite with a classified PolicyViolationError.
- PolicyViolationError exposes semantic failure information.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    OverwritePolicy,
    PolicyViolationError,
)


def test_policy_allows_new_file(tmp_path: Path) -> None:
    """
    New files must always be allowed regardless of overwrite policy.
    """
    policy = MutationPolicy(OverwritePolicy.DENY)

    target = tmp_path / "new.txt"
    policy.validate_target(target)  # Must not raise


def test_policy_deny_blocks_existing_file(tmp_path: Path) -> None:
    """
    DENY must block writes to existing files and raise PolicyViolationError.
    """
    policy = MutationPolicy(OverwritePolicy.DENY)

    target = tmp_path / "file.txt"
    target.write_text("existing")

    with pytest.raises(PolicyViolationError) as excinfo:
        policy.validate_target(target)

    exc = excinfo.value
    assert exc.failure_type == "policy_violation"
    assert exc.target == target
    assert "Overwrite denied" in str(exc)


def test_policy_replace_allows_existing_file(tmp_path: Path) -> None:
    """
    REPLACE must allow overwriting existing files.
    """
    policy = MutationPolicy(OverwritePolicy.REPLACE)

    target = tmp_path / "file.txt"
    target.write_text("existing")

    policy.validate_target(target)  # Must not raise


def test_policy_skip_blocks_existing_file(tmp_path: Path) -> None:
    """
    SKIP must block writes to existing files and raise PolicyViolationError.
    """
    policy = MutationPolicy(OverwritePolicy.SKIP)

    target = tmp_path / "file.txt"
    target.write_text("existing")

    with pytest.raises(PolicyViolationError) as excinfo:
        policy.validate_target(target)

    exc = excinfo.value
    assert exc.failure_type == "policy_violation"
    assert exc.target == target
    assert "skipped" in str(exc).lower()


def test_policy_skip_does_not_block_new_file(tmp_path: Path) -> None:
    """
    SKIP must not block creation of new files.
    """
    policy = MutationPolicy(OverwritePolicy.SKIP)

    target = tmp_path / "new.txt"
    policy.validate_target(target)  # Must not raise


def test_policy_requires_path_type() -> None:
    """
    validate_target must reject non-Path arguments explicitly.
    """
    policy = MutationPolicy(OverwritePolicy.DENY)

    with pytest.raises(TypeError):
        policy.validate_target("not-a-path")  # type: ignore[arg-type]


def test_policy_requires_valid_overwrite_policy() -> None:
    """
    MutationPolicy must reject invalid overwrite policy types.
    """
    with pytest.raises(TypeError):
        MutationPolicy("deny")  # type: ignore[arg-type]