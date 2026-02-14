"""
Plan loading utilities.

Loads a ``plan.json`` file from disk and hydrates it into a validated
:class:`~dita_package_processor.planning.models.Plan` model.

Responsibilities:
- Read JSON from disk
- Parse JSON into a Python object
- Delegate structural validation and typing to the hydrator

This module enforces a *hard boundary* between:
    Filesystem → Planning Domain

No semantic validation, execution logic, or fallback behavior is allowed here.
All failures are fatal and must abort the pipeline.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.planning.hydrator import (
    PlanHydrationError,
    hydrate_plan,
)
from dita_package_processor.planning.models import Plan

LOGGER = logging.getLogger(__name__)


class PlanLoadError(ValueError):
    """
    Raised when a plan file cannot be loaded or hydrated.

    Indicates a contract boundary failure between the filesystem
    and the planning domain model.

    These errors are non-recoverable by design.
    """


def load_plan(path: Path) -> Plan:
    """
    Load and hydrate a ``plan.json`` file.

    Strict process:
        1. Read UTF-8 JSON text from disk
        2. Parse JSON into a Python mapping
        3. Hydrate mapping into a :class:`Plan`

    No optional behavior, no guessing, no silent recovery.

    :param path: Path to the ``plan.json`` file.
    :return: Fully hydrated :class:`Plan` instance.
    :raises PlanLoadError: If any step fails.
    """
    LOGGER.info("Loading execution plan from %s", path)

    raw_text = _read_file(path)
    payload = _parse_json(raw_text, path)
    plan = _hydrate(payload, path)

    LOGGER.info(
        "Plan successfully loaded: version=%s path=%s",
        plan.plan_version,
        path,
    )
    return plan


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> str:
    """
    Read plan file from disk.

    :param path: File path.
    :return: File contents as string.
    :raises PlanLoadError: If file cannot be read.
    """
    try:
        text = path.read_text(encoding="utf-8")
        LOGGER.debug("Read %d bytes from plan file: %s", len(text), path)
        return text
    except Exception as exc:  # noqa: BLE001
        LOGGER.error(
            "Failed to read plan file: %s",
            path,
            exc_info=True,
        )
        raise PlanLoadError(f"Failed to read plan file: {path}") from exc


def _parse_json(raw_text: str, path: Path) -> Dict[str, Any]:
    """
    Parse JSON payload.

    :param raw_text: Raw JSON string.
    :param path: Source file path (for error context).
    :return: Parsed JSON mapping.
    :raises PlanLoadError: If JSON is invalid.
    """
    try:
        payload = json.loads(raw_text)
        LOGGER.debug("Parsed JSON successfully from %s", path)
        return payload
    except json.JSONDecodeError as exc:
        LOGGER.error(
            "Invalid JSON in plan file: %s",
            path,
            exc_info=True,
        )
        raise PlanLoadError(f"Invalid JSON in plan file: {path}") from exc


def _hydrate(payload: Dict[str, Any], path: Path) -> Plan:
    """
    Hydrate JSON payload into a Plan model.

    :param payload: Parsed JSON mapping.
    :param path: Source file path (for error context).
    :return: Hydrated Plan.
    :raises PlanLoadError: If hydration fails.
    """
    try:
        plan = hydrate_plan(payload)
        LOGGER.debug(
            "Hydrated plan successfully: version=%s path=%s",
            plan.plan_version,
            path,
        )
        return plan
    except PlanHydrationError as exc:
        LOGGER.error(
            "Plan hydration failed for file: %s",
            path,
            exc_info=True,
        )
        raise PlanLoadError(f"Plan hydration failed for file: {path}") from exc
    except Exception as exc:  # noqa: BLE001
        LOGGER.error(
            "Unexpected error during plan hydration: %s",
            path,
            exc_info=True,
        )
        raise PlanLoadError(f"Unexpected error while loading plan: {path}") from exc