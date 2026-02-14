"""
Semantic execution handler for injecting a ``<topicref>`` element into a DITA map.

Although categorized as semantic, this handler performs real filesystem
mutation and MUST obey the same safety guarantees as filesystem handlers.

Responsibilities
----------------
- Validate parameters
- Resolve paths via sandbox
- Enforce MutationPolicy before writes
- Parse XML
- Enforce idempotence
- Inject deterministic topicref
- Persist changes
- Support dry-run

Never:
- use cwd
- construct absolute paths directly
- bypass sandbox or policy
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
)

LOGGER = logging.getLogger(__name__)


class InjectTopicrefHandler(ExecutionHandler):
    """
    Execution handler for ``inject_topicref`` actions.
    """

    action_type = "inject_topicref"

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
        Execute an ``inject_topicref`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            href = params["href"]
            rel_target = Path(params["target_path"])
        except KeyError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message=f"Missing required parameter: {exc.args[0]}",
                error=str(exc),
            )

        if not isinstance(href, str) or not href.strip():
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="Parameter 'href' must be a non-empty string",
            )

        # -------------------------------------------------
        # Resolve via sandbox
        # -------------------------------------------------

        target_path = sandbox.resolve(rel_target)

        LOGGER.info(
            "inject_topicref id=%s dry_run=%s target=%s href=%s",
            action_id,
            dry_run,
            target_path,
            href,
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
                message="Dry-run: topicref injection skipped",
                data={
                    "target_map": str(target_path),
                    "href": href,
                },
            )

        # -------------------------------------------------
        # Validation
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
        # Idempotence
        # -------------------------------------------------

        for elem in root.iter():
            if elem.tag.endswith("topicref") and elem.attrib.get("href") == href:
                return ExecutionActionResult(
                    action_id=action_id,
                    status="skipped",
                    handler=self.__class__.__name__,
                    dry_run=False,
                    message=f"topicref with href '{href}' already exists",
                )

        # -------------------------------------------------
        # Inject
        # -------------------------------------------------

        topicref = ET.Element("topicref", href=href)
        root.append(topicref)

        tree.write(
            target_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        LOGGER.info(
            "inject_topicref id=%s injected href='%s' into %s",
            action_id,
            href,
            target_path,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message=f"Injected topicref href='{href}' into {target_path}",
            data={
                "target_map": str(target_path),
                "href": href,
            },
        )