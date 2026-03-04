"""
Plugin registry.

Aggregates all loaded plugins and provides unified access to:

- patterns (for discovery)
- handlers (for execution bootstrap)
- action emission (for planning)

The registry is a lazy singleton: it is populated on the first call
to ``get_plugin_registry()`` by invoking the plugin loader.

Cross-plugin conflict rules
---------------------------
- Duplicate pattern ID → startup error
- Duplicate action_type → startup error
- CorePlugin always loads first; third-party plugins sort alphabetically.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

if TYPE_CHECKING:
    from dita_package_processor.discovery.patterns import Pattern
    from dita_package_processor.execution.registry import ExecutionHandler
    from dita_package_processor.planning.contracts.planning_input import (
        PlanningArtifact,
        PlanningInput,
    )
    from dita_package_processor.plugins.protocol import DitaPlugin

LOGGER = logging.getLogger(__name__)


class PluginRegistryError(RuntimeError):
    """Raised when plugin conflict or structural error is detected."""


class PluginRegistry:
    """
    Registry holding all loaded and validated plugins.

    Do not instantiate directly. Use :func:`get_plugin_registry`.
    """

    def __init__(self) -> None:
        self._plugins: List["DitaPlugin"] = []

    # =========================================================================
    # Registration
    # =========================================================================

    def register(self, plugin: "DitaPlugin") -> None:
        """
        Add a validated plugin to the registry.

        :param plugin: Plugin instance (already validated).
        """
        LOGGER.info(
            "Registering plugin: name=%s version=%s",
            plugin.name,
            plugin.version,
        )
        self._plugins.append(plugin)

    # =========================================================================
    # Pattern access
    # =========================================================================

    def all_patterns(self) -> "List[Pattern]":
        """
        Aggregate patterns from all plugins.

        Pattern IDs must be unique across all plugins.

        :return: Flat list of all Pattern objects.
        :raises PluginRegistryError: On duplicate pattern ID.
        """
        seen: dict[str, str] = {}  # id → plugin name
        patterns: List["Pattern"] = []

        for plugin in self._plugins:
            for pattern in plugin.patterns():
                if pattern.id in seen:
                    raise PluginRegistryError(
                        f"Duplicate pattern id {pattern.id!r}: "
                        f"registered by both {seen[pattern.id]!r} and {plugin.name!r}"
                    )
                seen[pattern.id] = plugin.name
                patterns.append(pattern)

        LOGGER.debug(
            "Aggregated %d patterns from %d plugins",
            len(patterns),
            len(self._plugins),
        )
        return patterns

    # =========================================================================
    # Handler access
    # =========================================================================

    def all_handlers(self) -> "List[Type[ExecutionHandler]]":
        """
        Aggregate handler classes from all plugins.

        Handler action_types must be unique (wildcards ``"*"`` are allowed
        from exactly one plugin).

        :return: Flat list of handler classes.
        :raises PluginRegistryError: On duplicate action_type.
        """
        seen: dict[str, str] = {}  # action_type → plugin name
        handlers: List[Type["ExecutionHandler"]] = []

        for plugin in self._plugins:
            for handler_cls in plugin.handlers():
                action_type = handler_cls.action_type

                if action_type == "*":
                    if "*" in seen:
                        raise PluginRegistryError(
                            f"Wildcard handler already registered by {seen['*']!r}; "
                            f"plugin {plugin.name!r} cannot register another"
                        )
                else:
                    if action_type in seen:
                        raise PluginRegistryError(
                            f"Duplicate action_type {action_type!r}: "
                            f"registered by both {seen[action_type]!r} and {plugin.name!r}"
                        )

                seen[action_type] = plugin.name
                handlers.append(handler_cls)

        LOGGER.debug(
            "Aggregated %d handlers from %d plugins",
            len(handlers),
            len(self._plugins),
        )
        return handlers

    # =========================================================================
    # Action emission (planning)
    # =========================================================================

    def emit_actions_for(
        self,
        artifact: "PlanningArtifact",
        planning_input: "PlanningInput",
    ) -> "List[Dict[str, Any]]":
        """
        Collect action dicts from all plugins for a single artifact.

        Calls each plugin's ``emit_actions()`` in load order and aggregates
        the results. Evidence is extracted from ``artifact.metadata["evidence"]``.

        :param artifact: The artifact being planned.
        :param planning_input: Full planning context.
        :return: Flat list of action template dicts (no ``id`` field).
        """
        evidence: List[Dict[str, Any]] = artifact.metadata.get("evidence", [])
        actions: List[Dict[str, Any]] = []

        for plugin in self._plugins:
            emitted = plugin.emit_actions(artifact, evidence, planning_input)

            if emitted:
                LOGGER.debug(
                    "Plugin %s emitted %d action(s) for artifact %s",
                    plugin.name,
                    len(emitted),
                    artifact.path,
                )
                actions.extend(emitted)

        return actions

    # =========================================================================
    # Introspection
    # =========================================================================

    def list_plugins(self) -> "List[DitaPlugin]":
        """Return ordered list of all registered plugins."""
        return list(self._plugins)

    def __len__(self) -> int:
        return len(self._plugins)


# =============================================================================
# Singleton
# =============================================================================

_REGISTRY: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """
    Return the global plugin registry, populating it on first call.

    This function is safe to call from anywhere. The registry is built
    exactly once per process.

    :return: Fully populated :class:`PluginRegistry`.
    """
    global _REGISTRY

    if _REGISTRY is not None:
        return _REGISTRY

    LOGGER.debug("Initializing plugin registry (singleton)")

    from dita_package_processor.plugins.loader import load_plugins

    _REGISTRY = PluginRegistry()

    for plugin in load_plugins():
        _REGISTRY.register(plugin)

    LOGGER.info(
        "Plugin registry initialized: %d plugin(s) loaded",
        len(_REGISTRY),
    )

    return _REGISTRY
