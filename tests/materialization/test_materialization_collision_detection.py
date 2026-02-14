"""
Tests for materialization collision detection.

These tests validate that the materialization layer detects
filesystem target conflicts before execution occurs.
"""

from pathlib import Path

import pytest

from dita_package_processor.materialization.collision import (
    CollisionDetector,
    MaterializationCollisionError,
    TargetArtifact,
)


def test_no_collision_passes(tmp_path: Path) -> None:
    artifacts = [
        TargetArtifact(
            path=tmp_path / "a" / "one.dita",
            source_action_id="a1",
        ),
        TargetArtifact(
            path=tmp_path / "b" / "two.dita",
            source_action_id="a2",
        ),
    ]

    detector = CollisionDetector(artifacts=artifacts)

    detector.detect()  # should not raise


def test_duplicate_target_path_fails(tmp_path: Path) -> None:
    shared = tmp_path / "dup" / "same.dita"

    artifacts = [
        TargetArtifact(
            path=shared,
            source_action_id="a1",
        ),
        TargetArtifact(
            path=shared,
            source_action_id="a2",
        ),
    ]

    detector = CollisionDetector(artifacts=artifacts)

    with pytest.raises(MaterializationCollisionError) as exc:
        detector.detect()

    message = str(exc.value)
    assert "Duplicate target path" in message
    assert "same.dita" in message
    assert "a1" in message or "a2" in message


def test_path_resolution_detects_collision(tmp_path: Path) -> None:
    artifacts = [
        TargetArtifact(
            path=tmp_path / "x" / ".." / "y" / "file.dita",
            source_action_id="a1",
        ),
        TargetArtifact(
            path=tmp_path / "y" / "file.dita",
            source_action_id="a2",
        ),
    ]

    detector = CollisionDetector(artifacts=artifacts)

    with pytest.raises(MaterializationCollisionError):
        detector.detect()