"""
Semantic execution handler for injecting ``<topicref>`` elements from one
DITA map into another.

Although categorized as semantic, this handler performs real filesystem
mutation and MUST obey the same safety guarantees as filesystem handlers.

Responsibilities
----------------
- Validate parameters
- Resolve paths via sandbox/source_root
- Parse XML
- Enforce idempotence
- Inject deterministic topicrefs
- Persist changes
- Support dry-run
- Enforce MutationPolicy before writes

Never:
- use cwd
- construct absolute paths directly
- bypass sandbox or policy
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Set

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
)

LOGGER = logging.getLogger(__name__)


class InjectTopicrefsHandler(ExecutionHandler):
    """
    Execution handler for ``inject_topicrefs`` actions.
    """

    action_type = "inject_topicrefs"

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
        Execute an ``inject_topicrefs`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            rel_source = Path(params["source_map"])
            rel_target = Path(params["target_map"])
        except KeyError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message=f"Missing required parameter: {exc.args[0]}",
                error=str(exc),
            )

        # -------------------------------------------------
        # Path resolution
        # -------------------------------------------------

        source_map = (sandbox.source_root / rel_source).resolve()
        target_map = sandbox.resolve(rel_target)

        LOGGER.info(
            "inject_topicrefs id=%s dry_run=%s source=%s target=%s",
            action_id,
            dry_run,
            source_map,
            target_map,
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
                message="Dry-run: topicrefs injection skipped",
                data={
                    "source_map": str(source_map),
                    "target_map": str(target_map),
                },
            )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        for label, path in (("source_map", source_map), ("target_map", target_map)):
            if not path.exists() or not path.is_file():
                return ExecutionActionResult(
                    action_id=action_id,
                    status="failed",
                    handler=self.__class__.__name__,
                    dry_run=False,
                    message=f"{label} does not exist or is not a file: {path}",
                    error="InvalidPath",
                )

        # -------------------------------------------------
        # Policy enforcement (WRITE GUARD)
        # -------------------------------------------------

        try:
            policy.validate_target(target_map)
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
        # Parse XML
        # -------------------------------------------------

        try:
            source_tree = ET.parse(source_map)
            target_tree = ET.parse(target_map)
            source_root = source_tree.getroot()
            target_root = target_tree.getroot()
        except ET.ParseError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Invalid XML in source or target map",
                error=str(exc),
            )

        # -------------------------------------------------
        # Collect source topicrefs
        # -------------------------------------------------

        source_topicrefs: List[ET.Element] = [
            elem
            for elem in source_root.iter()
            if elem.tag.endswith("topicref") and "href" in elem.attrib
        ]

        if not source_topicrefs:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="No topicrefs found in source map",
            )

        # -------------------------------------------------
        # Idempotence
        # -------------------------------------------------

        existing_hrefs: Set[str] = {
            elem.attrib.get("href")
            for elem in target_root.iter()
            if elem.tag.endswith("topicref") and "href" in elem.attrib
        }

        injected: List[str] = []
        skipped: List[str] = []

        # -------------------------------------------------
        # Inject
        # -------------------------------------------------

        for topicref in source_topicrefs:
            href = topicref.attrib.get("href")

            if href in existing_hrefs:
                skipped.append(href)
                continue

            # deep copy element
            target_root.append(
                ET.fromstring(ET.tostring(topicref, encoding="unicode"))
            )

            injected.append(href)
            existing_hrefs.add(href)

        if not injected:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="All topicrefs already present",
                data={"skipped": skipped},
            )

        # -------------------------------------------------
        # Persist
        # -------------------------------------------------

        target_tree.write(
            target_map,
            encoding="utf-8",
            xml_declaration=True,
        )

        LOGGER.info(
            "inject_topicrefs id=%s injected=%d into %s",
            action_id,
            len(injected),
            target_map,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message=f"Injected {len(injected)} topicrefs",
            data={
                "source_map": str(source_map),
                "target_map": str(target_map),
                "injected": injected,
                "skipped": skipped,
            },
        )