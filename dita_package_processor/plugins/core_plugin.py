"""
Built-in core plugin.

``CorePlugin`` wraps the entire existing built-in stack:

- Patterns  → loaded from ``knowledge/known_patterns.yaml``
- Handlers  → all filesystem and semantic handlers
- Actions   → copy_map / copy_topic / copy_media per artifact type

It is the reference implementation of the DitaPlugin protocol and is
always loaded first, before any third-party plugins.

Third-party plugin developers should study this class as the canonical
example. Note that ``emit_actions`` must NOT include an ``"id"`` key —
the planner assigns IDs globally after collecting all actions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Type

from dita_package_processor.plugins.protocol import DitaPlugin

LOGGER = logging.getLogger(__name__)


class CorePlugin(DitaPlugin):
    """
    Built-in plugin that provides the standard DITA processing stack.

    This plugin is always loaded first and covers the full standard
    pipeline for DITA 1.3 packages.
    """

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def name(self) -> str:
        return "dita_package_processor.core"

    @property
    def version(self) -> str:
        from dita_package_processor import __version__

        # __version__ may be None if package metadata is unavailable in the
        # current environment (e.g. editable installs without re-running pip).
        return __version__ or "0.1.0"

    # =========================================================================
    # Discovery: patterns
    # =========================================================================

    def patterns(self):
        """Load all built-in discovery patterns from known_patterns.yaml."""
        from dita_package_processor.knowledge.known_patterns import (
            load_normalized_patterns,
        )

        return load_normalized_patterns()

    # =========================================================================
    # Planning: action emission
    # =========================================================================

    def emit_actions(
        self,
        artifact,
        evidence: List[Dict[str, Any]],
        context,
    ) -> List[Dict[str, Any]]:
        """
        Emit a single copy action for every artifact.

        Routing:
            map   → copy_map
            topic → copy_topic
            media → copy_media

        The action type mirrors the artifact type so the built-in handlers
        handle all standard artifacts without additional configuration.
        """
        from dita_package_processor.planning.layout_rules import resolve_target_path

        source_path = Path(artifact.path)
        logical_target_root = Path("target")

        target_path = resolve_target_path(
            artifact_type=artifact.artifact_type,
            source_path=source_path,
            target_root=logical_target_root,
        )

        action_type = f"copy_{artifact.artifact_type}"

        action: Dict[str, Any] = {
            "type": action_type,
            "target": str(target_path),
            "parameters": {
                "source_path": str(source_path),
                "target_path": str(target_path),
            },
            "reason": "Deterministic artifact copy (core plugin)",
            "derived_from_evidence": [
                ev.get("pattern_id", "") for ev in evidence if ev.get("pattern_id")
            ],
        }

        LOGGER.debug(
            "CorePlugin emitting %s for %s → %s",
            action_type,
            source_path,
            target_path,
        )

        return [action]

    # =========================================================================
    # Execution: handlers
    # =========================================================================

    def handlers(self) -> list:
        """Return all built-in execution handler classes."""
        # Filesystem handlers
        from dita_package_processor.execution.handlers.fs.fs_copy_map import (
            CopyMapHandler,
        )
        from dita_package_processor.execution.handlers.fs.fs_copy_media import (
            CopyMediaHandler,
        )
        from dita_package_processor.execution.handlers.fs.fs_copy_topic import (
            CopyTopicHandler,
        )

        # Semantic handlers
        from dita_package_processor.execution.handlers.semantic.s_copy_file import (
            CopyFileHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_delete_file import (
            DeleteFileHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_extract_glossary import (
            ExtractGlossaryHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_inject_glossary import (
            InjectGlossaryHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_inject_topicref import (
            InjectTopicrefHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_inject_topicrefs import (
            InjectTopicrefsHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_wrap_map import (
            WrapMapHandler,
        )
        from dita_package_processor.execution.handlers.semantic.s_wrap_map_topicrefs import (
            WrapMapTopicrefsHandler,
        )

        return [
            # Filesystem
            CopyMapHandler,
            CopyTopicHandler,
            CopyMediaHandler,
            # Semantic
            CopyFileHandler,
            DeleteFileHandler,
            WrapMapHandler,
            InjectTopicrefHandler,
            InjectTopicrefsHandler,
            WrapMapTopicrefsHandler,
            InjectGlossaryHandler,
            ExtractGlossaryHandler,
        ]
