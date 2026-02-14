"""
Shared pytest configuration and fixtures.
"""

from pathlib import Path
import pytest


@pytest.fixture
def project_root() -> Path:
    """
    Return the project root directory.
    """
    return Path(__file__).resolve().parents[1]