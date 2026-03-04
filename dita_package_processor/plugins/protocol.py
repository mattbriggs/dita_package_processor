"""
Plugin protocol for the DITA Package Processor.

A plugin is a vertical slice that contributes:

    patterns    → discovery signals that classify artifacts
    emit_actions → action dicts emitted during planning, keyed to those patterns
    handlers    → execution handlers that carry out those actions

Design rules
------------
- One plugin = one Python installable package.
- Registration happens automatically via Python entry points; no main code changes.
- Conflict (duplicate pattern ID or duplicate action_type) is a startup error.
- CorePlugin is always loaded first and serves as the reference implementation.

Entry point group: ``dita_package_processor.plugins``

A third-party plugin declares itself in ``pyproject.toml``::

    [project.entry-points."dita_package_processor.plugins"]
    my_plugin = "my_package:plugin"          # module-level instance
    # or
    my_plugin = "my_package:MyPlugin"        # class (will be instantiated)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Type

if TYPE_CHECKING:
    from dita_package_processor.discovery.patterns import Pattern
    from dita_package_processor.execution.registry import ExecutionHandler
    from dita_package_processor.planning.contracts.planning_input import (
        PlanningArtifact,
        PlanningInput,
    )


class DitaPlugin(ABC):
    """
    Abstract base class for all DITA Package Processor plugins.

    Subclass this and implement the abstract properties.
    All other methods have safe empty defaults.

    Minimal viable plugin::

        class MyPlugin(DitaPlugin):
            @property
            def name(self) -> str:
                return "acme.my_plugin"

            @property
            def version(self) -> str:
                return "1.0.0"

    A plugin that adds a new detection pattern and handler::

        class GlossaryPlugin(DitaPlugin):
            @property
            def name(self) -> str:
                return "acme.glossary"

            @property
            def version(self) -> str:
                return "1.0.0"

            def patterns(self) -> List[Pattern]:
                return load_normalized_patterns_from_yaml(
                    Path(__file__).parent / "patterns.yaml"
                )

            def handlers(self) -> List[Type[ExecutionHandler]]:
                return [MyGlossaryHandler]

            def emit_actions(self, artifact, evidence, context):
                roles = {ev.get("asserted_role") for ev in evidence}
                if artifact.artifact_type == "map" and "glossary" in roles:
                    return [{
                        "type": "copy_map",
                        "target": f"target/glossary/{Path(artifact.path).name}",
                        "parameters": {
                            "source_path": artifact.path,
                            "target_path": f"target/glossary/{Path(artifact.path).name}",
                        },
                        "reason": "Glossary map routing",
                        "derived_from_evidence": [
                            ev.get("pattern_id", "") for ev in evidence
                        ],
                    }]
                return []
    """

    # =========================================================================
    # Identity (required)
    # =========================================================================

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique plugin identifier.

        Use reverse-domain notation to avoid conflicts:
        ``"com.example.my_plugin"``
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string (e.g. ``"1.0.0"``)."""

    # =========================================================================
    # Discovery layer (optional)
    # =========================================================================

    def patterns(self) -> "List[Pattern]":
        """
        Discovery patterns this plugin contributes.

        Patterns are evaluated against every artifact during discovery.
        Each matching pattern emits an Evidence record that is forwarded
        to :meth:`emit_actions` via the ``evidence`` parameter.

        Pattern IDs must be globally unique across all loaded plugins.

        :return: List of :class:`~dita_package_processor.discovery.patterns.Pattern`
                 instances.
        """
        return []

    # =========================================================================
    # Planning layer (optional)
    # =========================================================================

    def emit_actions(
        self,
        artifact: "PlanningArtifact",
        evidence: "List[Dict[str, Any]]",
        context: "PlanningInput",
    ) -> "List[Dict[str, Any]]":
        """
        Emit action dicts for a single artifact during planning.

        Called once per artifact, for every loaded plugin, in load order.
        Return an empty list if this plugin does not handle the artifact.

        Each returned dict must conform to the plan action contract::

            {
                "type": str,          # One of the registered action types
                "target": str,        # Package-relative target path
                "parameters": dict,   # Action-specific parameters
                "reason": str,        # Human-readable justification
                "derived_from_evidence": List[str],  # Pattern IDs from evidence
            }

        Do NOT include an ``"id"`` key — the planner assigns IDs.

        Parameters
        ----------
        artifact:
            The artifact being planned. Carries ``path``, ``artifact_type``,
            ``classification``, and ``metadata`` (which includes ``evidence``).
        evidence:
            List of serialized Evidence dicts for this artifact.
            Each dict has: ``pattern_id``, ``asserted_role``, ``confidence``,
            ``rationale``.
        context:
            Full :class:`~dita_package_processor.planning.contracts.planning_input.PlanningInput`
            for the current run — useful for relationship queries.

        :return: List of action template dicts (no ``id`` field).
        """
        return []

    # =========================================================================
    # Execution layer (optional)
    # =========================================================================

    def handlers(self) -> "List[Type[ExecutionHandler]]":
        """
        Execution handler classes this plugin contributes.

        Each class must:
        - inherit from :class:`~dita_package_processor.execution.registry.ExecutionHandler`
        - define a unique ``action_type`` class attribute

        The ``action_type`` must be globally unique across all loaded plugins.

        :return: List of handler classes (not instances).
        """
        return []

    # =========================================================================
    # Dunder helpers
    # =========================================================================

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} version={self.version!r}>"
