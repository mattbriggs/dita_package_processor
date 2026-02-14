"""
Tests for filesystem topic copy handler.

Verifies:

- Byte-for-byte copy
- Parent directory creation
- Dry-run safety
- Correct ExecutionActionResult reporting
"""

from pathlib import Path
from uuid import uuid4

from dita_package_processor.execution.handlers.fs.fs_copy_topic import (
    CopyTopicHandler,
)
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    OverwritePolicy,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _context(root: Path):
    """
    Build minimal execution context for handler.

    source_root == sandbox root for tests.
    """
    source_root = root
    sandbox = Sandbox(root)
    policy = MutationPolicy(OverwritePolicy.REPLACE)
    return source_root, sandbox, policy


def _make_action(source: Path, target: Path, *, dry_run: bool = False) -> dict:
    """
    Build normalized execution action.

    Paths MUST be relative to source_root/sandbox.
    """
    root = source.parent

    return {
        "id": str(uuid4()),
        "type": "copy_topic",
        "parameters": {
            "source_path": str(source.relative_to(root)),
            "target_path": str(target.relative_to(root)),
        },
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_copy_topic_byte_for_byte(tmp_path: Path) -> None:
    source = tmp_path / "source.dita"
    target = tmp_path / "out" / "target.dita"

    content = b"<topic>This is a test</topic>"
    source.write_bytes(content)

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyTopicHandler()

    result = handler.execute(
        action=_make_action(source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.read_bytes() == content
    assert result.status == "success"


def test_copy_topic_creates_parent_directories(tmp_path: Path) -> None:
    source = tmp_path / "source.dita"
    target = tmp_path / "deep" / "nested" / "target.dita"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyTopicHandler()

    result = handler.execute(
        action=_make_action(source, target),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert target.exists()
    assert target.parent.exists()
    assert result.status == "success"


def test_copy_topic_dry_run(tmp_path: Path) -> None:
    source = tmp_path / "source.dita"
    target = tmp_path / "target.dita"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyTopicHandler()

    result = handler.execute(
        action=_make_action(source, target, dry_run=True),
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert not target.exists()
    assert result.status == "skipped"


def test_copy_topic_result_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.dita"
    target = tmp_path / "target.dita"

    source.write_text("content")

    source_root, sandbox, policy = _context(tmp_path)

    handler = CopyTopicHandler()

    action = _make_action(source, target)

    result = handler.execute(
        action=action,
        source_root=source_root,
        sandbox=sandbox,
        policy=policy,
    )

    assert result.action_id == action["id"]
    assert result.handler == "CopyTopicHandler"
    assert result.status == "success"
    assert result.dry_run is False