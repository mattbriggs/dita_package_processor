"""
Configuration loading utilities for the DITA Package Processor.

This module is responsible for loading runtime configuration from
``pyproject.toml`` and extracting the tool-specific configuration
namespace.
"""

from pathlib import Path
import tomllib
from typing import Dict, Any


def load_config(path: Path) -> Dict[str, Any]:
    """
    Load and return the DITA Package Processor configuration.

    The configuration is read from a TOML file and must contain a
    ``[tool.dita_package_processor]`` section. Only that subsection
    is returned to the caller.

    :param path: Path to the ``pyproject.toml`` configuration file.
    :return: Parsed configuration dictionary for the processor.
    :raises FileNotFoundError: If the configuration file does not exist.
    :raises KeyError: If the required tool configuration section
        is missing.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}"
        )

    with path.open("rb") as file_handle:
        config = tomllib.load(file_handle)

    try:
        return config["tool"]["dita_package_processor"]
    except KeyError as exc:
        raise KeyError(
            "Missing [tool.dita_package_processor] section in config."
        ) from exc