"""
Tests for materialization layout rules.

These tests validate that layout mapping is:
- deterministic
- conservative (safe)
- policy-driven
- consistent with default DITA package conventions

No filesystem mutation is required for these tests.
"""

from pathlib import Path

import pytest

from dita_package_processor.materialization.layout import (
    DefaultDitaLayoutPolicy,
    LayoutError,
    TargetLayout,
)


def test_rejects_absolute_paths(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)
    with pytest.raises(LayoutError):
        layout.resolve(rel_path=Path("/etc/passwd"))


def test_rejects_path_traversal(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)
    with pytest.raises(LayoutError):
        layout.resolve(rel_path=Path("../evil.dita"))


def test_maps_are_flattened_to_target_root(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out1 = layout.resolve(rel_path=Path("maps/main.ditamap"))
    out2 = layout.resolve(rel_path=Path("main.ditamap"))

    assert out1 == tmp_path / "main.ditamap"
    assert out2 == tmp_path / "main.ditamap"


def test_topics_go_under_topics_dir(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out1 = layout.resolve(rel_path=Path("content/a.dita"))
    out2 = layout.resolve(rel_path=Path("a.dita"))

    assert out1 == tmp_path / "topics" / "a.dita"
    assert out2 == tmp_path / "topics" / "a.dita"


def test_topics_preserve_topics_subtree(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out = layout.resolve(rel_path=Path("topics/ch1/intro.dita"))
    assert out == tmp_path / "topics" / "ch1" / "intro.dita"


def test_media_defaults_to_media_flattened(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out = layout.resolve(rel_path=Path("assets/logo.png"))
    assert out == tmp_path / "media" / "logo.png"


def test_media_preserves_media_subtree(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out = layout.resolve(rel_path=Path("media/images/logo.png"))
    assert out == tmp_path / "media" / "images" / "logo.png"


def test_images_subtree_is_nested_under_media_images(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    out = layout.resolve(rel_path=Path("images/icons/x.svg"))
    assert out == tmp_path / "media" / "images" / "icons" / "x.svg"


def test_deterministic_mapping(tmp_path: Path) -> None:
    layout = TargetLayout(target_root=tmp_path)

    rel = Path("random/thing.pdf")
    out1 = layout.resolve(rel_path=rel)
    out2 = layout.resolve(rel_path=rel)

    assert out1 == out2


def test_custom_policy_can_be_injected(tmp_path: Path) -> None:
    class _Policy(DefaultDitaLayoutPolicy):
        def map_relative_path(self, rel_path: Path) -> Path:
            # Everything goes to media/, flattened.
            return Path("media") / rel_path.name

    layout = TargetLayout(target_root=tmp_path, policy=_Policy())

    out = layout.resolve(rel_path=Path("topics/a.dita"))
    assert out == tmp_path / "media" / "a.dita"