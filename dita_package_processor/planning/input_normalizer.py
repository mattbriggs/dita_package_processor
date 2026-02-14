"""
Discovery input normalizer (legacy compatibility layer).

This module exists to normalize older discovery JSON formats that still expose
graph structures. It is NOT part of the new contract boundary.

The new, canonical boundary is:

    discovery.json
        → planning/contracts/discovery_to_planning.py
        → PlanningInput

This module remains only for historical pipeline compatibility and migration
support. Planning MUST NOT depend on this module.

Responsibilities:
- Canonicalize paths
- Remove media artifacts from graph topology
- Remove edges involving media
- Ensure graph nodes reference known artifacts
- Perform no inference and no guessing
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Set

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


def _normalize_path(path: str) -> str:
    """
    Canonicalize a discovery path.

    Rules:
    - Convert to POSIX format
    - Strip leading './'
    - No filesystem access
    - No guessing

    :param path: Raw discovery path.
    :return: Canonicalized path.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"Invalid artifact path: {path!r}")

    normalized = Path(path).as_posix().lstrip("./")
    LOGGER.debug("Normalized path: %s → %s", path, normalized)
    return normalized


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------


class PlanningInputNormalizer:
    """
    Normalize legacy discovery graph output into planner-compatible structure.

    WARNING:
        This is NOT the new contract bridge.
        The canonical bridge is planning/contracts/discovery_to_planning.py.

    This class only exists to stabilize older pipeline stages that still expect
    graph-shaped discovery output.
    """

    @staticmethod
    def normalize(discovery: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize legacy discovery input.

        :param discovery: Parsed discovery JSON.
        :return: Normalized structure with semantic-only artifacts and graph.
        :raises ValueError: On structural inconsistency.
        """
        LOGGER.info("Normalizing legacy discovery input")

        if not isinstance(discovery, dict):
            raise ValueError("Discovery input must be an object")

        raw_artifacts = discovery.get("artifacts")
        raw_graph = discovery.get("graph")

        if not isinstance(raw_artifacts, list):
            raise ValueError("discovery.artifacts must be a list")

        if not isinstance(raw_graph, dict):
            raise ValueError("discovery.graph must be an object")

        # ------------------------------------------------------------------
        # Normalize artifacts
        # ------------------------------------------------------------------

        artifacts: List[Dict[str, Any]] = []
        artifact_index: Dict[str, Dict[str, Any]] = {}

        for idx, artifact in enumerate(raw_artifacts):
            if not isinstance(artifact, dict):
                raise ValueError(f"artifact[{idx}] must be an object")

            if "path" not in artifact or "artifact_type" not in artifact:
                raise ValueError(f"artifact[{idx}] missing required fields")

            path = _normalize_path(artifact["path"])

            normalized = dict(artifact)
            normalized["path"] = path

            artifacts.append(normalized)
            artifact_index[path] = normalized

        # Filter out media artifacts
        semantic_artifacts = [
            a for a in artifacts if a.get("artifact_type") != "media"
        ]

        semantic_paths: Set[str] = {a["path"] for a in semantic_artifacts}

        LOGGER.debug(
            "Artifacts normalized: total=%d semantic=%d",
            len(artifacts),
            len(semantic_artifacts),
        )

        # ------------------------------------------------------------------
        # Normalize graph nodes
        # ------------------------------------------------------------------

        raw_nodes = raw_graph.get("nodes")
        if not isinstance(raw_nodes, list):
            raise ValueError("discovery.graph.nodes must be a list")

        normalized_nodes: List[str] = []

        for node in raw_nodes:
            node_path = _normalize_path(node)

            if node_path not in artifact_index:
                LOGGER.error("Graph node references missing artifact: %s", node_path)
                raise ValueError(f"Graph node references missing artifact: {node_path}")

            if artifact_index[node_path]["artifact_type"] != "media":
                normalized_nodes.append(node_path)

        # ------------------------------------------------------------------
        # Normalize edges
        # ------------------------------------------------------------------

        raw_edges = raw_graph.get("edges")
        if not isinstance(raw_edges, list):
            raise ValueError("discovery.graph.edges must be a list")

        normalized_edges: List[Dict[str, Any]] = []

        for idx, edge in enumerate(raw_edges):
            if not isinstance(edge, dict):
                raise ValueError(f"edge[{idx}] must be an object")

            for key in ("source", "target"):
                if key not in edge:
                    raise ValueError(f"edge[{idx}] missing '{key}'")

            src = _normalize_path(edge["source"])
            tgt = _normalize_path(edge["target"])

            if src not in artifact_index or tgt not in artifact_index:
                LOGGER.error("Edge references missing artifact: %s", edge)
                raise ValueError(f"Edge references missing artifact: {edge}")

            # Remove any edges involving media
            if artifact_index[src]["artifact_type"] == "media":
                continue
            if artifact_index[tgt]["artifact_type"] == "media":
                continue

            normalized_edge = dict(edge)
            normalized_edge["source"] = src
            normalized_edge["target"] = tgt
            normalized_edges.append(normalized_edge)

        normalized = {
            "artifacts": semantic_artifacts,
            "graph": {
                "nodes": normalized_nodes,
                "edges": normalized_edges,
            },
        }

        LOGGER.info(
            "Legacy normalization complete: artifacts=%d nodes=%d edges=%d",
            len(semantic_artifacts),
            len(normalized_nodes),
            len(normalized_edges),
        )

        return normalized


# ---------------------------------------------------------------------------
# Functional alias (pipeline ergonomics only)
# ---------------------------------------------------------------------------


def normalize(discovery: Dict[str, Any]) -> Dict[str, Any]:
    """
    Functional wrapper for PlanningInputNormalizer.normalize.

    Exists only for backward pipeline compatibility.
    """
    return PlanningInputNormalizer.normalize(discovery)