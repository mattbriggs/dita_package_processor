"""
Execution dispatcher.

The dispatcher is responsible for:

- Receiving a validated plan dictionary
- Executing actions in deterministic order via an Executor
- Collecting ExecutionActionResult objects
- Emitting an ExecutionReport

It performs:
    - NO planning
    - NO handler resolution
    - NO filesystem logic
    - NO registry inspection

The dispatcher owns plan iteration and structural validation.

The executor owns single-action execution.

This module is intentionally minimal and deterministic.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Protocol

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

LOGGER = logging.getLogger(__name__)

__all__ = [
    "ExecutionDispatchError",
    "ExecutionDispatcher",
]


# =============================================================================
# Exceptions
# =============================================================================


class ExecutionDispatchError(RuntimeError):
    """
    Raised when the execution plan is structurally invalid.

    This indicates a contract violation between planning and execution.
    """


# =============================================================================
# Executor Protocol
# =============================================================================


class ExecutorProtocol(Protocol):
    """
    Minimal protocol for executors consumed by ExecutionDispatcher.

    Executors must implement:

        execute(action: Dict[str, Any]) -> ExecutionActionResult
    """

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        ...


# =============================================================================
# Dispatcher
# =============================================================================


class ExecutionDispatcher:
    """
    Deterministic plan dispatcher.
    """

    def __init__(self, executor: ExecutorProtocol) -> None:
        """
        Initialize dispatcher with executor.
        """
        if not callable(getattr(executor, "execute", None)):
            raise TypeError(
                "executor must implement execute(action: dict)"
            )

        self._executor = executor

        LOGGER.debug(
            "ExecutionDispatcher initialized executor=%s",
            executor.__class__.__name__,
        )

    def dispatch(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
        dry_run: bool,
    ) -> ExecutionReport:
        """
        Execute all actions sequentially.
        """
        LOGGER.info(
            "Dispatch start execution_id=%s dry_run=%s",
            execution_id,
            dry_run,
        )

        actions = plan.get("actions")

        if not isinstance(actions, list):
            LOGGER.error("Plan missing 'actions' list")
            raise ExecutionDispatchError(
                "Plan must contain an 'actions' list"
            )

        results: List[ExecutionActionResult] = []
        started_at = datetime.now(UTC)

        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                LOGGER.error("Action[%d] is not a dictionary", index)
                raise ExecutionDispatchError(
                    f"Action[{index}] must be a dictionary"
                )

            action_id = str(action.get("id", "<unknown>"))

            LOGGER.debug(
                "Dispatching action index=%d id=%s",
                index,
                action_id,
            )

            try:
                result = self._executor.execute(action)

                if not isinstance(result, ExecutionActionResult):
                    raise ExecutionDispatchError(
                        f"Executor returned invalid result type "
                        f"for action_id={action_id}"
                    )

            except Exception as exc:  # noqa: BLE001
                LOGGER.exception(
                    "Executor failure id=%s",
                    action_id,
                )

                result = ExecutionActionResult(
                    action_id=action_id,
                    status="failed",
                    handler=self._executor.__class__.__name__,
                    dry_run=dry_run,
                    message="Executor crashed during action execution",
                    error=str(exc),
                    error_type="executor_error",
                )

                results.append(result)
                break

            results.append(result)

        finished_at = datetime.now(UTC)

        report = ExecutionReport.create(
            execution_id=execution_id,
            dry_run=dry_run,
            results=results,
            started_at=started_at,
            finished_at=finished_at,
            discovery=self._derive_discovery_summary(plan),
        )

        LOGGER.info(
            "Dispatch complete execution_id=%s total=%d",
            execution_id,
            len(results),
        )

        return report

    # -------------------------------------------------------------------------
    # Discovery summary derivation
    # -------------------------------------------------------------------------

    @staticmethod
    def _derive_discovery_summary(plan: Dict[str, Any]) -> Dict[str, int]:
        """
        Resolve discovery counts for execution reporting.

        Preferred source is an explicit discovery section on the plan.
        Fallbacks are deterministic and best-effort only.
        """
        explicit = ExecutionDispatcher._coerce_discovery_summary(
            plan.get("discovery")
        )
        if explicit is not None:
            return explicit

        source_discovery = plan.get("source_discovery")
        if isinstance(source_discovery, dict):
            from_source = ExecutionDispatcher._coerce_discovery_summary(
                source_discovery.get("summary")
            )
            if from_source is not None:
                return from_source

            from_source = ExecutionDispatcher._coerce_discovery_summary(
                source_discovery
            )
            if from_source is not None:
                return from_source

        from_summary = ExecutionDispatcher._coerce_discovery_summary(
            plan.get("summary")
        )
        if from_summary is not None:
            return from_summary

        artifacts = plan.get("artifacts")
        if isinstance(artifacts, list):
            discovered = {
                "maps": 0,
                "topics": 0,
                "media": 0,
                "missing_references": 0,
                "external_references": 0,
            }
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    continue
                artifact_type = artifact.get("artifact_type")
                if artifact_type == "map":
                    discovered["maps"] += 1
                elif artifact_type == "topic":
                    discovered["topics"] += 1
                elif artifact_type == "media":
                    discovered["media"] += 1
            return discovered

        actions = plan.get("actions")
        if isinstance(actions, list):
            discovered = {
                "maps": 0,
                "topics": 0,
                "media": 0,
                "missing_references": 0,
                "external_references": 0,
            }
            for action in actions:
                if not isinstance(action, dict):
                    continue
                action_type = action.get("type")
                if action_type == "copy_map":
                    discovered["maps"] += 1
                elif action_type == "copy_topic":
                    discovered["topics"] += 1
                elif action_type == "copy_media":
                    discovered["media"] += 1
            return discovered

        return {
            "maps": 0,
            "topics": 0,
            "media": 0,
            "missing_references": 0,
            "external_references": 0,
        }

    @staticmethod
    def _coerce_discovery_summary(
        payload: Any,
    ) -> Dict[str, int] | None:
        """
        Coerce any compatible summary object into the strict discovery shape.
        """
        if not isinstance(payload, dict):
            return None

        aliases = {
            "maps": ("maps", "map_count"),
            "topics": ("topics", "topic_count"),
            "media": ("media", "media_count"),
            "missing_references": ("missing_references",),
            "external_references": ("external_references",),
        }

        if not any(
            any(alias in payload for alias in alias_set)
            for alias_set in aliases.values()
        ):
            return None

        normalized: Dict[str, int] = {}
        for key, alias_set in aliases.items():
            raw_value: Any = 0
            for alias in alias_set:
                if alias in payload:
                    raw_value = payload[alias]
                    break

            try:
                coerced = int(raw_value)
            except (TypeError, ValueError):
                coerced = 0

            normalized[key] = max(0, coerced)

        return normalized
