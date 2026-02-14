"""
Dependency graph data structures for discovery.

This module defines the read-only graph model derived from discovery output.

Discovery is authoritative.
The graph is a computed structure.

Schema contract:
- discovery.relationships use: from / to / type / pattern_id
- graph edges use: source / target / type / pattern_id

This module:
- consumes discovery relationships
- emits a stable graph contract
- never invents structure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DependencyEdge
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyEdge:
    """
    Directed relationship between two artifacts.

    :param source: Source artifact path.
    :param target: Target artifact path.
    :param edge_type: Relationship type (topicref, image, xref, etc).
    :param pattern_id: Discovery pattern identifier.
    """

    source: str
    target: str
    edge_type: str
    pattern_id: str

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize edge to graph contract.

        Output:
        {
          "source": "...",
          "target": "...",
          "type": "...",
          "pattern_id": "..."
        }
        """
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "pattern_id": self.pattern_id,
        }

    @classmethod
    def from_relationship(cls, data: Dict[str, Any]) -> "DependencyEdge":
        """
        Build edge from discovery.relationship entry.

        Expected keys:
        - from
        - to
        - type
        - pattern_id
        """
        try:
            return cls(
                source=str(data["source"]),
                target=str(data["target"]),
                edge_type=str(data["type"]),
                pattern_id=str(data["pattern_id"]),
            )
        except KeyError as exc:
            raise KeyError(
                f"Relationship missing required field: {exc}"
            ) from exc

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyEdge":
        """
        Build edge from graph serialization.

        Expected keys:
        - source
        - target
        - type
        - pattern_id
        """
        try:
            return cls(
                source=str(data["source"]),
                target=str(data["target"]),
                edge_type=str(data["type"]),
                pattern_id=str(data["pattern_id"]),
            )
        except KeyError as exc:
            raise KeyError(
                f"Graph edge missing required field: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# DependencyGraph
# ---------------------------------------------------------------------------


@dataclass
class DependencyGraph:
    """
    Derived dependency graph.

    Nodes are artifact paths.
    Edges are DependencyEdge instances.
    """

    nodes: Set[str] = field(default_factory=set)
    edges: List[DependencyEdge] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Canonical constructor
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_artifact_path(path: str) -> str | None:
        """
        Normalize a relationship endpoint to its artifact (file) path.

        Cases:
            file.dita#id  -> file.dita
            file.dita     -> file.dita
            #id           -> None (intra-file reference)

        :param path: Relationship endpoint path.
        :return: File-level artifact path or None if fragment-only.
        """
        if path.startswith("#"):
            return None

        return path.split("#", 1)[0]

    @classmethod
    def from_discovery(
        cls,
        *,
        artifacts: Iterable[Dict[str, Any]],
        relationships: Iterable[Dict[str, Any]],
    ) -> "DependencyGraph":
        """
        Build a graph from discovery JSON.

        Discovery is authoritative.
        Graph must not contain unknown nodes.

        :param artifacts: discovery["artifacts"]
        :param relationships: discovery["relationships"]
        """
        LOGGER.info("Building DependencyGraph from discovery contract")

        graph = cls()

        artifact_paths: Set[str] = set()
        for art in artifacts:
            path = art.get("path")
            if not path:
                raise ValueError(f"Artifact missing required path: {art}")
            artifact_paths.add(str(path))
            graph.nodes.add(str(path))

        for rel in relationships:
            edge = DependencyEdge.from_relationship(rel)

            def _normalize(value: str) -> str | None:
                if value.startswith("#"):
                    return None
                return value.split("#", 1)[0]

            src = _normalize(edge.source)
            tgt = _normalize(edge.target)

            if src and src not in artifact_paths:
                raise ValueError(f"Relationship source not in artifacts: {edge.source}")

            if tgt and tgt not in artifact_paths:
                raise ValueError(f"Relationship target not in artifacts: {edge.target}")

            graph.edges.append(edge)

        LOGGER.info(
            "DependencyGraph constructed: %d nodes, %d edges",
            len(graph.nodes),
            len(graph.edges),
        )
        return graph

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def incoming(self, node: str) -> List[DependencyEdge]:
        """Edges that point to node."""
        return [e for e in self.edges if e.target == node]

    def outgoing(self, node: str) -> List[DependencyEdge]:
        """Edges that originate from node."""
        return [e for e in self.edges if e.source == node]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, object]:
        """
        Serialize graph.

        {
          "nodes": [...],
          "edges": [...]
        }
        """
        LOGGER.debug("Serializing DependencyGraph")
        return {
            "nodes": sorted(self.nodes),
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "DependencyGraph":
        """
        Deserialize from graph serialization, not discovery JSON.
        """
        LOGGER.debug("Deserializing DependencyGraph")

        graph = cls()

        for node in data.get("nodes", []):
            graph.nodes.add(str(node))

        for edge_data in data.get("edges", []):
            edge = DependencyEdge.from_dict(edge_data)
            graph.edges.append(edge)

        return graph