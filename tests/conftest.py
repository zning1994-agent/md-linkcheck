"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_markdown(fixtures_dir):
    """Return path to sample markdown file."""
    return fixtures_dir / "sample.md"


@pytest.fixture
def broken_markdown(fixtures_dir):
    """Return path to broken markdown file."""
    return fixtures_dir / "broken.md"
