"""
Semantic execution handler for deleting a file.

Although categorized as "semantic", this handler performs real filesystem
mutation and therefore MUST obey the same safety guarantees as filesystem
handlers.

It NEVER:
- resolves paths relative to cwd
- deletes outside the sandbox
- bypasses mutation policy

All paths are resolved through the executor context.

Design principles
----------------
- Deterministic behavior
- Explicit path resolution
- Idempotent deletes
- Side-effect free in dry-run mode
- Forensic logging only
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
)

LOGGER = logging.getLogger(__name__)


class DeleteFileHandler(ExecutionHandler):
    """
    Execution handler for ``delete_file``.

    Deletes:

        sandbox_root / target_path

    Idempotent behavior:
        - missing → skipped
        - existing → deleted

    Only files are deleted. Directories are rejected.
    """

    action_type = "delete_file"

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        action: Dict[str, Any],
        sandbox: Sandbox,
        policy: MutationPolicy,
    ) -> ExecutionActionResult:
        """
        Execute a ``delete_file`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            rel_target = Path(params["target_path"])
        except KeyError as exc:
            LOGGER.error(
                "delete_file id=%s missing parameter: target_path",
                action_id,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="Missing required parameter: target_path",
                error=str(exc),
            )

        # -------------------------------------------------
        # Resolve path (sandbox-controlled)
        # -------------------------------------------------

        target_path = sandbox.resolve(rel_target)

        LOGGER.info(
            "delete_file id=%s dry_run=%s target=%s",
            action_id,
            dry_run,
            target_path,
        )

        # -------------------------------------------------
        # Dry-run
        # -------------------------------------------------

        if dry_run:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=True,
                message=f"Dry-run: would delete file if present: {target_path}",
            )

        # -------------------------------------------------
        # Idempotence (safe no-op)
        # -------------------------------------------------

        if not target_path.exists():
            LOGGER.info(
                "delete_file id=%s target missing → skipped",
                action_id,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"File not present: {target_path}",
            )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not target_path.is_file():
            LOGGER.error(
                "delete_file id=%s target not a file: %s",
                action_id,
                target_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Target is not a file: {target_path}",
                error="NotAFileError",
            )

        # -------------------------------------------------
        # Policy enforcement
        # -------------------------------------------------

        try:
            policy.validate_target(target_path)
        except PolicyViolationError as exc:
            LOGGER.error(
                "delete_file id=%s policy violation for target: %s",
                action_id,
                target_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=str(exc),
                error=exc.failure_type,
            )

        # -------------------------------------------------
        # Delete
        # -------------------------------------------------

        try:
            target_path.unlink()

            LOGGER.info(
                "delete_file succeeded id=%s deleted=%s",
                action_id,
                target_path,
            )

            return ExecutionActionResult(
                action_id=action_id,
                status="success",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Deleted file: {target_path}",
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("delete_file failed id=%s", action_id)

            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="delete_file execution failed",
                error=str(exc),
            )