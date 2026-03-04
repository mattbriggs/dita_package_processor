"""
Plugin validation.

Validates a DitaPlugin instance for structural correctness before
it is admitted into the plugin registry.

Validation is intentionally strict:
- Missing or empty name/version → error
- Handler without action_type → error
- Pattern without required fields → error
- Duplicate IDs *within* a single plugin → error

Cross-plugin conflicts (duplicate pattern IDs, duplicate action_types)
are detected later in PluginRegistry when all plugins are aggregated.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dita_package_processor.plugins.protocol import DitaPlugin

LOGGER = logging.getLogger(__name__)


class PluginValidationError(ValueError):
    """Raised when a plugin fails structural validation."""


def validate_plugin(plugin: "DitaPlugin") -> "DitaPlugin":
    """
    Validate a plugin instance.

    :param plugin: Plugin instance to validate.
    :return: The same plugin instance (for chaining).
    :raises PluginValidationError: If any validation check fails.
    """
    _check_identity(plugin)
    _check_handlers(plugin)
    _check_patterns(plugin)

    LOGGER.debug(
        "Plugin validated: name=%s version=%s patterns=%d handlers=%d",
        plugin.name,
        plugin.version,
        len(plugin.patterns()),
        len(plugin.handlers()),
    )

    return plugin


# =============================================================================
# Identity checks
# =============================================================================


def _check_identity(plugin: "DitaPlugin") -> None:
    try:
        name = plugin.name
    except Exception as exc:  # noqa: BLE001
        raise PluginValidationError(
            f"Plugin {plugin!r} raised error accessing .name: {exc}"
        ) from exc

    if not name or not isinstance(name, str):
        raise PluginValidationError(
            f"Plugin {plugin.__class__.__name__}.name must be a non-empty string, "
            f"got {name!r}"
        )

    try:
        version = plugin.version
    except Exception as exc:  # noqa: BLE001
        raise PluginValidationError(
            f"Plugin {name!r} raised error accessing .version: {exc}"
        ) from exc

    if not version or not isinstance(version, str):
        raise PluginValidationError(
            f"Plugin {name!r}.version must be a non-empty string, got {version!r}"
        )


# =============================================================================
# Handler checks
# =============================================================================


def _check_handlers(plugin: "DitaPlugin") -> None:
    try:
        handler_classes = plugin.handlers()
    except Exception as exc:  # noqa: BLE001
        raise PluginValidationError(
            f"Plugin {plugin.name!r}.handlers() raised: {exc}"
        ) from exc

    if not isinstance(handler_classes, list):
        raise PluginValidationError(
            f"Plugin {plugin.name!r}.handlers() must return a list"
        )

    seen_types: set[str] = set()

    for handler_cls in handler_classes:
        action_type = getattr(handler_cls, "action_type", None)

        if not action_type or not isinstance(action_type, str):
            raise PluginValidationError(
                f"Plugin {plugin.name!r}: handler {handler_cls.__name__!r} "
                f"missing valid action_type class attribute"
            )

        if action_type != "*" and action_type in seen_types:
            raise PluginValidationError(
                f"Plugin {plugin.name!r}: duplicate action_type {action_type!r} "
                f"within the same plugin"
            )

        seen_types.add(action_type)

        if not callable(getattr(handler_cls, "execute", None)):
            raise PluginValidationError(
                f"Plugin {plugin.name!r}: handler {handler_cls.__name__!r} "
                f"missing callable execute() method"
            )


# =============================================================================
# Pattern checks
# =============================================================================


def _check_patterns(plugin: "DitaPlugin") -> None:
    try:
        patterns = plugin.patterns()
    except Exception as exc:  # noqa: BLE001
        raise PluginValidationError(
            f"Plugin {plugin.name!r}.patterns() raised: {exc}"
        ) from exc

    if not isinstance(patterns, list):
        raise PluginValidationError(
            f"Plugin {plugin.name!r}.patterns() must return a list"
        )

    seen_ids: set[str] = set()

    for pattern in patterns:
        pid = getattr(pattern, "id", None)

        if not pid or not isinstance(pid, str):
            raise PluginValidationError(
                f"Plugin {plugin.name!r}: pattern missing valid id attribute"
            )

        if pid in seen_ids:
            raise PluginValidationError(
                f"Plugin {plugin.name!r}: duplicate pattern id {pid!r} "
                f"within the same plugin"
            )

        seen_ids.add(pid)

        for required_attr in ("applies_to", "signals", "asserts", "rationale"):
            if not hasattr(pattern, required_attr):
                raise PluginValidationError(
                    f"Plugin {plugin.name!r}: pattern {pid!r} missing "
                    f"required attribute {required_attr!r}"
                )
