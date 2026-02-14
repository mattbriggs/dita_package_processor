"""
Tests for the path normalization utilities.

These tests verify that:
- Relative paths are resolved correctly
- ./ and ../ segments are normalized
- Absolute paths are treated as package-root anchored
- Escaping the package root raises an error

Path normalization is symbolic and must not depend on filesystem existence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.discovery.path_normalizer import (
    normalize_reference_path,
)


def test_simple_relative_path(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    source = package / "topics" / "a.dita"

    normalized = normalize_reference_path(
        source_path=source,
        reference="b.dita",
        package_root=package,
    )

    assert normalized == "topics/b.dita"


def test_dot_relative_path() -> None:
    package = Path("/pkg")
    source = package / "topics" / "a.dita"

    normalized = normalize_reference_path(
        source_path=source,
        reference="./b.dita",
        package_root=package,
    )

    assert normalized == "topics/b.dita"


def test_parent_relative_path() -> None:
    package = Path("/pkg")
    source = package / "topics" / "sub" / "a.dita"

    normalized = normalize_reference_path(
        source_path=source,
        reference="../b.dita",
        package_root=package,
    )

    assert normalized == "topics/b.dita"


def test_complex_relative_path() -> None:
    package = Path("/pkg")
    source = package / "topics" / "a.dita"

    normalized = normalize_reference_path(
        source_path=source,
        reference="sub/.././b.dita",
        package_root=package,
    )

    assert normalized == "topics/b.dita"


def test_absolute_path_is_package_root_anchored() -> None:
    package = Path("/pkg")
    source = package / "topics" / "a.dita"

    normalized = normalize_reference_path(
        source_path=source,
        reference="/topics/b.dita",
        package_root=package,
    )

    assert normalized == "topics/b.dita"


def test_path_escaping_package_root_raises_error() -> None:
    package = Path("/pkg")
    source = package / "topics" / "a.dita"

    with pytest.raises(ValueError):
        normalize_reference_path(
            source_path=source,
            reference="../../../etc/passwd",
            package_root=package,
        )