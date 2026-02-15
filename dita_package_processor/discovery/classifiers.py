"""
Discovery-time classifiers for DITA packages.

This module adapts declarative pattern evaluation into concrete
classification outcomes used during discovery.

It performs no transformation and no inference beyond deterministic
resolution of emitted pattern evidence.

Contract (Iteration 7 – locked):

• Evidence means something was observed.
• No evidence means nothing was observed.
• Fallback evidence is not evidence and must never appear in output.
• If classification is None:
    - confidence must be None
    - evidence must be []
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from dita_package_processor.discovery.models import DiscoveryArtifact
from dita_package_processor.discovery.patterns import (
    Evidence,
    Pattern,
    PatternEvaluator,
)
from dita_package_processor.knowledge.known_patterns import load_patterns
from dita_package_processor.knowledge.map_types import MapType
from dita_package_processor.knowledge.topic_types import (
    TopicKind,
    TopicType,
)

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Pattern Loading
# =============================================================================


def _load_patterns() -> List[Pattern]:
    """
    Load declarative discovery patterns from YAML and normalize them
    into Pattern objects.
    """
    LOGGER.info("Loading discovery patterns")

    raw = load_patterns()
    patterns: List[Pattern] = []

    for entry in raw["patterns"]:
        pattern = Pattern(
            id=entry["id"],
            applies_to=entry["applies_to"],
            signals=entry["signals"],
            asserts=entry["asserts"],
            rationale=entry.get("rationale", []),
        )
        patterns.append(pattern)

        LOGGER.debug("Loaded pattern: %s", pattern.id)

    LOGGER.info("Total discovery patterns loaded: %d", len(patterns))
    return patterns


_PATTERN_EVALUATOR = PatternEvaluator(_load_patterns())


# =============================================================================
# Public Classifiers
# =============================================================================


def classify_map(*, path: Path, metadata: Dict) -> DiscoveryArtifact:
    """
    Classify a DITA map using declarative pattern evaluation.

    Map classifications are returned as MapType enum values.
    """
    LOGGER.info("Classifying map: %s", path)

    artifact = DiscoveryArtifact(
        path=path,
        artifact_type="map",
        metadata=metadata,
    )

    evidence = _PATTERN_EVALUATOR.evaluate(artifact)
    artifact.evidence = evidence

    LOGGER.debug(
        "Map %s produced %d raw evidence entries",
        path,
        len(evidence),
    )

    _resolve_evidence(artifact, is_topic=False)

    return artifact


def classify_topic(*, path: Path, metadata: Dict) -> DiscoveryArtifact:
    """
    Classify a DITA topic using declarative pattern evaluation.

    Topics are classified using TopicType.
    """
    LOGGER.info("Classifying topic: %s", path)

    artifact = DiscoveryArtifact(
        path=path,
        artifact_type="topic",
        metadata=metadata,
    )

    evidence = _PATTERN_EVALUATOR.evaluate(artifact)
    artifact.evidence = evidence

    LOGGER.debug(
        "Topic %s produced %d raw evidence entries",
        path,
        len(evidence),
    )

    _resolve_evidence(artifact, is_topic=True)

    return artifact


# =============================================================================
# Evidence Resolution
# =============================================================================


def _resolve_evidence(
    artifact: DiscoveryArtifact,
    *,
    is_topic: bool,
) -> None:
    """
    Resolve emitted evidence into classification and confidence.

    Rules
    -----
    1. Only real evidence is kept.
    2. If none → classification=None, confidence=None, evidence=[]
    3. Highest-confidence evidence wins.
    4. Topics produce TopicType classification.
    5. Maps produce MapType classification.
    """
    real = _filter_real_evidence(artifact.evidence)

    if not real:
        LOGGER.info(
            "No real evidence for %s %s; leaving unclassified",
            artifact.artifact_type,
            artifact.path,
        )
        artifact.classification = None
        artifact.confidence = None
        artifact.evidence = []
        return

    best = max(real, key=lambda ev: ev.confidence)

    if is_topic:
        classification = _build_topic_type(best)
        artifact.classification = classification
        artifact.confidence = classification.confidence
    else:
        artifact.classification = _build_map_type(best)
        artifact.confidence = best.confidence

    artifact.evidence = real

    LOGGER.debug(
        "%s %s resolved to %s using pattern %s",
        artifact.artifact_type.capitalize(),
        artifact.path,
        artifact.classification,
        best.pattern_id,
    )


# =============================================================================
# Map Classification
# =============================================================================


def _build_map_type(evidence: Evidence) -> MapType:
    """
    Convert Evidence into MapType.

    Parameters
    ----------
    evidence : Evidence

    Returns
    -------
    MapType
    """
    role = evidence.asserted_role.upper()

    try:
        map_type = MapType[role]
    except KeyError:
        LOGGER.warning(
            "Unknown map role '%s'; defaulting to UNKNOWN",
            role,
        )
        map_type = MapType.UNKNOWN

    LOGGER.debug(
        "Constructed MapType(%s) with confidence=%.2f",
        map_type.value,
        evidence.confidence,
    )

    return map_type


# =============================================================================
# Topic Classification
# =============================================================================


def _build_topic_type(evidence: Evidence) -> TopicType:
    """
    Convert Evidence into TopicType.
    """
    role = evidence.asserted_role.lower()

    try:
        kind = TopicKind(role)
    except ValueError:
        LOGGER.warning(
            "Unknown topic role '%s'; defaulting to UNKNOWN",
            role,
        )
        kind = TopicKind.UNKNOWN

    topic_type = TopicType(
        kind=kind,
        confidence=evidence.confidence,
    )

    LOGGER.debug(
        "Constructed TopicType(kind=%s, confidence=%.2f)",
        topic_type.kind.value,
        topic_type.confidence,
    )

    return topic_type


# =============================================================================
# Evidence Filtering
# =============================================================================


def _filter_real_evidence(
    evidence: List[Evidence],
) -> List[Evidence]:
    """
    Remove fallback / UNKNOWN evidence.

    Real evidence must:
        - assert a concrete role
        - have confidence > 0
    """
    real: List[Evidence] = []

    for ev in evidence:
        if not ev.asserted_role:
            continue

        if ev.asserted_role.upper() == "UNKNOWN":
            continue

        if ev.confidence <= 0:
            continue

        real.append(ev)

    LOGGER.debug(
        "Filtered %d raw evidence entries into %d real entries",
        len(evidence),
        len(real),
    )

    return real