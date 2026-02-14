"""
builder.py

Materialization target builder for the DITA Package Processor.

This module is a thin adapter responsible for preparing a concrete,
publication-ready target directory for materialization output.

Materialization is intentionally separated from execution and validation:

- Planning answers: "What should happen?"
- Execution answers: "What actually ran?"
- Materialization answers: "Is it safe to publish the results, and where?"
- Builder answers: "Can we write to the target location?"

This module does NOT:
- perform discovery
- emit plans
- execute handlers
- validate execution semantics
- detect collisions
- decide safety

It operates strictly on a MaterializationManifest and filesystem targets.

Builder contract:
"I prepare the place. I do not decide if it’s safe."
"""

from __future__ import annotations

import logging
from pathlib import Path

from dita_package_processor.materialization.models import MaterializationManifest

LOGGER = logging.getLogger(__name__)


class MaterializationError(RuntimeError):
    """Raised when the target filesystem location cannot be prepared safely."""


class TargetMaterializationBuilder:
    """
    Prepares the target directory for materialization output.

    This builder is intentionally thin. It assumes upstream orchestration
    has already validated safety (execution state, layout, collisions, etc.)
    and provides a complete MaterializationManifest.

    Design constraints:
    - deterministic
    - idempotent
    - no implicit deletion
    - no implicit overwrites
    - filesystem readiness only
    """

    def __init__(
        self,
        *,
        manifest: MaterializationManifest,
    ) -> None:
        """
        Initialize the builder.

        :param manifest: MaterializationManifest describing the target root
            and intended outputs.
        """
        self._manifest = manifest

    def build(self) -> None:
        """
        Prepare the target directory for materialization output.

        This method creates the target root directory if missing and performs
        minimal sanity checks that the location is usable.

        :raises MaterializationError: If the target location cannot be prepared.
        """
        target_root = self._get_target_root()

        LOGGER.info("Preparing materialization target root: %s", target_root)

        self._ensure_target_root_exists(target_root)
        self._ensure_target_root_is_directory(target_root)
        self._ensure_target_root_is_writable(target_root)

        LOGGER.info("Target root prepared successfully: %s", target_root)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_target_root(self) -> Path:
        """
        Get the target root from the manifest.

        :return: Target root path.
        :raises MaterializationError: If the manifest does not provide one.
        """
        target_root = getattr(self._manifest, "target_root", None)

        if target_root is None:
            raise MaterializationError(
                "MaterializationManifest missing target_root; cannot prepare target"
            )

        if not isinstance(target_root, Path):
            raise MaterializationError(
                f"MaterializationManifest target_root is not a Path: {target_root!r}"
            )

        if str(target_root).strip() == "":
            raise MaterializationError("MaterializationManifest target_root is empty")

        return target_root

    def _ensure_target_root_exists(self, target_root: Path) -> None:
        """
        Ensure the target root exists. Creates it if missing.

        :param target_root: Target root directory.
        :raises MaterializationError: If directory creation fails.
        """
        try:
            target_root.mkdir(parents=True, exist_ok=True)
            LOGGER.debug("Ensured target root exists: %s", target_root)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "Failed to create target root %s: %s",
                target_root,
                exc,
                exc_info=True,
            )
            raise MaterializationError(
                f"Unable to create target root: {target_root}"
            ) from exc

    def _ensure_target_root_is_directory(self, target_root: Path) -> None:
        """
        Ensure the target root is a directory.

        :param target_root: Target root path.
        :raises MaterializationError: If the path exists but is not a directory.
        """
        if not target_root.is_dir():
            raise MaterializationError(
                f"Target root exists but is not a directory: {target_root}"
            )

    def _ensure_target_root_is_writable(self, target_root: Path) -> None:
        """
        Ensure the target root is writable.

        Uses a practical, deterministic probe: create and delete a tiny
        sentinel file. This avoids platform-specific permission guessing.

        :param target_root: Target root directory.
        :raises MaterializationError: If the directory is not writable.
        """
        sentinel = target_root / ".materialization_write_probe"

        try:
            sentinel.write_text("probe", encoding="utf-8")
            sentinel.unlink(missing_ok=True)
            LOGGER.debug("Target root is writable: %s", target_root)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "Target root is not writable %s: %s",
                target_root,
                exc,
                exc_info=True,
            )
            raise MaterializationError(
                f"Target root is not writable: {target_root}"
            ) from exc


__all__ = [
    "MaterializationError",
    "TargetMaterializationBuilder",
]