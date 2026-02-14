"""
Plan hydration logic.

This module converts a JSON-loaded dictionary into strongly-typed
planning domain models.

Hydration is a strict boundary:

- JSON is untrusted input
- Models are validated, typed contracts
- Errors are explicit and never silent

No filesystem or execution semantics exist here.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dita_package_processor.planning.models import (
    Plan,
    PlanAction,
    PlanIntent,
    PlanSourceDiscovery,
)

LOGGER = logging.getLogger(__name__)


class PlanHydrationError(ValueError):
    """
    Raised when a plan cannot be hydrated into a Plan model.

    This signals malformed, missing, or structurally invalid input.
    """


def hydrate_plan(payload: Dict[str, Any]) -> Plan:
    """
    Hydrate a :class:`Plan` model from a parsed JSON payload.

    This function is a strict deserialization boundary. It assumes:

    - Input is untrusted
    - All required fields must be present
    - Types must be valid or convertible
    - Failures must be explicit and actionable

    :param payload: Parsed JSON dictionary.
    :return: Hydrated :class:`Plan` instance.
    :raises PlanHydrationError: If required fields are missing or invalid.
    """
    LOGGER.debug("Starting plan hydration")

    try:
        plan_version = payload["plan_version"]
        generated_at_raw = payload["generated_at"]
        source = payload["source_discovery"]
        intent = payload["intent"]

        LOGGER.debug("Hydrating plan version=%s", plan_version)

        generated_at = _parse_datetime(generated_at_raw)

        source_discovery = _hydrate_source_discovery(source)
        plan_intent = _hydrate_intent(intent)
        actions = _hydrate_actions(payload.get("actions", []))
        invariants = payload.get("invariants", [])

        plan = Plan(
            plan_version=plan_version,
            generated_at=generated_at,
            source_discovery=source_discovery,
            intent=plan_intent,
            actions=actions,
            invariants=invariants,
        )

        LOGGER.info(
            "Hydrated plan version=%s with %d actions",
            plan.plan_version,
            len(plan.actions),
        )
        return plan

    except KeyError as exc:
        LOGGER.error("Missing required plan field: %s", exc)
        raise PlanHydrationError(
            f"Missing required plan field: {exc}"
        ) from exc

    except Exception as exc:
        LOGGER.exception("Plan hydration failed")
        raise PlanHydrationError(
            f"Plan hydration failed: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_datetime(value: Any) -> datetime:
    """
    Parse an ISO-8601 datetime string.

    :param value: Raw datetime value.
    :return: Parsed datetime.
    :raises PlanHydrationError: If value is invalid.
    """
    if not isinstance(value, str):
        raise PlanHydrationError(
            f"generated_at must be an ISO-8601 string, got {type(value)}"
        )

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise PlanHydrationError(
            f"Invalid generated_at timestamp: {value}"
        ) from exc


def _hydrate_source_discovery(source: Dict[str, Any]) -> PlanSourceDiscovery:
    """
    Hydrate PlanSourceDiscovery.

    :param source: Source discovery payload.
    :return: PlanSourceDiscovery instance.
    """
    try:
        path = Path(source["path"])
        schema_version = source["schema_version"]
        artifact_count = source["artifact_count"]

        LOGGER.debug(
            "Hydrated source discovery: path=%s schema=%s artifacts=%s",
            path,
            schema_version,
            artifact_count,
        )

        return PlanSourceDiscovery(
            path=path,
            schema_version=schema_version,
            artifact_count=artifact_count,
        )

    except KeyError as exc:
        raise PlanHydrationError(
            f"Missing source_discovery field: {exc}"
        ) from exc


def _hydrate_intent(intent: Dict[str, Any]) -> PlanIntent:
    """
    Hydrate PlanIntent.

    :param intent: Intent payload.
    :return: PlanIntent instance.
    """
    try:
        target = intent["target"]
        description = intent["description"]

        LOGGER.debug(
            "Hydrated plan intent: target=%s",
            target,
        )

        return PlanIntent(
            target=target,
            description=description,
        )

    except KeyError as exc:
        raise PlanHydrationError(
            f"Missing intent field: {exc}"
        ) from exc


def _hydrate_actions(raw_actions: List[Dict[str, Any]]) -> List[PlanAction]:
    """
    Hydrate a list of PlanAction models.

    :param raw_actions: Raw actions list.
    :return: List of PlanAction objects.
    """
    actions: List[PlanAction] = []

    for index, action in enumerate(raw_actions):
        try:
            hydrated = PlanAction(
                id=action["id"],
                type=action["type"],
                target=action["target"],
                reason=action["reason"],
                parameters=action.get("parameters", {}),
                derived_from_evidence=action.get(
                    "derived_from_evidence",
                    [],
                ),
            )
            actions.append(hydrated)

            LOGGER.debug(
                "Hydrated action %s: id=%s type=%s",
                index,
                hydrated.id,
                hydrated.type,
            )

        except KeyError as exc:
            raise PlanHydrationError(
                f"Missing action field {exc} in action index {index}"
            ) from exc

    return actions