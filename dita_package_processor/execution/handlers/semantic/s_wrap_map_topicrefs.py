"""
Semantic execution handler for wrapping top-level ``<topicref>`` elements
in a DITA map under a single wrapper ``<topicref>``.

Although categorized as semantic, this handler performs real filesystem
mutation and MUST obey the same safety guarantees as filesystem handlers.

Responsibilities
----------------
- Validate parameters
- Resolve paths via sandbox
- Parse XML
- Enforce idempotence
- Perform deterministic mutation
- Enforce MutationPolicy before writes
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


class WrapMapTopicrefsHandler(ExecutionHandler):
    """
    Execution handler for ``wrap_map_topicrefs`` actions.
    """

    action_type = "wrap_map_topicrefs"

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
        Execute a ``wrap_map_topicrefs`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            wrapper_href = params["wrapper_href"]
        except KeyError:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="Missing required parameter: wrapper_href",
            )

        target_rel = action.get("target")
        if not target_rel:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="wrap_map_topicrefs requires action.target",
            )

        # -------------------------------------------------
        # Path resolution
        # -------------------------------------------------

        target_path = sandbox.resolve(Path(target_rel))

        LOGGER.info(
            "wrap_map_topicrefs id=%s dry_run=%s target=%s wrapper_href=%s",
            action_id,
            dry_run,
            target_path,
            wrapper_href,
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
                message="Dry-run: wrap_map_topicrefs skipped",
                data={
                    "target": str(target_path),
                    "wrapper_href": wrapper_href,
                },
            )

        # -------------------------------------------------
        # Filesystem validation
        # -------------------------------------------------

        if not target_path.exists() or not target_path.is_file():
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message=f"Target map does not exist or is not a file: {target_path}",
                error="InvalidTarget",
            )

        # -------------------------------------------------
        # Policy enforcement (WRITE GUARD)
        # -------------------------------------------------

        try:
            policy.validate_target(target_path)
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
            tree = ET.parse(target_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Invalid XML in target map",
                error=str(exc),
            )

        # -------------------------------------------------
        # Collect top-level topicrefs
        # -------------------------------------------------

        topicrefs: List[ET.Element] = [
            elem
            for elem in root.findall("./topicref")
            if elem.attrib.get("href") != wrapper_href
        ]

        if not topicrefs:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Nothing to wrap",
            )

        # -------------------------------------------------
        # Idempotence
        # -------------------------------------------------

        # If already wrapped, skip
        for elem in root.findall("./topicref"):
            if elem.attrib.get("href") == wrapper_href:
                return ExecutionActionResult(
                    action_id=action_id,
                    status="skipped",
                    handler=self.__class__.__name__,
                    dry_run=False,
                    message="Wrapper already exists",
                )

        # -------------------------------------------------
        # Wrap
        # -------------------------------------------------

        for tr in topicrefs:
            root.remove(tr)

        wrapper = ET.Element("topicref", href=wrapper_href)

        for tr in topicrefs:
            wrapper.append(tr)

        root.append(wrapper)

        # -------------------------------------------------
        # Persist
        # -------------------------------------------------

        tree.write(
            target_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        LOGGER.info(
            "wrap_map_topicrefs id=%s wrapped_count=%d target=%s",
            action_id,
            len(topicrefs),
            target_path,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message=f"Wrapped {len(topicrefs)} topicrefs",
            data={
                "target": str(target_path),
                "wrapper_href": wrapper_href,
                "wrapped_count": len(topicrefs),
            },
        )