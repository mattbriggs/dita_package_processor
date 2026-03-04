"""
Plugin system for the DITA Package Processor.

Public surface
--------------
- :class:`DitaPlugin`          Base class for all plugins.
- :func:`get_plugin_registry`  Access the singleton plugin registry.
- :func:`load_plugins`         Load all plugins (called once at bootstrap).

Quick start
-----------
Create a Python package that implements :class:`DitaPlugin`, then declare
it as an entry point in your ``pyproject.toml``::

    [project.entry-points."dita_package_processor.plugins"]
    my_plugin = "my_package:plugin"   # module-level DitaPlugin instance

Install it (``pip install -e .``) and it will be picked up automatically.

Use ``dita_package_processor plugin list`` to verify the plugin is loaded.
"""

from dita_package_processor.plugins.protocol import DitaPlugin
from dita_package_processor.plugins.registry import get_plugin_registry
from dita_package_processor.plugins.loader import load_plugins

__all__ = [
    "DitaPlugin",
    "get_plugin_registry",
    "load_plugins",
]
