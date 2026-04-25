"""Pytest configuration and shared fixtures."""

import pytest

pytest_plugins = ["pytest_asyncio", "aioresponses"]


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"
