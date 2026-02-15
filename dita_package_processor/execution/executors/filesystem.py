"""
FilesystemExecutor.

Concrete executor that performs real filesystem mutations.

Responsibilities
----------------
- Own all filesystem access
- Resolve relative source paths using source_root
- Enforce sandbox boundaries for writes
- Enforce mutation policies
- Resolve handlers through the registry
- Delegate real work to handlers
- Translate failures into ExecutionActionResult

Safety pipeline
---------------
source_root → sandbox → policy → handler → result

Notes
-----
This is the ONLY component allowed to touch disk.

Handlers must never guess paths or use CWD.
All path resolution flows through this executor.
"""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Protocol

from dita_package_processor.execution.bootstrap import get_registry
from dita_package_processor.execution.dispatcher import ExecutionDispatcher
from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
    OverwritePolicy,
)
from dita_package_processor.execution.safety.sandbox import Sandbox

LOGGER = logging.getLogger(__name__)

__all__ = ["FilesystemExecutor"]


# =============================================================================
# Registry protocol
# =============================================================================


class RegistryProtocol(Protocol):
    """Minimal protocol for handler registry."""

    def get_handler(self, action_type: str) -> Any:  # pragma: no cover
        ...


# =============================================================================
# Executor
# =============================================================================


class FilesystemExecutor:
    """
    Executor that performs real filesystem mutations.

    Parameters
    ----------
    source_root : Path
        Root directory containing source artifacts.
    sandbox_root : Path
        Root directory where writes are permitted.
    apply : bool
        Whether mutation is allowed (dry-run vs real execution).
    """

    # ------------------------------------------------------------------
    # init
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        source_root: Path,
        sandbox_root: Path,
        apply: bool,
    ) -> None:
        self.source_root = Path(source_root).resolve()
        self.sandbox = Sandbox(Path(sandbox_root).resolve())
        self.apply = apply

        self.policy = MutationPolicy(
            overwrite=OverwritePolicy.REPLACE
            if apply
            else OverwritePolicy.DENY
        )

        self._registry: RegistryProtocol = get_registry()
        self._dispatcher = ExecutionDispatcher(self)

        LOGGER.debug(
            "FilesystemExecutor initialized "
            "source_root=%s sandbox_root=%s apply=%s",
            self.source_root,
            self.sandbox.root,
            self.apply,
        )

    # =========================================================================
    # PLAN ENTRY
    # =========================================================================

    def run(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
    ) -> ExecutionReport:
        """
        Execute full plan.

        Parameters
        ----------
        execution_id : str
        plan : dict

        Returns
        -------
        ExecutionReport
        """
        LOGGER.info(
            "Filesystem execution start id=%s source=%s sandbox=%s",
            execution_id,
            self.source_root,
            self.sandbox.root,
        )

        report = self._dispatcher.dispatch(
            execution_id=execution_id,
            plan=plan,
            dry_run=not self.apply,
        )

        LOGGER.info(
            "Filesystem execution complete id=%s actions=%d",
            execution_id,
            len(getattr(report, "results", [])),
        )

        return report

    # =========================================================================
    # ACTION EXECUTION
    # =========================================================================

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        """
        Execute a single action.

        This method:
        1. resolves handler
        2. injects source_root + sandbox + policy
        3. delegates work
        4. normalizes result to execution context
        """
        action_id = str(action.get("id", "<unknown>"))
        action_type = action.get("type")

        LOGGER.debug(
            "Executing action id=%s type=%s",
            action_id,
            action_type,
        )

        try:
            handler = self._resolve_handler(action_type)

            handler_instance = (
                handler() if inspect.isclass(handler) else handler
            )

            result = self._invoke_handler(
                handler=handler_instance,
                action=action,
            )

        except PolicyViolationError as exc:
            LOGGER.error("Policy violation id=%s: %s", action_id, exc)

            result = ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=not self.apply,
                message=str(exc),
                error=str(exc),
                error_type="policy_violation",
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Executor crash id=%s", action_id)

            result = ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=not self.apply,
                message="Executor crash",
                error=str(exc),
                error_type="executor_error",
            )

        # ------------------------------------------------------------------
        # Normalize dry-run semantics
        # ------------------------------------------------------------------

        if not self.apply and result.dry_run is False:
            LOGGER.debug(
                "Normalizing dry-run for action id=%s",
                action_id,
            )

            result = ExecutionActionResult(
                action_id=result.action_id,
                status=result.status,
                handler=result.handler,
                dry_run=True,
                message=result.message,
                error=result.error,
                error_type=result.error_type,
                metadata=result.metadata,
            )

        return result

    # =========================================================================
    # handler plumbing
    # =========================================================================

    def _resolve_handler(self, action_type: str) -> Any:
        """Resolve handler from registry."""
        return self._registry.get_handler(action_type)

    # ------------------------------------------------------------------

    def _invoke_handler(
        self,
        *,
        handler: Any,
        action: Dict[str, Any],
    ) -> ExecutionActionResult:
        """
        Invoke handler with supported kwargs.

        Handlers may accept:
        - action
        - source_root
        - sandbox
        - policy
        """
        fn = self._get_callable(handler)

        sig = inspect.signature(fn)
        params = sig.parameters

        kwargs: Dict[str, Any] = {}

        if "action" in params:
            kwargs["action"] = action
        if "source_root" in params:
            kwargs["source_root"] = self.source_root
        if "sandbox" in params:
            kwargs["sandbox"] = self.sandbox
        if "policy" in params:
            kwargs["policy"] = self.policy

        LOGGER.debug(
            "Invoking handler=%s kwargs=%s",
            handler.__class__.__name__,
            sorted(kwargs.keys()),
        )

        result = fn(**kwargs)

        if not isinstance(result, ExecutionActionResult):
            raise TypeError(
                f"{handler.__class__.__name__} "
                "must return ExecutionActionResult"
            )

        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _get_callable(handler: Any) -> Callable[..., Any]:
        """Return execute() or handle()."""
        if hasattr(handler, "execute"):
            return handler.execute
        if hasattr(handler, "handle"):
            return handler.handle

        raise AttributeError(
            f"{handler.__class__.__name__} missing execute()/handle()"
        )