"""
Invariant definitions for DITA package processing.

This module defines *invariants*: conditions that must hold true for a
DITA package to be safely processed by the pipeline.

Invariants differ from validation rules:

- Validation answers: "Is this document well-formed or schema-valid?"
- Invariants answer: "Is this package *structurally processable*?"

Invariant violations are always fatal and must halt execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dita_package_processor.discovery.models import DiscoveryInventory
from dita_package_processor.knowledge.map_types import MapType

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvariantViolation:
    """
    Represents a violation of a structural invariant.

    Violations are immutable and descriptive. They do not attempt to
    recover or suggest fixes.
    """

    #: Stable identifier for the invariant.
    invariant_id: str

    #: Human-readable description of the violation.
    message: str

    #: Optional filesystem path associated with the violation.
    path: Optional[Path] = None


# ---------------------------------------------------------------------------
# Discovery-based invariants
# ---------------------------------------------------------------------------


def validate_single_main_map(
    inventory: DiscoveryInventory,
) -> List[InvariantViolation]:
    """
    Validate that exactly one main map exists in the discovery inventory.

    Accepts either:
    - MapType enum values
    - string contract values ("MAIN_MAP")

    This keeps invariants tolerant of internal vs serialized
    classification representations.
    """
    LOGGER.debug("Validating invariant: SINGLE_MAIN_MAP")

    def _is_main(classification: object) -> bool:
        if classification is None:
            return False

        # enum support
        if classification == MapType.MAIN:
            return True

        # string support (discovery/report contract)
        if str(classification).upper() == "MAIN_MAP":
            return True

        return False

    main_maps = [
        artifact
        for artifact in inventory.artifacts
        if artifact.artifact_type == "map"
        and _is_main(artifact.classification)
    ]

    LOGGER.debug("Found %d main map(s)", len(main_maps))

    if len(main_maps) == 1:
        LOGGER.debug("Invariant SINGLE_MAIN_MAP satisfied")
        return []

    violation = InvariantViolation(
        invariant_id="SINGLE_MAIN_MAP",
        message=(
            f"Expected exactly one main map, "
            f"found {len(main_maps)}."
        ),
    )

    LOGGER.error("Invariant violation: %s", violation)
    return [violation]


# ---------------------------------------------------------------------------
# Filesystem invariants
# ---------------------------------------------------------------------------


def invariant_package_root_exists(
    package_dir: Path,
) -> List[InvariantViolation]:
    """
    Ensure the package root directory exists and is a directory.

    :param package_dir: Root directory of the DITA package.
    :return: List of invariant violations (empty if none).
    """
    LOGGER.debug("Validating invariant: PACKAGE_ROOT_EXISTS (%s)", package_dir)

    if not package_dir.exists():
        violation = InvariantViolation(
            invariant_id="PACKAGE_ROOT_MISSING",
            message="DITA package root directory does not exist.",
            path=package_dir,
        )
        LOGGER.error("Invariant violation: %s", violation)
        return [violation]

    if not package_dir.is_dir():
        violation = InvariantViolation(
            invariant_id="PACKAGE_ROOT_NOT_DIRECTORY",
            message="DITA package root path is not a directory.",
            path=package_dir,
        )
        LOGGER.error("Invariant violation: %s", violation)
        return [violation]

    LOGGER.debug("Invariant PACKAGE_ROOT_EXISTS satisfied")
    return []


def invariant_topics_directory_present(
    package_dir: Path,
) -> List[InvariantViolation]:
    """
    Ensure the ``topics/`` directory exists under the package root.

    :param package_dir: Root directory of the DITA package.
    :return: List of invariant violations (empty if none).
    """
    LOGGER.debug("Validating invariant: TOPICS_DIRECTORY_PRESENT")

    topics_dir = package_dir / "topics"

    if not topics_dir.exists():
        violation = InvariantViolation(
            invariant_id="TOPICS_DIR_MISSING",
            message="DITA package is missing required 'topics/' directory.",
            path=topics_dir,
        )
        LOGGER.error("Invariant violation: %s", violation)
        return [violation]

    if not topics_dir.is_dir():
        violation = InvariantViolation(
            invariant_id="TOPICS_PATH_NOT_DIRECTORY",
            message="'topics/' exists but is not a directory.",
            path=topics_dir,
        )
        LOGGER.error("Invariant violation: %s", violation)
        return [violation]

    LOGGER.debug("Invariant TOPICS_DIRECTORY_PRESENT satisfied")
    return []


def invariant_contains_ditamap(
    package_dir: Path,
) -> List[InvariantViolation]:
    """
    Ensure the package contains at least one ``.ditamap`` file.

    :param package_dir: Root directory of the DITA package.
    :return: List of invariant violations (empty if none).
    """
    LOGGER.debug("Validating invariant: CONTAINS_DITAMAP")

    maps = list(package_dir.glob("*.ditamap"))
    LOGGER.debug("Found %d .ditamap file(s)", len(maps))

    if not maps:
        violation = InvariantViolation(
            invariant_id="NO_DITAMAPS_FOUND",
            message="DITA package contains no '.ditamap' files.",
            path=package_dir,
        )
        LOGGER.error("Invariant violation: %s", violation)
        return [violation]

    LOGGER.debug("Invariant CONTAINS_DITAMAP satisfied")
    return []


# ---------------------------------------------------------------------------
# Invariant evaluation
# ---------------------------------------------------------------------------


def evaluate_invariants(
    package_dir: Path,
) -> List[InvariantViolation]:
    """
    Evaluate all filesystem-level invariants for a DITA package.

    :param package_dir: Root directory of the DITA package.
    :return: List of invariant violations.
    """
    LOGGER.info("Evaluating filesystem invariants for %s", package_dir)

    violations: List[InvariantViolation] = []

    checks = [
        invariant_package_root_exists,
        invariant_topics_directory_present,
        invariant_contains_ditamap,
    ]

    for check in checks:
        LOGGER.debug("Running invariant check: %s", check.__name__)
        violations.extend(check(package_dir))

    if violations:
        LOGGER.warning(
            "Invariant evaluation completed with %d violation(s)",
            len(violations),
        )
    else:
        LOGGER.info("All filesystem invariants satisfied")

    return violations


def assert_invariants(package_dir: Path) -> None:
    """
    Assert that all filesystem invariants hold for the DITA package.

    :param package_dir: Root directory of the DITA package.
    :raises RuntimeError: If any invariant is violated.
    """
    LOGGER.info("Asserting invariants for %s", package_dir)

    violations = evaluate_invariants(package_dir)

    if violations:
        messages = [
            f"[{v.invariant_id}] {v.message}"
            + (f" ({v.path})" if v.path else "")
            for v in violations
        ]
        error_message = (
            "Invariant violations detected:\n" + "\n".join(messages)
        )

        LOGGER.critical(error_message)
        raise RuntimeError(error_message)

    LOGGER.info("All invariants satisfied; safe to proceed")