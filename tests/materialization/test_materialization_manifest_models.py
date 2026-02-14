"""
Tests for materialization manifest models.

These tests validate that materialization models are:
- immutable
- serializable
- deterministic
- structurally explicit
- collision-safe by construction

They do NOT test filesystem behavior.
"""

from pathlib import Path

import pytest

from dita_package_processor.materialization.models import (
    MaterializedFile,
    MaterializationManifest,
)


# ----------------------------------------------------------------------
# MaterializedFile
# ----------------------------------------------------------------------


def test_materialized_file_to_dict(tmp_path: Path) -> None:
    target_root = tmp_path / "out"
    file_path = target_root / "maps" / "main.ditamap"

    mf = MaterializedFile(
        path=file_path,
        role="MAIN_MAP",
        source_action_id="copy-map-1",
        layout_metadata={"format": "dita"},
    )

    payload = mf.to_dict()

    assert payload["path"] == str(file_path)
    assert payload["role"] == "MAIN_MAP"
    assert payload["source_action_id"] == "copy-map-1"
    assert payload["layout_metadata"]["format"] == "dita"


def test_materialized_file_is_immutable(tmp_path: Path) -> None:
    mf = MaterializedFile(
        path=tmp_path / "a.dita",
        source_action_id="a1",
    )

    with pytest.raises(Exception):
        mf.path = tmp_path / "b.dita"


# ----------------------------------------------------------------------
# MaterializationManifest
# ----------------------------------------------------------------------


def test_materialization_manifest_to_dict(tmp_path: Path) -> None:
    target_root = tmp_path / "out"

    files = [
        MaterializedFile(path=target_root / "maps" / "main.ditamap"),
        MaterializedFile(path=target_root / "topics" / "intro.dita"),
    ]

    manifest = MaterializationManifest(
        target_root=target_root,
        files=files,
        metadata={"profile": "publish"},
    )

    payload = manifest.to_dict()

    assert payload["target_root"] == str(target_root)
    assert len(payload["files"]) == 2
    assert payload["metadata"]["profile"] == "publish"


def test_manifest_rejects_relative_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        MaterializationManifest(
            target_root=tmp_path,
            files=[
                MaterializedFile(path=Path("relative/path.dita")),
            ],
        )


def test_manifest_rejects_paths_outside_target_root(tmp_path: Path) -> None:
    target_root = tmp_path / "out"

    with pytest.raises(ValueError):
        MaterializationManifest(
            target_root=target_root,
            files=[
                MaterializedFile(path=tmp_path / "elsewhere" / "file.dita"),
            ],
        )


def test_manifest_rejects_collisions(tmp_path: Path) -> None:
    target_root = tmp_path / "out"
    path = target_root / "topics" / "a.dita"

    with pytest.raises(ValueError):
        MaterializationManifest(
            target_root=target_root,
            files=[
                MaterializedFile(path=path, source_action_id="a1"),
                MaterializedFile(path=path, source_action_id="a2"),
            ],
        )


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    target_root = tmp_path / "out"

    files = [
        MaterializedFile(path=target_root / "a.dita"),
        MaterializedFile(path=target_root / "b.dita"),
    ]

    m1 = MaterializationManifest(target_root=target_root, files=files)
    m2 = MaterializationManifest(target_root=target_root, files=files)

    assert m1.to_dict() == m2.to_dict()