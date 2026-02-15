"""
Tests for invariant validation.

These tests verify the SINGLE_MAIN_MAP invariant.

Rules
-----
- Exactly one MAIN map must exist.
- Accepts:
    - MapType.MAIN
    - Legacy alias "MAIN_MAP"
- Raw string "MAIN" is NOT a supported classification anymore.
"""

from pathlib import Path

from dita_package_processor.discovery.models import (
    DiscoveryArtifact,
    DiscoveryInventory,
)
from dita_package_processor.knowledge.invariants import (
    validate_single_main_map,
)
from dita_package_processor.knowledge.map_types import MapType


# =============================================================================
# Helpers
# =============================================================================


def _map(path: str, classification):
    return DiscoveryArtifact(
        path=Path(path),
        artifact_type="map",
        classification=classification,
    )


# =============================================================================
# Tests
# =============================================================================


def test_single_main_map_passes_enum() -> None:
    """Exactly one MapType.MAIN must pass."""
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("Main.ditamap", MapType.MAIN))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 0


def test_single_main_map_passes_legacy_alias() -> None:
    """Legacy alias 'MAIN_MAP' must also pass."""
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("Main.ditamap", "MAIN_MAP"))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 0


def test_string_main_is_not_accepted() -> None:
    """
    Raw string 'MAIN' is not a valid invariant classification.
    The invariant layer expects enum or canonical alias.
    """
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("Main.ditamap", "MAIN"))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 1
    assert violations[0].invariant_id == "SINGLE_MAIN_MAP"


def test_no_main_maps_fails() -> None:
    """Zero MAIN maps must produce exactly one violation."""
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("SomeMap.ditamap", None))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 1
    assert violations[0].invariant_id == "SINGLE_MAIN_MAP"


def test_multiple_main_maps_fails() -> None:
    """Multiple MAIN maps must produce exactly one violation."""
    inventory = DiscoveryInventory()

    inventory.add_artifact(_map("Main1.ditamap", MapType.MAIN))
    inventory.add_artifact(_map("Main2.ditamap", MapType.MAIN))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 1
    assert violations[0].invariant_id == "SINGLE_MAIN_MAP"