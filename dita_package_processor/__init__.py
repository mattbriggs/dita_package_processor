"""
DITA Package Processor.

Deterministic, modular pipeline for normalizing DITA 1.3 packages.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("dita-package-processor")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["__version__"]