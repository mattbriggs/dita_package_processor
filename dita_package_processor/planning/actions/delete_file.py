"""
Filesystem action: delete_file

Executes a single explicit file deletion.

DESIGN RULES
------------
Execution layer:
    • performs mutation only
    • never guesses paths
    • never performs discovery
    • never infers roots

Planning layer:
    • must provide target paths relative to the sandbox root

Safety guarantees:
    • deletes exactly one file
    • refuses directories
    • refuses paths outside sandbox
    • fails loudly on invalid input
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Execution
# =============================================================================


def delete_file_action(
    action: PlanAction,
    *,
    sandbox_root: Path,
    dry_run: bool = False,
) -> None:
    """
    Execute a ``delete_file`` action.

    Parameters
    ----------
    action : PlanAction
        Declarative action describing the deletion.

    sandbox_root : Path
        Root directory of execution sandbox.
        All mutations must occur beneath this directory.

    dry_run : bool, default=False
        If True, logs intent but performs no deletion.

    Raises
    ------
    ValueError
        If parameters are missing, invalid, or unsafe.

    FileNotFoundError
        If the target file does not exist.

    Notes
    -----
    Execution is intentionally conservative:

    • exactly one file
    • no directories
    • no traversal outside sandbox
    """

    params: dict[str, Any] = action.parameters or {}

    if "target_path" not in params:
        raise ValueError("delete_file action requires parameter: target_path")

    # -------------------------------------------------------------------------
    # Resolve path safely inside sandbox
    # -------------------------------------------------------------------------

    target_rel = Path(params["target_path"])
    target_abs = (sandbox_root / target_rel).resolve()

    sandbox_root = sandbox_root.resolve()

    LOGGER.debug(
        "delete_file | id=%s target=%s dry_run=%s",
        action.id,
        target_abs,
        dry_run,
    )

    # -------------------------------------------------------------------------
    # Safety checks
    # -------------------------------------------------------------------------

    if not str(target_abs).startswith(str(sandbox_root)):
        raise ValueError(
            f"Refusing to delete outside sandbox: {target_abs}"
        )

    if not target_abs.exists():
        raise FileNotFoundError(f"Target file does not exist: {target_abs}")

    if not target_abs.is_file():
        raise ValueError(f"Target path is not a file: {target_abs}")

    # -------------------------------------------------------------------------
    # Execute
    # -------------------------------------------------------------------------

    if dry_run:
        LOGGER.info("DRY-RUN delete_file: %s", target_abs)
        return

    target_abs.unlink()

    LOGGER.info("Deleted file: %s", target_abs)