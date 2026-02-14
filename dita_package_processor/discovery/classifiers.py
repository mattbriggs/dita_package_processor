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

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pattern loading (performed once at import time)
# ---------------------------------------------------------------------------


def _load_patterns() -> List[Pattern]:
    """
    Load declarative discovery patterns from YAML and normalize them
    into :class:`Pattern` objects.

    :return: List of normalized Pattern instances.
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


#: Shared evaluator instance used for all discovery classifications.
_PATTERN_EVALUATOR = PatternEvaluator(_load_patterns())


# ---------------------------------------------------------------------------
# Public classifier functions (external contract)
# ---------------------------------------------------------------------------


def classify_map(*, path: Path, metadata: Dict) -> DiscoveryArtifact:
    """
    Classify a DITA map using declarative pattern evaluation.

    If no real evidence exists, the artifact remains unclassified:
        - classification = None
        - confidence = None
        - evidence = []

    :param path: Filesystem path to the map file.
    :param metadata: Discovery metadata extracted upstream.
    :return: Classified DiscoveryArtifact instance.
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

    _resolve_evidence(artifact)

    return artifact


def classify_topic(*, path: Path, metadata: Dict) -> DiscoveryArtifact:
    """
    Classify a DITA topic using declarative pattern evaluation.

    If no real evidence exists, the artifact remains unclassified:
        - classification = None
        - confidence = None
        - evidence = []

    :param path: Filesystem path to the topic file.
    :param metadata: Discovery metadata extracted upstream.
    :return: Classified DiscoveryArtifact instance.
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

    _resolve_evidence(artifact)

    return artifact


# ---------------------------------------------------------------------------
# Evidence resolution (shared logic)
# ---------------------------------------------------------------------------


def _resolve_evidence(artifact: DiscoveryArtifact) -> None:
    """
    Resolve emitted evidence into classification and confidence.

    Rules:

    1. Only *real* evidence is kept.
       Fallback or UNKNOWN evidence is discarded.
    2. If no real evidence exists:
        - classification = None
        - confidence = None
        - evidence = []
    3. If real evidence exists:
        - highest-confidence entry wins
        - classification = asserted_role
        - confidence = evidence.confidence
        - evidence = [real evidence only]

    :param artifact: DiscoveryArtifact to update.
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

    artifact.classification = best.asserted_role
    artifact.confidence = best.confidence
    artifact.evidence = real

    LOGGER.debug(
        "%s %s resolved to %s using pattern %s",
        artifact.artifact_type.capitalize(),
        artifact.path,
        artifact.classification,
        best.pattern_id,
    )


def _filter_real_evidence(evidence: List[Evidence]) -> List[Evidence]:
    """
    Remove fallback / UNKNOWN evidence.

    Real evidence must:
        - assert a concrete role
        - have a confidence > 0
        - not be marked as fallback

    :param evidence: Raw evidence list.
    :return: Filtered real evidence list.
    """
    real: List[Evidence] = []

    for ev in evidence:
        if ev.asserted_role is None:
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