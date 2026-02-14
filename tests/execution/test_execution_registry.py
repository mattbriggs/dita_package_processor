"""
Tests for ExecutionHandlerRegistry.

These tests lock the execution registry contract:

- Handlers must declare an action_type.
- Duplicate registrations are forbidden.
- Missing handlers must fail immediately.
- Handler resolution is deterministic.
"""

from __future__ import annotations

import pytest

from dita_package_processor.execution.registry import (
    ExecutionHandler,
    ExecutionHandlerError,
    ExecutionHandlerRegistry,
)


# ---------------------------------------------------------------------------
# Test handlers
# ---------------------------------------------------------------------------


class DummyHandler(ExecutionHandler):
    action_type = "copy_map"

    def execute(self, action: dict):
        pass


class AnotherDummyHandler(ExecutionHandler):
    action_type = "copy_topic"

    def execute(self, action: dict):
        pass


class InvalidHandler:
    pass


class DuplicateHandler(ExecutionHandler):
    action_type = "copy_map"

    def execute(self, action: dict):
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_register_and_resolve_handler() -> None:
    registry = ExecutionHandlerRegistry()

    registry.register(DummyHandler)
    handler_cls = registry.get_handler("copy_map")

    assert handler_cls is DummyHandler


def test_register_multiple_handlers() -> None:
    registry = ExecutionHandlerRegistry()

    registry.register(DummyHandler)
    registry.register(AnotherDummyHandler)

    assert registry.get_handler("copy_map") is DummyHandler
    assert registry.get_handler("copy_topic") is AnotherDummyHandler


def test_register_handler_missing_action_type_fails() -> None:
    registry = ExecutionHandlerRegistry()

    with pytest.raises(ExecutionHandlerError, match="missing valid action_type"):
        registry.register(InvalidHandler)  # type: ignore[arg-type]


def test_duplicate_handler_registration_fails() -> None:
    registry = ExecutionHandlerRegistry()

    registry.register(DummyHandler)

    with pytest.raises(ExecutionHandlerError, match="already registered"):
        registry.register(DuplicateHandler)


def test_missing_handler_lookup_fails() -> None:
    registry = ExecutionHandlerRegistry()

    with pytest.raises(ExecutionHandlerError, match="No execution handler registered"):
        registry.get_handler("copy_missing")


def test_registered_action_types() -> None:
    registry = ExecutionHandlerRegistry()

    registry.register(DummyHandler)
    registry.register(AnotherDummyHandler)

    types = registry.registered_action_types()

    assert types == {"copy_map", "copy_topic"}