"""
Semantic execution handler for ``wrap_map`` actions.

Although categorized as semantic, this handler performs real filesystem
mutation and MUST obey the same safety guarantees as filesystem handlers.

Responsibilities
----------------
- Validate parameters
- Resolve paths via sandbox
- Enforce mutation policy
- Create wrapper topic (idempotent)
- Rewrite map deterministically
- Support dry-run

Never:
- use cwd
- construct absolute paths
- bypass sandbox or policy
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
)

LOGGER = logging.getLogger(__name__)


class WrapMapHandler(ExecutionHandler):
    """
    Execution handler for ``wrap_map`` actions.

    Creates a wrapper topic and nests all top-level topicrefs
    beneath a single wrapper topicref.
    """

    action_type = "wrap_map"

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        action: Dict[str, Any],
        sandbox: Sandbox,
        policy: MutationPolicy,
    ) -> ExecutionActionResult:
        """
        Execute a ``wrap_map`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        target_rel = action.get("target")
        title = params.get("title")
        source_rel = params.get("source_map")

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        if not target_rel:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="wrap_map requires action.target",
            )

        if not title:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="wrap_map requires parameter: title",
            )

        if not source_rel:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="wrap_map requires parameter: source_map",
            )

        # -------------------------------------------------
        # Path resolution
        # -------------------------------------------------

        wrapper_topic = sandbox.resolve(Path(target_rel))
        source_map = sandbox.resolve(Path(source_rel))

        LOGGER.info(
            "wrap_map id=%s dry_run=%s wrapper=%s source=%s",
            action_id,
            dry_run,
            wrapper_topic,
            source_map,
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
                message="Dry-run: wrap_map skipped",
                data={
                    "wrapper_topic": str(wrapper_topic),
                    "source_map": str(source_map),
                    "title": title,
                },
            )

        # -------------------------------------------------
        # Validate source map
        # -------------------------------------------------

        if not source_map.exists() or not source_map.is_file():
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Source map does not exist or is not a file: {source_map}",
                error="InvalidSource",
            )

        # -------------------------------------------------
        # Policy enforcement BEFORE any write
        # -------------------------------------------------

        try:
            policy.validate_target(wrapper_topic)
            policy.validate_target(source_map)
        except PolicyViolationError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=str(exc),
                error=exc.failure_type,
            )

        # -------------------------------------------------
        # Create wrapper topic (idempotent)
        # -------------------------------------------------

        created_wrapper = False

        if not wrapper_topic.exists():
            LOGGER.info("Creating wrapper topic: %s", wrapper_topic)

            topic_id = title.strip().lower().replace(" ", "_")

            concept = ET.Element("concept", id=topic_id)
            ET.SubElement(concept, "title").text = title
            ET.SubElement(concept, "conbody")

            wrapper_topic.parent.mkdir(parents=True, exist_ok=True)

            ET.ElementTree(concept).write(
                wrapper_topic,
                encoding="utf-8",
                xml_declaration=True,
            )

            created_wrapper = True

        # -------------------------------------------------
        # Parse source map
        # -------------------------------------------------

        try:
            tree = ET.parse(source_map)
            root = tree.getroot()
        except ET.ParseError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Invalid XML in source map",
                error=str(exc),
            )

        original_refs: List[ET.Element] = list(root.findall("./topicref"))

        if len(original_refs) <= 1:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Map already wrapped or trivial",
                data={
                    "wrapper_created": created_wrapper,
                    "topicref_count": len(original_refs),
                },
            )

        # -------------------------------------------------
        # Rewrite map
        # -------------------------------------------------

        for ref in original_refs:
            root.remove(ref)

        wrapper_ref = ET.Element("topicref", href=wrapper_topic.name)

        for ref in original_refs:
            wrapper_ref.append(ref)

        root.append(wrapper_ref)

        tree.write(
            source_map,
            encoding="utf-8",
            xml_declaration=True,
        )

        LOGGER.info(
            "wrap_map id=%s wrapped_count=%d wrapper=%s",
            action_id,
            len(original_refs),
            wrapper_topic.name,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message="Map wrapped successfully",
            data={
                "wrapper_topic": str(wrapper_topic),
                "source_map": str(source_map),
                "wrapper_created": created_wrapper,
                "wrapped_topicref_count": len(original_refs),
            },
        )