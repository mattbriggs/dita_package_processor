"""
Pattern evaluation for DITA discovery.

This module defines the declarative pattern model and the evaluation
engine that converts observed discovery signals into evidence.

It performs **no resolution**, **no ranking**, and **no inference**.
It only answers the question:

    “Given this artifact and these signals, what evidence exists?”

Fallback patterns are *classification helpers*, not semantic evidence.
They only fire when explicitly enabled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dita_package_processor.discovery.models import DiscoveryArtifact

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Pattern:
    """
    Declarative structural pattern.
    """

    id: str
    applies_to: str
    signals: Dict[str, Any]
    asserts: Dict[str, Any]
    rationale: List[str]


@dataclass(frozen=True)
class Evidence:
    """
    Evidence emitted when a pattern matches an artifact.
    """

    pattern_id: str
    artifact_path: Path
    asserted_role: str
    confidence: float
    rationale: List[str]


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class PatternEvaluator:
    """
    Evaluates patterns against a single discovery artifact.

    Supports two modes:

    1. Observation mode (default)
       - fallback patterns are ignored
       - discovery is silent if no semantic evidence exists

    2. Classification mode (allow_fallback=True)
       - fallback patterns fire if no other patterns match
    """

    def __init__(self, patterns: Iterable[Pattern]) -> None:
        self.patterns: List[Pattern] = list(patterns)
        LOGGER.debug(
            "PatternEvaluator initialized with %d patterns",
            len(self.patterns),
        )

    def evaluate(
        self,
        artifact: DiscoveryArtifact,
        *,
        allow_fallback: bool = False,
    ) -> List[Evidence]:
        """
        Evaluate all patterns against a discovery artifact.

        :param artifact: Discovery artifact to evaluate.
        :param allow_fallback: Enable fallback emission when no other
                              patterns match (classification mode).
        :return: List of emitted evidence.
        """
        LOGGER.debug(
            "Evaluating patterns for artifact: path=%s type=%s allow_fallback=%s",
            artifact.path,
            artifact.artifact_type,
            allow_fallback,
        )

        applicable = [
            pattern
            for pattern in self.patterns
            if pattern.applies_to == artifact.artifact_type
        ]

        non_fallback = [
            p for p in applicable if not p.signals.get("fallback", False)
        ]

        fallback = [
            p for p in applicable if p.signals.get("fallback", False)
        ]

        evidence: List[Evidence] = []

        # --------------------------------------------------
        # Phase 1: semantic patterns
        # --------------------------------------------------

        for pattern in non_fallback:
            LOGGER.debug("Evaluating pattern: %s", pattern.id)

            if self._matches(pattern, artifact):
                LOGGER.debug(
                    "Pattern matched: %s (artifact=%s)",
                    pattern.id,
                    artifact.path,
                )
                evidence.append(self._emit(pattern, artifact))
            else:
                LOGGER.debug(
                    "Pattern did not match: %s (artifact=%s)",
                    pattern.id,
                    artifact.path,
                )

        # Semantic evidence always suppresses fallback
        if evidence:
            return evidence

        # --------------------------------------------------
        # Phase 2: fallback (classification-only)
        # --------------------------------------------------

        if allow_fallback and fallback:
            LOGGER.debug(
                "No semantic patterns matched. Emitting fallback: %s",
                fallback[0].id,
            )
            return [self._emit(fallback[0], artifact)]

        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _matches(self, pattern: Pattern, artifact: DiscoveryArtifact) -> bool:
        """
        Determine whether a pattern matches an artifact.

        Unknown signal types fail closed.
        """
        metadata: Dict[str, Any] = artifact.metadata or {}

        for key, condition in pattern.signals.items():
            if key == "fallback":
                continue

            if key == "filename":
                expected = condition.get("equals")
                if artifact.path.name != expected:
                    return False

            elif key == "contains":
                for requirement in condition:
                    element = requirement.get("element")
                    flag = metadata.get(f"contains_{element}", False)
                    if not flag:
                        return False

            elif key == "root_element":
                expected = condition.get("equals")
                actual = metadata.get("root_element")
                if actual != expected:
                    return False

            elif key == "package":
                LOGGER.debug(
                    "Package-level signal ignored during artifact evaluation"
                )
                return False

            else:
                LOGGER.warning(
                    "Unknown signal '%s' in pattern '%s'. Failing closed.",
                    key,
                    pattern.id,
                )
                return False

        return True

    def _emit(self, pattern: Pattern, artifact: DiscoveryArtifact) -> Evidence:
        """
        Emit an Evidence instance.
        """
        return Evidence(
            pattern_id=pattern.id,
            artifact_path=artifact.path,
            asserted_role=pattern.asserts["role"],
            confidence=pattern.asserts["confidence"],
            rationale=pattern.rationale,
        )