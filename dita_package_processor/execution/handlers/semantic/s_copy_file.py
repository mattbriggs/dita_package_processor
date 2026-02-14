"""
Semantic execution handler for copying arbitrary files.

Despite living in the semantic layer, this handler performs real
filesystem I/O and must obey the same safety rules as filesystem handlers.

It NEVER:
- uses current working directory
- constructs absolute paths directly from parameters
- bypasses sandbox or policy

All resolution is provided explicitly by the executor.

Design principles
----------------
- Deterministic
- Explicit path resolution
- Side-effect free in dry-run mode
- Zero interpretation of file content
- Forensic logging only
"""

from __future__ import annotations

import logging
import shutil
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


class CopyFileHandler(ExecutionHandler):
    """
    Execution handler for ``copy_file``.

    Copies:

        source_root / source_path

    to:

        sandbox_root / target_path

    Both parameters must be relative paths.
    """

    action_type = "copy_file"

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        action: Dict[str, Any],
        source_root: Path,
        sandbox: Sandbox,
        policy: MutationPolicy,
    ) -> ExecutionActionResult:
        """
        Execute a ``copy_file`` action.

        Parameters
        ----------
        action : dict
            Normalized execution action dictionary.
        source_root : Path
            Root directory containing source artifacts.
        sandbox : Sandbox
            Sandbox enforcing write boundaries.
        policy : MutationPolicy
            Mutation / overwrite policy.

        Returns
        -------
        ExecutionActionResult
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            rel_source = Path(params["source_path"])
            rel_target = Path(params["target_path"])
        except KeyError as exc:
            LOGGER.error(
                "copy_file id=%s missing parameter: %s",
                action_id,
                exc,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="Missing required parameters: source_path, target_path",
                error=str(exc),
            )

        # -------------------------------------------------
        # Resolve paths (executor-controlled)
        # -------------------------------------------------

        source_path = (source_root / rel_source).resolve()

        # Prevent path traversal outside source_root
        if not source_path.is_relative_to(source_root):
            LOGGER.error(
                "copy_file id=%s source escapes source_root: %s",
                action_id,
                source_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="source_path escapes source_root",
                error="PathTraversalError",
            )

        target_path = sandbox.resolve(rel_target)

        LOGGER.info(
            "copy_file id=%s dry_run=%s source=%s target=%s",
            action_id,
            dry_run,
            source_path,
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
                message="Dry-run: copy_file skipped",
            )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not source_path.exists() or not source_path.is_file():
            LOGGER.error(
                "copy_file id=%s invalid source file: %s",
                action_id,
                source_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Source file does not exist or is not a file: {source_path}",
                error="InvalidSource",
            )

        # -------------------------------------------------
        # Policy enforcement
        # -------------------------------------------------

        try:
            policy.validate_target(target_path)
        except PolicyViolationError as exc:
            LOGGER.error(
                "copy_file id=%s policy violation for target: %s",
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
        # Copy
        # -------------------------------------------------

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

            LOGGER.info(
                "copy_file succeeded id=%s %s → %s",
                action_id,
                source_path,
                target_path,
            )

            return ExecutionActionResult(
                action_id=action_id,
                status="success",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Copied file to {target_path}",
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("copy_file failed id=%s", action_id)

            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="copy_file execution failed",
                error=str(exc),
            )