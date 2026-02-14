"""
Execution handler registry.

This module defines a strict registry that maps plan action types to concrete
execution handlers.

The registry is the only legal mechanism for dispatching actions to handlers.
There is no dynamic discovery, no reflection, and no guessing.

If an action type is not registered, execution must fail — unless a wildcard
handler is explicitly registered (used for dry-run execution).
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional, Type

LOGGER = logging.getLogger(__name__)


class ExecutionHandlerError(RuntimeError):
    """
    Raised when execution handlers are misconfigured or missing.

    These are structural errors and must halt execution immediately.
    """


class ExecutionHandler:
    """
    Abstract base class for all execution handlers.

    Concrete handlers must implement:

        - action_type: class attribute
        - execute(action: dict) -> ExecutionActionResult

    This base class exists only to define the interface contract.
    """

    action_type: str

    def execute(self, action: dict):
        """
        Execute a single plan action.

        :param action: Action dictionary from the plan.
        :return: ExecutionActionResult
        """
        raise NotImplementedError("Execution handlers must implement execute()")


class ExecutionHandlerRegistry:
    """
    Registry for mapping action types to execution handlers.

    This is a strict, closed system:
    - Handlers must be explicitly registered.
    - Duplicate registrations are forbidden.
    - Missing handlers cause immediate failure unless a wildcard handler
      has been registered.

    The wildcard handler ("*") is intended exclusively for dry-run execution.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Type[ExecutionHandler]] = {}
        self._default_handler: Optional[Type[ExecutionHandler]] = None
        LOGGER.debug("Initialized empty ExecutionHandlerRegistry")

    def register(self, handler_cls: Type[ExecutionHandler]) -> None:
        """
        Register a handler class.

        The handler class must define a unique ``action_type`` attribute.

        Special case:
            action_type="*" registers a wildcard fallback handler.

        :param handler_cls: Handler class to register.
        :raises ExecutionHandlerError: If invalid or duplicate.
        """
        action_type = getattr(handler_cls, "action_type", None)

        if not action_type or not isinstance(action_type, str):
            raise ExecutionHandlerError(
                f"Handler {handler_cls.__name__} missing valid action_type"
            )

        if action_type == "*":
            if self._default_handler is not None:
                raise ExecutionHandlerError(
                    "Wildcard handler already registered"
                )
            self._default_handler = handler_cls
            LOGGER.info(
                "Registered wildcard execution handler %s",
                handler_cls.__name__,
            )
            return

        if action_type in self._handlers:
            raise ExecutionHandlerError(
                f"Handler already registered for action_type '{action_type}'"
            )

        self._handlers[action_type] = handler_cls
        LOGGER.info(
            "Registered execution handler %s for action_type '%s'",
            handler_cls.__name__,
            action_type,
        )

    def get_handler(self, action_type: str) -> Type[ExecutionHandler]:
        """
        Retrieve a handler class for an action type.

        Resolution order:
        1. Exact action_type match
        2. Wildcard handler (if registered)
        3. Failure

        :param action_type: Action type string.
        :return: Handler class.
        :raises ExecutionHandlerError: If not registered.
        """
        if action_type in self._handlers:
            handler = self._handlers[action_type]
            LOGGER.debug(
                "Resolved handler %s for action_type '%s'",
                handler.__name__,
                action_type,
            )
            return handler

        if self._default_handler is not None:
            LOGGER.debug(
                "Resolved wildcard handler %s for action_type '%s'",
                self._default_handler.__name__,
                action_type,
            )
            return self._default_handler

        raise ExecutionHandlerError(
            f"No execution handler registered for action_type '{action_type}'"
        )

    def registered_action_types(self) -> set[str]:
        """
        Return the set of registered concrete action types.

        Wildcard is excluded.

        :return: Set of action type strings.
        """
        return set(self._handlers.keys())