"""
Semantic execution handler for injecting a glossary placeholder
into a DITA topic.

This handler mutates the filesystem in a controlled and auditable way.

Responsibilities
----------------
- Validate parameters
- Resolve paths via sandbox
- Parse XML
- Enforce idempotence
- Inject deterministic placeholder
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
from typing import Any, Dict, List

from dita_package_processor.execution.models import ExecutionActionResult
from dita_package_processor.execution.registry import ExecutionHandler
from dita_package_processor.execution.safety.sandbox import Sandbox
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    PolicyViolationError,
)

LOGGER = logging.getLogger(__name__)


class InjectGlossaryHandler(ExecutionHandler):
    """
    Execution handler for ``inject_glossary``.
    """

    action_type = "inject_glossary"

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
        Execute an ``inject_glossary`` action.
        """
        action_id = str(action.get("id", "<unknown>"))
        params: Dict[str, Any] = action.get("parameters", {})
        dry_run = bool(action.get("dry_run", False))

        # -------------------------------------------------
        # Parameter validation
        # -------------------------------------------------

        try:
            rel_target = Path(params["target_topic"])
        except KeyError as exc:
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message=f"Missing required parameter: {exc.args[0]}",
                error=str(exc),
            )

        glossary_hrefs: List[str] = params.get("glossary_hrefs", [])

        if not isinstance(glossary_hrefs, list):
            return ExecutionActionResult(
                action_id=action_id,
                status="failed",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="Parameter 'glossary_hrefs' must be a list",
            )

        if not glossary_hrefs:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=dry_run,
                message="No glossary_hrefs provided",
            )

        # -------------------------------------------------
        # Resolve target via sandbox
        # -------------------------------------------------

        target_path = sandbox.resolve(rel_target)

        LOGGER.info(
            "inject_glossary id=%s dry_run=%s target=%s glossary_count=%d",
            action_id,
            dry_run,
            target_path,
            len(glossary_hrefs),
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
                message="Dry-run: injection skipped",
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
                message=f"Target topic does not exist or is not a file: {target_path}",
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
                message="Invalid XML in target topic",
                error=str(exc),
            )

        # -------------------------------------------------
        # Locate conbody
        # -------------------------------------------------

        conbody = next(
            (e for e in root.iter() if e.tag.endswith("conbody")),
            None,
        )

        if conbody is None:
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="No conbody element found",
            )

        # -------------------------------------------------
        # Idempotence
        # -------------------------------------------------

        if any(e.tag.endswith("glossentry") for e in conbody.iter()):
            return ExecutionActionResult(
                action_id=action_id,
                status="skipped",
                handler=self.__class__.__name__,
                dry_run=False,
                message="Glossary already injected",
            )

        # -------------------------------------------------
        # Inject placeholder
        # -------------------------------------------------

        glossentry = ET.SubElement(conbody, "glossentry")
        ET.SubElement(glossentry, "glossterm").text = "Glossary"

        glossdef = ET.SubElement(glossentry, "glossdef")
        ET.SubElement(glossdef, "p").text = "Glossary entries injected."

        # -------------------------------------------------
        # Persist
        # -------------------------------------------------

        tree.write(
            target_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        LOGGER.info(
            "inject_glossary id=%s injected placeholder into %s",
            action_id,
            target_path,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="success",
            handler=self.__class__.__name__,
            dry_run=False,
            message=f"Injected glossary placeholder into {target_path}",
            data={
                "target_topic": str(target_path),
                "glossary_count": len(glossary_hrefs),
            },
        )