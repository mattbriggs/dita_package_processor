"""
Plugin loader.

Discovers and loads plugins via Python entry points.

Load order
----------
1. ``CorePlugin`` — always first; provides the built-in stack.
2. Third-party plugins — sorted alphabetically by entry point name.

Each plugin is validated before being admitted. A bad plugin causes a
loud startup failure (no silent skips in production; logging for debug).

Entry point group: ``dita_package_processor.plugins``

Third-party ``pyproject.toml``::

    [project.entry-points."dita_package_processor.plugins"]
    my_plugin = "my_package:plugin"       # module-level DitaPlugin instance
    # or
    my_plugin = "my_package:MyPlugin"     # DitaPlugin subclass (instantiated here)
"""

from __future__ import annotations

import importlib.metadata
import logging
from typing import List

from dita_package_processor.plugins.protocol import DitaPlugin
from dita_package_processor.plugins.validator import validate_plugin

LOGGER = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "dita_package_processor.plugins"


def load_plugins() -> List[DitaPlugin]:
    """
    Build the ordered plugin list.

    :return: Validated plugins in load order (CorePlugin first).
    :raises Exception: If any plugin fails validation or cannot be imported.
    """
    # CorePlugin is always first — it wraps the built-in stack.
    from dita_package_processor.plugins.core_plugin import CorePlugin

    core = CorePlugin()
    validate_plugin(core)
    plugins: List[DitaPlugin] = [core]

    LOGGER.debug("CorePlugin loaded: name=%s version=%s", core.name, core.version)

    # Discover and load third-party plugins.
    eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)

    for ep in sorted(eps, key=lambda e: e.name):
        LOGGER.debug("Loading plugin entry point: %s", ep.name)

        try:
            obj = ep.load()
        except Exception as exc:
            LOGGER.error(
                "Failed to import plugin entry point %r: %s",
                ep.name,
                exc,
            )
            raise

        # Entry point may be a class or an instance.
        if isinstance(obj, type) and issubclass(obj, DitaPlugin):
            try:
                obj = obj()
            except Exception as exc:
                LOGGER.error(
                    "Failed to instantiate plugin class %r from entry point %r: %s",
                    obj.__name__,
                    ep.name,
                    exc,
                )
                raise

        if not isinstance(obj, DitaPlugin):
            raise TypeError(
                f"Plugin entry point {ep.name!r} must resolve to a DitaPlugin "
                f"instance or subclass, got {type(obj)!r}"
            )

        validate_plugin(obj)
        plugins.append(obj)

        LOGGER.info(
            "Plugin loaded from entry point %r: name=%s version=%s",
            ep.name,
            obj.name,
            obj.version,
        )

    LOGGER.info("Total plugins loaded: %d", len(plugins))
    return plugins
