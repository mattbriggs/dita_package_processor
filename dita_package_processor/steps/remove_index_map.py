"""
Processing step for resolving and removing the index DITA map.

This step reads ``index.ditamap``, resolves the referenced main map,
records its location in the processing context, and then deletes
``index.ditamap`` from the package.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dita_package_processor.context import ProcessingContext
from dita_package_processor.dita_xml import first_href_to_map, read_xml
from dita_package_processor.steps.base import ProcessingStep


class RemoveIndexMapStep(ProcessingStep):
    """
    Resolve the main map from ``index.ditamap`` and remove the index map.

    This step:
    - Reads ``index.ditamap`` from the package root
    - Extracts the referenced main map ``href``
    - Stores the resolved main map path in the processing context
    - Deletes ``index.ditamap`` from the filesystem
    """

    #: Canonical step name used for registration and logging.
    name: str = "remove-index-map"

    def run(self, context: ProcessingContext, logger: logging.Logger) -> None:
        """
        Execute the index map resolution step.

        :param context: Shared processing context.
        :param logger: Logger instance scoped to the processor.
        :raises FileNotFoundError: If ``index.ditamap`` is missing.
        :raises ValueError: If the main map ``href`` cannot be resolved.
        """
        index_path = context.index_map_path

        if not index_path.exists():
            raise FileNotFoundError(
                f"Missing index map: {index_path}"
            )

        index_doc = read_xml(index_path)
        href = first_href_to_map(index_doc)

        if not href:
            raise ValueError(
                "Could not find referenced main .ditamap href in index.ditamap"
            )

        main_map_path = (context.package_dir / href).resolve()

        if not main_map_path.exists():
            raise FileNotFoundError(
                f"Referenced main map not found: {main_map_path}"
            )

        context.main_map_path = Path(main_map_path)

        logger.info(
            "Main map resolved from index: %s",
            context.main_map_path,
        )

        index_path.unlink()

        logger.info(
            "Deleted index map: %s",
            index_path,
        )