"""
Processing step for normalizing non-main DITA maps.

This step performs the following actions:

- Identifies and handles the abstract map.
- Pulls the abstract topic into the main map.
- Numbers remaining maps sequentially.
- Wraps each map's top-level topicrefs under a generated concept topic.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List

from lxml import etree

from dita_package_processor.context import ProcessingContext
from dita_package_processor.dita_xml import (
    XmlDocument,
    create_concept_topic_xml,
    find_first_topicref_href,
    get_map_title,
    get_top_level_topicrefs,
    read_xml,
    write_xml,
)
from dita_package_processor.steps.base import ProcessingStep
from dita_package_processor.utils import slugify


class ProcessMapsStep(ProcessingStep):
    """
    Normalize non-main DITA maps.

    Responsibilities:

    1. Detect an abstract map and inject its referenced topic into the
       renamed main map.
    2. Wrap each remaining map under a numbered wrapper concept topic
       to enforce a deterministic hierarchy.
    """

    #: Canonical step name used for registration.
    name: str = "process-maps"

    def _is_abstract_map(self, map_path: Path, map_title: str) -> bool:
        """
        Determine whether a map should be treated as the abstract map.

        Detection is based on filename or extracted map title.

        :param map_path: Path to the map file.
        :param map_title: Extracted map title.
        :return: ``True`` if the map is considered the abstract map.
        """
        if "abstract" in map_path.name.lower():
            return True

        return map_title.strip().lower() == "abstract map"

    def run(self, context: ProcessingContext, logger: logging.Logger) -> None:
        """
        Execute the map normalization step.

        :param context: Shared processing context.
        :param logger: Logger instance scoped to the processor.
        """
        if context.renamed_main_map_path is None:
            raise ValueError(
                "Renamed main map not set; did RenameMainMapStep run?"
            )

        # ------------------------------------------------------------------
        # Load renamed main map
        # ------------------------------------------------------------------
        main_doc: XmlDocument = read_xml(context.renamed_main_map_path)
        main_root = main_doc.root

        # ------------------------------------------------------------------
        # Collect non-main maps
        # ------------------------------------------------------------------
        all_maps: List[Path] = sorted(context.package_dir.glob("*.ditamap"))
        other_maps: List[Path] = [
            path
            for path in all_maps
            if path.resolve() != context.renamed_main_map_path.resolve()
        ]

        abstract_map: Optional[Path] = None
        numbered_maps: List[Path] = []

        # ------------------------------------------------------------------
        # Identify abstract map and remaining maps
        # ------------------------------------------------------------------
        for map_path in other_maps:
            # --------------------------------------------------------------
            # Skip definition map entirely
            # --------------------------------------------------------------
            if (
                context.definition_map_name
                and map_path.name == context.definition_map_name
            ):
                logger.info(
                    "Skipping definition map during map processing: %s",
                    map_path.name,
                )
                continue

            map_doc = read_xml(map_path)
            map_title = get_map_title(map_doc)

            if self._is_abstract_map(map_path, map_title):
                abstract_map = map_path
            else:
                numbered_maps.append(map_path)

        # ------------------------------------------------------------------
        # Handle abstract map (non-fatal)
        # ------------------------------------------------------------------
        if abstract_map is not None:
            abstract_doc = read_xml(abstract_map)
            abstract_href = find_first_topicref_href(abstract_doc)

            if abstract_href:
                abstract_ref = etree.Element(
                    "topicref",
                    href=abstract_href,
                )
                main_root.insert(0, abstract_ref)

                logger.info(
                    "Injected abstract topicref into main map: %s",
                    abstract_href,
                )
            else:
                logger.warning(
                    "Abstract map found but no topicref href detected: %s",
                    abstract_map.name,
                )

        # ------------------------------------------------------------------
        # Number and wrap remaining maps
        # ------------------------------------------------------------------
        for sequence, map_path in enumerate(numbered_maps, start=1):
            map_doc = read_xml(map_path)
            map_root = map_doc.root

            map_title = get_map_title(map_doc) or map_path.stem
            slug = slugify(map_title)

            topic_filename = f"{sequence}_{slug}.dita"
            topic_path = context.topics_dir / topic_filename

            topic_id = f"t_{sequence}_{slug}" if slug else f"t_{sequence}"
            topic_title = f"{sequence}. {map_title}"

            # --------------------------------------------------------------
            # Create wrapper concept topic
            # --------------------------------------------------------------
            wrapper_doc = create_concept_topic_xml(
                path=topic_path,
                topic_id=topic_id,
                title=topic_title,
            )

            write_xml(wrapper_doc)

            logger.info(
                "Created wrapper concept topic: %s",
                topic_path.name,
            )

            # --------------------------------------------------------------
            # Wrap existing top-level topicrefs
            # --------------------------------------------------------------
            top_refs = get_top_level_topicrefs(map_doc)

            wrapper_ref = etree.Element(
                "topicref",
                href=f"topics/{topic_filename}",
            )

            for ref in top_refs:
                map_root.remove(ref)
                wrapper_ref.append(ref)

            map_root.insert(0, wrapper_ref)

            write_xml(map_doc)

            logger.info(
                "Wrapped %d topicrefs under %s in %s",
                len(top_refs),
                topic_filename,
                map_path.name,
            )

        # ------------------------------------------------------------------
        # Persist main map
        # ------------------------------------------------------------------
        write_xml(main_doc)