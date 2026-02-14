"""
Tests for filesystem copy handlers.

These tests verify that handlers perform real filesystem operations:

- Byte-for-byte copy
- Parent directory creation
- Correct ExecutionActionResult reporting

Handlers now require executor context:
    source_root, sandbox, policy

So tests must supply those explicitly.
"""

from pathlib import Path
from uuid import uuid4

from dita_package_processor.execution.handlers.fs.fs_copy_map import CopyMapHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import MutationPolicy, OverwritePolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_action(
    source_root: Path,
    source: Path,
    target: Path,
    *,
    dry_run: bool = False,
) -> dict:
    """
    Build a normalized execution action dictionary compatible with
    ExecutionHandler.execute().
    """
    return {
        "id": str(uuid4()),
        "type": "copy_map",
        "parameters": {
            "source_path": str(source.relative_to(source_root)),
            "target_path": str(target.relative_to(source_root)),
        },
        "dry_run": dry_run,
    }


def _context(tmp_path: Path):
    """
    Build executor context required by handlers.
    """
    sandbox = Sandbox(tmp_path)
    policy = MutationPolicy(overwrite=OverwritePolicy.REPLACE)
    return tmp_path, sandbox, policy


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_copy_map_byte_for_byte(tmp_path: Path) -> None:
    """
    Copying a map must produce an identical file.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "target.ditamap"

    content = b"<map>This is a test</map>"
    source.write_bytes(content)

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMapHandler()

    result = handler.execute(
        action=_make_action(source_root, source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.read_bytes() == content
    assert result.status == "success"


def test_copy_map_creates_parent_directories(tmp_path: Path) -> None:
    """
    Parent directories must be created automatically.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "deep" / "nested" / "target.ditamap"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMapHandler()

    result = handler.execute(
        action=_make_action(source_root, source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.parent.exists()
    assert result.status == "success"


def test_copy_map_dry_run(tmp_path: Path) -> None:
    """
    Dry-run must not mutate the filesystem.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "target.ditamap"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMapHandler()

    result = handler.execute(
        action=_make_action(source_root, source, target, dry_run=True),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert not target.exists()
    assert result.status == "skipped"


def test_copy_map_result_metadata(tmp_path: Path) -> None:
    """
    ExecutionActionResult must report correct metadata.
    """
    source = tmp_path / "source.ditamap"
    target = tmp_path / "target.ditamap"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMapHandler()
    action = _make_action(source_root, source, target)

    result = handler.execute(
        action=action,
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert result.action_id == action["id"]
    assert result.handler == "CopyMapHandler"
    assert result.status == "success"
    assert result.dry_run is False