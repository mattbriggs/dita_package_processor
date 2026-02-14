from __future__ import annotations

from pathlib import Path
import pytest

from dita_package_processor.execution.safety.sandbox import (
    Sandbox,
    SandboxViolationError,
)


def test_sandbox_accepts_valid_root(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)
    assert sandbox.root == tmp_path.resolve()


def test_sandbox_rejects_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(SandboxViolationError):
        Sandbox(missing)


def test_sandbox_rejects_file_as_root(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("nope")

    with pytest.raises(SandboxViolationError):
        Sandbox(file_path)


def test_resolve_relative_path_inside_sandbox(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)

    resolved = sandbox.resolve(Path("data/file.txt"))
    assert resolved == (tmp_path / "data/file.txt").resolve()


def test_resolve_absolute_path_inside_sandbox(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)

    inside = tmp_path / "subdir" / "file.txt"
    inside.parent.mkdir(parents=True)

    resolved = sandbox.resolve(inside)
    assert resolved == inside.resolve()


def test_resolve_rejects_path_outside_sandbox(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)

    outside = tmp_path.parent / "escape.txt"

    with pytest.raises(SandboxViolationError):
        sandbox.resolve(outside)


def test_resolve_rejects_traversal_attempt(tmp_path: Path) -> None:
    sandbox = Sandbox(tmp_path)

    traversal = Path("../escape.txt")

    with pytest.raises(SandboxViolationError):
        sandbox.resolve(traversal)