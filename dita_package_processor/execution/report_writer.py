"""
Execution report writer.

This module is responsible for writing an ExecutionReport to disk in a
deterministic and reproducible way.

Determinism rules:
- Keys must be sorted.
- Indentation must be stable.
- UTF-8 encoding must be enforced.
- No implicit mutations of the report structure.
- Output must be byte-for-byte reproducible for the same input.

This module is the final serialization boundary of the execution layer.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.execution.models import ExecutionReport

LOGGER = logging.getLogger(__name__)


class ExecutionReportWriteError(RuntimeError):
    """
    Raised when an execution report cannot be written to disk.

    These are hard failures that indicate filesystem or serialization problems.
    """


class ExecutionReportWriter:
    """
    Deterministic writer for ExecutionReport objects.

    This class owns all disk serialization semantics for execution reports.
    """

    def __init__(
        self,
        *,
        indent: int = 2,
        sort_keys: bool = True,
        ensure_ascii: bool = False,
    ) -> None:
        """
        Initialize the writer.

        :param indent: JSON indentation level.
        :param sort_keys: Whether to sort dictionary keys.
        :param ensure_ascii: Whether to escape non-ASCII characters.
        """
        self._indent = indent
        self._sort_keys = sort_keys
        self._ensure_ascii = ensure_ascii

        LOGGER.debug(
            "ExecutionReportWriter initialized indent=%s sort_keys=%s ensure_ascii=%s",
            indent,
            sort_keys,
            ensure_ascii,
        )

    def write(
        self,
        *,
        report: ExecutionReport,
        path: Path,
    ) -> None:
        """
        Write an ExecutionReport to disk.

        :param report: ExecutionReport instance.
        :param path: Target file path.
        :raises ExecutionReportWriteError: If writing fails.
        """
        LOGGER.info("Writing execution report to %s", path)

        try:
            payload: Dict[str, Any] = report.to_dict()
            serialized = json.dumps(
                payload,
                indent=self._indent,
                sort_keys=self._sort_keys,
                ensure_ascii=self._ensure_ascii,
            )

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(serialized, encoding="utf-8")

            LOGGER.debug(
                "Execution report written (%d bytes) to %s",
                len(serialized.encode("utf-8")),
                path,
            )

        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "Failed to write execution report to %s: %s",
                path,
                exc,
                exc_info=True,
            )
            raise ExecutionReportWriteError(
                f"Failed to write execution report to {path}"
            ) from exc