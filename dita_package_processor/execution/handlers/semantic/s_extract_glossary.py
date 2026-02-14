"""
Semantic execution handler for extracting glossary topic references
from a DITA definition map.

This is a *read-only* execution handler. It performs no filesystem mutation
and no plan mutation. Its sole responsibility is to:

- Validate parameters
- Load and parse the definition map
- Locate glossary topicref containers by navtitle
- Extract nested topicref href attributes
- Return a deterministic ExecutionActionResult

It NEVER:
- uses cwd
- mutates filesystem
- mutates plan
- infers semantics beyond structural XML traversal
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler

LOGGER = logging.getLogger(__name__)


class ExtractGlossaryHandler(ExecutionHandler):
    """
    Execution handler for ``extract_glossary``.

    Pure read-only handler.
    """

    action_type = "extract_glossary"

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        action: Dict[str, Any],
    ) -> ExecutionActionResult:
        """
        Execute an ``extract_glossary`` action.

        Returns glossary hrefs in ExecutionActionResult.data.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            map_path = Path(params["definition_map"]).resolve()
            navtitle = str(params["definition_navtitle"])
        except KeyError as exc:
            LOGGER.error(
                "extract_glossary id=%s missing parameter: %s",
                action_id,
                exc,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message=f"Missing required parameter: {exc.args[0]}",
                error=str(exc),
            )

        LOGGER.info(
            "extract_glossary id=%s dry_run=%s map=%s navtitle=%s",
            action_id,
            dry_run,
            map_path,
            navtitle,
        )

        # -------------------------------------------------
        # Dry-run
        # -------------------------------------------------

        if dry_run:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=True,
                message=(
                    "Dry-run: would extract glossary references "
                    f"from {map_path}"
                ),
                data={"glossary_hrefs": []},
            )

        # -------------------------------------------------
        # Missing file (non-fatal)
        # -------------------------------------------------

        if not map_path.exists():
            LOGGER.warning(
                "extract_glossary id=%s definition map not found: %s",
                action_id,
                map_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Definition map not found: {map_path}",
                data={"glossary_hrefs": []},
            )

        # -------------------------------------------------
        # Parse XML
        # -------------------------------------------------

        try:
            tree = ET.parse(map_path)
        except ET.ParseError as exc:
            LOGGER.error(
                "extract_glossary id=%s invalid XML: %s",
                action_id,
                map_path,
            )
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Invalid XML in definition map",
                error=str(exc),
            )

        root = tree.getroot()

        glossary_hrefs: List[str] = []

        # -------------------------------------------------
        # Extract glossary topicrefs
        # -------------------------------------------------

        for topicref in root.iter():
            if not topicref.tag.endswith("topicref"):
                continue

            # ONLY direct navtitle child (deterministic)
            nav = topicref.find("navtitle")
            if nav is None:
                continue

            if (nav.text or "").strip() != navtitle:
                continue

            LOGGER.debug(
                "extract_glossary id=%s matched glossary container",
                action_id,
            )

            for child in topicref.iter():
                if not child.tag.endswith("topicref"):
                    continue

                href = child.attrib.get("href")
                if href:
                    glossary_hrefs.append(href)

        LOGGER.info(
            "extract_glossary id=%s extracted %d references",
            action_id,
            len(glossary_hrefs),
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message=f"Extracted {len(glossary_hrefs)} glossary references",
            data={"glossary_hrefs": glossary_hrefs},
        )