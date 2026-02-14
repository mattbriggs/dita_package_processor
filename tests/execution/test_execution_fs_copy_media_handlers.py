"""
Tests for filesystem media copy handlers.

These tests verify that handlers perform real filesystem operations:

- Byte-for-byte copy
- Parent directory creation
- Correct ExecutionActionResult reporting
"""

from pathlib import Path
from uuid import uuid4

from dita_package_processor.execution.handlers.fs.fs_copy_media import (
    CopyMediaHandler,
)
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    OverwritePolicy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _context(tmp_path: Path):
    """
    Build executor-style context objects.

    Mirrors how FilesystemExecutor constructs handler inputs.
    """
    source_root = tmp_path
    sandbox = Sandbox(tmp_path)
    policy = MutationPolicy(OverwritePolicy.REPLACE)
    return source_root, sandbox, policy


def _make_action(source: Path, target: Path, *, dry_run: bool = False) -> dict:
    """
    Build normalized action dictionary compatible with ExecutionHandler.execute().

    Paths must be RELATIVE to source_root/sandbox.
    """
    root = source.parent  # tmp_path

    return {
        "id": str(uuid4()),
        "type": "copy_media",
        "parameters": {
            "source_path": str(source.relative_to(root)),
            "target_path": str(target.relative_to(root)),
        },
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_copy_media_byte_for_byte(tmp_path: Path) -> None:
    """
    Copying a media file must produce an identical file.
    """
    source = tmp_path / "source.png"
    target = tmp_path / "out" / "target.png"

    content = b"\x89PNG\r\n\x1a\nfakepngdata"
    source.write_bytes(content)

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMediaHandler()

    result = handler.execute(
        action=_make_action(source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.read_bytes() == content
    assert result.status == "success"


def test_copy_media_creates_parent_directories(tmp_path: Path) -> None:
    """
    Parent directories must be created automatically.
    """
    source = tmp_path / "source.jpg"
    target = tmp_path / "deep" / "nested" / "target.jpg"

    source.write_text("binary-ish-content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMediaHandler()

    result = handler.execute(
        action=_make_action(source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.parent.exists()
    assert result.status == "success"


def test_copy_media_dry_run(tmp_path: Path) -> None:
    """
    Dry-run must not mutate the filesystem.
    """
    source = tmp_path / "source.bin"
    target = tmp_path / "target.bin"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMediaHandler()

    result = handler.execute(
        action=_make_action(source, target, dry_run=True),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert not target.exists()
    assert result.status == "skipped"


def test_copy_media_result_metadata(tmp_path: Path) -> None:
    """
    ExecutionActionResult must report correct metadata.
    """
    source = tmp_path / "source.bin"
    target = tmp_path / "target.bin"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyMediaHandler()

    action = _make_action(source, target)

    result = handler.execute(
        action=action,
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert result.action_id == action["id"]
    assert result.handler == "CopyMediaHandler"
    assert result.status == "success"
    assert result.dry_run is False