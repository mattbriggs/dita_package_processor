"""
Execution handler bootstrap.

This module is the single authoritative place where ALL execution handlers
are registered.

Design rules
------------
- Exactly ONE registry instance exists process-wide
- No dynamic discovery
- No reflection
- Explicit registration only
- Deterministic

Why
---
Handlers are infrastructure, not runtime state.
Creating multiple registries leads to:
    - missing handlers
    - inconsistent dispatch
    - impossible debugging

Therefore this module exposes:

    get_registry()

and NEVER returns a fresh registry.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from dita_package_processor.execution.registry import ExecutionHandlerRegistry

# -----------------------------------------------------------------------------
# Handler imports (explicit wiring only)
# -----------------------------------------------------------------------------

# Filesystem handlers
from dita_package_processor.execution.handlers.fs.fs_copy_map import CopyMapHandler
from dita_package_processor.execution.handlers.fs.fs_copy_topic import CopyTopicHandler
from dita_package_processor.execution.handlers.fs.fs_copy_media import CopyMediaHandler

# Semantic handlers
from dita_package_processor.execution.handlers.semantic.s_copy_file import CopyFileHandler
from dita_package_processor.execution.handlers.semantic.s_delete_file import DeleteFileHandler
from dita_package_processor.execution.handlers.semantic.s_wrap_map import WrapMapHandler
from dita_package_processor.execution.handlers.semantic.s_inject_topicref import (
    InjectTopicrefHandler,
)
from dita_package_processor.execution.handlers.semantic.s_inject_topicrefs import (
    InjectTopicrefsHandler,
)
from dita_package_processor.execution.handlers.semantic.s_wrap_map_topicrefs import (
    WrapMapTopicrefsHandler,
)
from dita_package_processor.execution.handlers.semantic.s_inject_glossary import (
    InjectGlossaryHandler,
)
from dita_package_processor.execution.handlers.semantic.s_extract_glossary import (
    ExtractGlossaryHandler,
)

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

    This function lazily constructs the registry exactly once.

    Returns
    -------
    ExecutionHandlerRegistry
        Fully populated registry containing all handlers.
    """
    global _REGISTRY

    if _REGISTRY is not None:
        return _REGISTRY

    LOGGER.debug("Initializing execution handler registry (singleton)")

    registry = ExecutionHandlerRegistry()

    # ------------------------------------------------------------------
    # Filesystem handlers
    # ------------------------------------------------------------------

    registry.register(CopyMapHandler)
    registry.register(CopyTopicHandler)
    registry.register(CopyMediaHandler)

    # ------------------------------------------------------------------
    # Semantic handlers
    # ------------------------------------------------------------------

    registry.register(CopyFileHandler)
    registry.register(DeleteFileHandler)
    registry.register(WrapMapHandler)
    registry.register(InjectTopicrefHandler)
    registry.register(InjectTopicrefsHandler)
    registry.register(WrapMapTopicrefsHandler)
    registry.register(InjectGlossaryHandler)
    registry.register(ExtractGlossaryHandler)

    count = _registry_size(registry)

    # If we couldn't count, still log something useful.
    if count == 0:
        LOGGER.info(
            "Execution handler registry initialized (count unavailable; "
            "consider adding __len__ to ExecutionHandlerRegistry)"
        )
    else:
        LOGGER.info("Execution handler registry initialized with %d handlers", count)

    _REGISTRY = registry
    return registry