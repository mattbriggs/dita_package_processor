"""
Tests for invariant validation.

These tests verify the SINGLE_MAIN_MAP invariant:

Rules:
- exactly one main map must exist
- accepts MapType enum OR string contract values
"""

from dita_package_processor.discovery.models import (
    DiscoveryArtifact,
    DiscoveryInventory,
)
from dita_package_processor.knowledge.invariants import (
    validate_single_main_map,
)
from dita_package_processor.knowledge.map_types import MapType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _map(path: str, classification):
    return DiscoveryArtifact(
        path=path,
        artifact_type="map",
        classification=classification,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_single_main_map_passes_enum() -> None:
    """
    Exactly one MapType.MAIN must pass.
    """
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("Main.ditamap", MapType.MAIN))

    violations = validate_single_main_map(inventory)

    assert violations == []


def test_single_main_map_passes_string() -> None:
    """
    String contract value "MAIN_MAP" must also pass.
    """
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("Main.ditamap", "MAIN_MAP"))

    violations = validate_single_main_map(inventory)

    assert violations == []


def test_no_main_maps_fails() -> None:
    """
    Zero main maps must fail.
    """
    inventory = DiscoveryInventory()
    inventory.add_artifact(_map("SomeMap.ditamap", None))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 1


def test_multiple_main_maps_fails() -> None:
    """
    Multiple main maps must fail.
    """
    inventory = DiscoveryInventory()

    inventory.add_artifact(_map("Main1.ditamap", MapType.MAIN))
    inventory.add_artifact(_map("Main2.ditamap", MapType.MAIN))

    violations = validate_single_main_map(inventory)

    assert len(violations) == 1