"""
Pattern evaluation for DITA discovery.

This module defines the declarative pattern model and the evaluation
engine that converts observed discovery signals into evidence.

It performs:

- No resolution
- No ranking
- No inference
- No mutation

It only answers:

    “Given this artifact and these signals, what evidence exists?”

Fallback patterns are classification helpers only.
They fire only when explicitly enabled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dita_package_processor.discovery.models import DiscoveryArtifact

LOGGER = logging.getLogger(__name__)

_ALLOWED_ARTIFACT_TYPES = {"map", "topic", "media"}


# =============================================================================
# Pattern Model
# =============================================================================


@dataclass(frozen=True)
class Pattern:
    """
    Declarative structural pattern.

    Parameters
    ----------
    id : str
        Unique pattern identifier.
    applies_to : str
        Artifact type this pattern applies to.
    signals : Dict[str, Any]
        Signal requirements.
    asserts : Dict[str, Any]
        Assertion payload. Must contain:
            - role
            - confidence
    rationale : List[str]
        Human-readable reasoning.
    """

    id: str
    applies_to: str
    signals: Dict[str, Any]
    asserts: Dict[str, Any]
    rationale: List[str]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Pattern.id must be non-empty")

        if self.applies_to not in _ALLOWED_ARTIFACT_TYPES:
            raise ValueError(
                f"Invalid applies_to: {self.applies_to}"
            )

        if not isinstance(self.signals, dict):
            raise ValueError("Pattern.signals must be dict")

        if not isinstance(self.asserts, dict):
            raise ValueError("Pattern.asserts must be dict")

        if "role" not in self.asserts:
            raise ValueError("Pattern.asserts must contain 'role'")

        if "confidence" not in self.asserts:
            raise ValueError("Pattern.asserts must contain 'confidence'")

        confidence = self.asserts["confidence"]

        if not isinstance(confidence, (float, int)):
            raise ValueError("Pattern.asserts.confidence must be numeric")

        if not (0.0 <= float(confidence) <= 1.0):
            raise ValueError("Pattern.asserts.confidence must be 0–1")

        if not isinstance(self.rationale, list):
            raise ValueError("Pattern.rationale must be list")

        LOGGER.debug("Pattern validated: %s", self.id)


# =============================================================================
# Evidence Model
# =============================================================================


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

    def __post_init__(self) -> None:
        if not self.pattern_id:
            raise ValueError("Evidence.pattern_id required")

        if not isinstance(self.artifact_path, Path):
            raise ValueError("Evidence.artifact_path must be Path")

        if not self.asserted_role:
            raise ValueError("Evidence.asserted_role required")

        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError("Evidence.confidence must be 0–1")

        LOGGER.debug(
            "Evidence emitted: pattern=%s artifact=%s role=%s",
            self.pattern_id,
            self.artifact_path,
            self.asserted_role,
        )


# =============================================================================
# Pattern Evaluator
# =============================================================================


class PatternEvaluator:
    """
    Evaluate patterns against a single discovery artifact.

    Modes
    -----
    Observation mode (default)
        - fallback patterns ignored

    Classification mode (allow_fallback=True)
        - fallback patterns fire only if no semantic match
    """

    def __init__(self, patterns: Iterable[Pattern]) -> None:
        self.patterns: List[Pattern] = list(patterns)

        LOGGER.debug(
            "PatternEvaluator initialized with %d patterns",
            len(self.patterns),
        )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def evaluate(
        self,
        artifact: DiscoveryArtifact,
        *,
        allow_fallback: bool = False,
    ) -> List[Evidence]:
        """
        Evaluate all patterns against an artifact.

        Parameters
        ----------
        artifact : DiscoveryArtifact
            Artifact to evaluate.
        allow_fallback : bool
            Enable fallback emission if no semantic match.

        Returns
        -------
        List[Evidence]
        """
        LOGGER.debug(
            "Evaluating artifact=%s type=%s allow_fallback=%s",
            artifact.path,
            artifact.artifact_type,
            allow_fallback,
        )

        applicable = [
            pattern
            for pattern in self.patterns
            if pattern.applies_to == artifact.artifact_type
        ]

        semantic_patterns = [
            p for p in applicable if not p.signals.get("fallback", False)
        ]

        fallback_patterns = [
            p for p in applicable if p.signals.get("fallback", False)
        ]

        evidence: List[Evidence] = []

        # --------------------------------------------------------------
        # Phase 1: semantic patterns
        # --------------------------------------------------------------

        for pattern in semantic_patterns:
            if self._matches(pattern, artifact):
                evidence.append(self._emit(pattern, artifact))

        if evidence:
            return evidence

        # --------------------------------------------------------------
        # Phase 2: fallback (deterministic)
        # --------------------------------------------------------------

        if allow_fallback and fallback_patterns:
            # Deterministic fallback: lowest pattern id
            selected = sorted(
                fallback_patterns,
                key=lambda p: p.id,
            )[0]

            LOGGER.debug(
                "Fallback pattern selected: %s",
                selected.id,
            )

            return [self._emit(selected, artifact)]

        return []

    # ---------------------------------------------------------------------
    # Internal
    # ---------------------------------------------------------------------

    def _matches(
        self,
        pattern: Pattern,
        artifact: DiscoveryArtifact,
    ) -> bool:
        """
        Determine whether a pattern matches an artifact.

        Unknown signals fail closed.
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
                    flag = metadata.get(
                        f"contains_{element}",
                        False,
                    )
                    if not flag:
                        return False

            elif key == "root_element":
                expected = condition.get("equals")
                actual = metadata.get("root_element")
                if actual != expected:
                    return False

            elif key == "package":
                # Artifact-level evaluator cannot evaluate package signals
                return False

            else:
                LOGGER.warning(
                    "Unknown signal '%s' in pattern '%s'. Failing closed.",
                    key,
                    pattern.id,
                )
                return False

        return True

    def _emit(
        self,
        pattern: Pattern,
        artifact: DiscoveryArtifact,
    ) -> Evidence:
        """
        Emit Evidence from matched pattern.
        """
        return Evidence(
            pattern_id=pattern.id,
            artifact_path=artifact.path,
            asserted_role=str(pattern.asserts["role"]),
            confidence=float(pattern.asserts["confidence"]),
            rationale=list(pattern.rationale),
        )