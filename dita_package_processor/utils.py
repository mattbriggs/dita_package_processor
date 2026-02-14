"""
General utility functions for the DITA Package Processor.

This module contains small, reusable helpers that do not belong to any
specific processing step.
"""

from __future__ import annotations

import re


def slugify(value: str, max_len: int = 60) -> str:
    """
    Convert a string into a filesystem-friendly slug.

    The transformation:
    - Lowercases the input
    - Removes non-alphanumeric characters (except whitespace and hyphens)
    - Collapses whitespace, underscores, and hyphens into single underscores
    - Trims leading and trailing underscores
    - Truncates the result to ``max_len`` characters

    :param value: Input string to convert.
    :param max_len: Maximum length of the returned slug.
    :return: Normalized slug string.
    """
    normalized = value.strip().lower()

    normalized = re.sub(
        r"[^\w\s-]",
        "",
        normalized,
    )

    normalized = re.sub(
        r"[\s_-]+",
        "_",
        normalized,
    )

    normalized = normalized.strip("_")

    if len(normalized) > max_len:
        return normalized[:max_len]

    return normalized