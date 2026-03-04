"""
Execution handler bootstrap.

This module is the single authoritative place where the execution handler
registry is populated.

Since the introduction of the plugin system, all handler registration is
delegated to the plugin registry. Handlers are no longer imported or
registered here explicitly — they are provided by each plugin via
``DitaPlugin.handlers()``.

Design rules (unchanged)
------------------------
- Exactly ONE registry instance exists process-wide.
- No dynamic discovery beyond what plugins declare.
- Deterministic: CorePlugin loads first, then third-party plugins in
  alphabetical entry-point order.
- Conflict (duplicate action_type) is a startup error.

Therefore this module exposes:

    get_registry()

and NEVER returns a fresh registry.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from dita_package_processor.execution.registry import ExecutionHandlerRegistry

LOGGER = logging.getLogger(__name__)

__all__ = ["get_registry"]

# -----------------------------------------------------------------------------
# Global registry (singleton)
# -----------------------------------------------------------------------------

_REGISTRY: Optional[ExecutionHandlerRegistry] = None


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------


def _registry_size(registry: Any) -> int:
    """
    Best-effort registry size for logging.

    Some registry implementations don't implement ``__len__``. This function
    attempts a few common internal layouts, without making bootstrap brittle.

    Parameters
    ----------
    registry:
        ExecutionHandlerRegistry instance (or equivalent).

    Returns
    -------
    int
        Best-effort count of registered handlers.
    """
    # 1) If registry implements __len__, use it.
    try:
        return len(registry)  # type: ignore[arg-type]
    except TypeError:
        pass

    # 2) Common attribute names.
    for attr in ("handlers", "_handlers", "_registry", "_map"):
        if hasattr(registry, attr):
            value = getattr(registry, attr)
            try:
                return len(value)
            except Exception:  # noqa: BLE001
                continue

    # 3) Last resort: unknown.
    return 0


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def get_registry() -> ExecutionHandlerRegistry:
    """
    Return the global execution handler registry.

    On first call, the registry is built by asking the plugin registry for
    all handler classes (CorePlugin first, then any installed third-party
    plugins in alphabetical order).

    Returns
    -------
    ExecutionHandlerRegistry
        Fully populated registry containing all handlers.
    """
    global _REGISTRY

    if _REGISTRY is not None:
        return _REGISTRY

    LOGGER.debug("Initializing execution handler registry via plugin system")

    from dita_package_processor.plugins.registry import get_plugin_registry

    registry = ExecutionHandlerRegistry()

    for handler_cls in get_plugin_registry().all_handlers():
        registry.register(handler_cls)

    count = _registry_size(registry)

    if count == 0:
        LOGGER.info(
            "Execution handler registry initialized (count unavailable; "
            "consider adding __len__ to ExecutionHandlerRegistry)"
        )
    else:
        LOGGER.info("Execution handler registry initialized with %d handlers", count)

    _REGISTRY = registry
    return registry
