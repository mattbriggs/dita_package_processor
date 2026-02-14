"""
Base interfaces for processing steps.

This module defines the abstract base class used by all processing
steps in the DITA Package Processor pipeline.
"""

from __future__ import annotations

import abc
import logging

from dita_package_processor.context import ProcessingContext


class ProcessingStep(abc.ABC):
    """
    Abstract base class for all processing steps.

    Each processing step represents a single, isolated transformation
    applied to a DITA package. Steps are executed sequentially by the
    pipeline and share state exclusively through the ProcessingContext.

    Subclasses must implement the ``run`` method.
    """

    #: Canonical step name used for registration and logging.
    name: str = "unnamed-step"

    @abc.abstractmethod
    def run(
        self,
        context: ProcessingContext,
        logger: logging.Logger,
    ) -> None:
        """
        Execute the processing step.

        Implementations should perform a single, well-defined operation
        and must not invoke other steps directly.

        :param context: Shared processing context containing package state.
        :param logger: Logger instance scoped to the processor.
        :raises Exception: Implementations may raise exceptions to signal
            unrecoverable errors.
        """
        raise NotImplementedError