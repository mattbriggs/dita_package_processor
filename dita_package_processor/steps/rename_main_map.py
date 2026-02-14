"""
Processing step for renaming the resolved main DITA map.

This step renames the main map resolved from ``index.ditamap`` to match
the configured DOCX filename stem and records the new path in the
processing context.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dita_package_processor.context import ProcessingContext
from dita_package_processor.steps.base import ProcessingStep


class RenameMainMapStep(ProcessingStep):
    """
    Rename the main DITA map to ``<docx_stem>.ditamap``.

    This step:
    - Requires the main map path to already be resolved
    - Renames the map file on disk
    - Stores the renamed path in the processing context
    """

    #: Canonical step name used for registration and logging.
    name: str = "rename-main-map"

    def run(self, context: ProcessingContext, logger: logging.Logger) -> None:
        """
        Execute the main map renaming step.

        :param context: Shared processing context.
        :param logger: Logger instance scoped to the processor.
        :raises ValueError: If the main map has not been resolved yet.
        :raises FileExistsError: If the target filename already exists.
        """
        if context.main_map_path is None:
            raise ValueError(
                "Main map path not set; did RemoveIndexMapStep run?"
            )

        source_path = context.main_map_path
        target_path = (
            context.package_dir / f"{context.docx_stem}.ditamap"
        )

        if source_path.resolve() == target_path.resolve():
            context.renamed_main_map_path = target_path

            logger.info(
                "Main map already matches target name: %s",
                target_path,
            )
            return

        if target_path.exists():
            raise FileExistsError(
                f"Target main map already exists: {target_path}"
            )

        source_path.rename(target_path)
        context.renamed_main_map_path = target_path

        logger.info(
            "Renamed main map: %s -> %s",
            source_path,
            target_path,
        )