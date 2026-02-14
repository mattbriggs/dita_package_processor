"""
Filesystem execution handler for copying media assets.

This handler performs a literal, byte-for-byte copy of any media artifact
(images, video, audio, PDFs, etc.) from a source path to a target path.

It NEVER:
- uses current working directory
- guesses absolute paths
- interprets content
- performs semantic logic

All path resolution is explicitly provided by the executor.

Design principles
----------------
- Deterministic
- Pure transport only
- Side-effect free in dry-run mode
- Strict sandbox + policy enforcement
- Forensic logging only
"""

from __future__ import annotations

from email import policy
import logging
import shutil
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.policies import MutationPolicy, PolicyViolationError
from dita_package_processor.execution.safety.sandbox import Sandbox

LOGGER = logging.getLogger(__name__)

__all__ = ["CopyMediaHandler"]


# ============================================================================
# Handler
# ============================================================================


class CopyMediaHandler(ExecutionHandler):
    """
    Execution handler for ``copy_media``.

    Copies:

        source_root / source_path

    to:

        sandbox_root / target_path

    Notes
    -----
    * Parameters MUST be relative paths.
    * Executor provides all filesystem context.
    * This handler performs no semantic interpretation.
    """

    action_type = "copy_media"

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
        Execute a ``copy_media`` action.

        Parameters
        ----------
        action:
            Normalized execution action dictionary.
        source_root:
            Root directory containing source artifacts.
        sandbox:
            Sandbox enforcing write boundaries.
        policy:
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
                "copy_media id=%s missing parameter: %s",
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
                "copy_media id=%s source escapes source_root: %s",
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
            "copy_media id=%s dry_run=%s source=%s target=%s",
            action_id,
            dry_run,
            source_path,
            target_path,
        )

        # -------------------------------------------------
        # Dry-run behavior
        # -------------------------------------------------

        if dry_run:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=True,
                message="Dry-run: copy_media skipped",
            )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not source_path.exists() or not source_path.is_file():
            LOGGER.error(
                "copy_media id=%s invalid source file: %s",
                action_id,
                source_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Source media does not exist or is not a file: {source_path}",
                error="InvalidSource",
            )

        # -------------------------------------------------
        # Policy enforcement
        # -------------------------------------------------

        try:
            policy.validate_target(target_path)
        except PolicyViolationError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=str(exc),
                error=exc.failure_type,
            )

        # -------------------------------------------------
        # Copy operation
        # -------------------------------------------------

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

            LOGGER.info(
                "copy_media succeeded id=%s %s → %s",
                action_id,
                source_path,
                target_path,
            )

            return ExecutionActionResult(
                action_id=action_id,
                status="success",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Copied media to {target_path}",
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("copy_media failed id=%s", action_id)

            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="copy_media execution failed",
                error=str(exc),
            )