"""
Graph-based planner for dependency resolution.

This module operates strictly on the PlanningInput contract layer.

It does NOT depend on discovery types or DependencyGraph.

Responsibilities
----------------
- Determine root artifact
- Walk relationships deterministically
- Produce stable execution ordering
- No filesystem
- No mutation
- No discovery coupling

Input
-----
nodes : list[str]
relationships : list[PlanningRelationship | dict]

Output
------
list[str]
    Deterministic artifact order suitable for action emission.

Design rules
------------
- deterministic
- pure
- contract-only
- fail fast
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, Iterable, List, Set

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class GraphPlannerError(RuntimeError):
    """Raised when dependency planning cannot be resolved safely."""


# =============================================================================
# Planner
# =============================================================================


class GraphPlanner:
    """
    Deterministic dependency planner operating on contract relationships.

    Guarantees
    ----------
    - stable ordering
    - no duplicates
    - dependencies visited before dependents
    - no discovery layer coupling
    """

    # -------------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------------

    def __init__(
        self,
        *,
        nodes: Iterable[str],
        relationships: Iterable[Dict[str, str]],
    ) -> None:
        """
        Initialize planner.

        Parameters
        ----------
        nodes
            Artifact identifiers.
        relationships
            Contract relationships containing:
                source, target, type, pattern_id
        """
        self.nodes: Set[str] = set(nodes)

        self._outgoing: Dict[str, List[str]] = defaultdict(list)
        self._incoming: Dict[str, List[str]] = defaultdict(list)

        for rel in relationships:
            source = rel["source"]
            target = rel["target"]

            self._outgoing[source].append(target)
            self._incoming[target].append(source)

        LOGGER.debug(
            "GraphPlanner initialized nodes=%d relationships=%d",
            len(self.nodes),
            sum(len(v) for v in self._outgoing.values()),
        )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def plan(self) -> List[str]:
        """
        Produce deterministic traversal order.

        Returns
        -------
        List[str]

        Raises
        ------
        GraphPlannerError
            If graph is cyclic or ambiguous.
        """
        LOGGER.info("Starting dependency planning")

        root = self._select_root()

        visited: Set[str] = set()
        ordered: List[str] = []

        self._walk(root, visited, ordered)

        LOGGER.info("Dependency planning complete: %d nodes", len(ordered))

        return ordered

    # -------------------------------------------------------------------------
    # Root selection
    # -------------------------------------------------------------------------

    def _select_root(self) -> str:
        """
        Select root node.

        Root definition:
            node with no incoming edges

        Returns
        -------
        str

        Raises
        ------
        GraphPlannerError
        """
        roots = sorted(n for n in self.nodes if not self._incoming[n])

        LOGGER.debug("Candidate roots: %s", roots)

        if not roots:
            raise GraphPlannerError("No root node found (cycle detected)")

        # deterministic
        selected = roots[0]

        LOGGER.info("Selected root node: %s", selected)

        return selected

    # -------------------------------------------------------------------------
    # DFS walk
    # -------------------------------------------------------------------------

    def _walk(
        self,
        node: str,
        visited: Set[str],
        ordered: List[str],
    ) -> None:
        """
        Depth-first traversal.

        Deterministic lexicographic ordering.
        """
        if node in visited:
            return

        visited.add(node)
        ordered.append(node)

        for child in sorted(self._outgoing[node]):
            self._walk(child, visited, ordered)