"""Tests for checker module."""

import pytest
from pathlib import Path

from md_linkcheck.checker import LinkChecker
from md_linkcheck.models import Link, LinkType


class TestLinkChecker:
    """Test cases for LinkChecker."""

    @pytest.fixture
    def http_link(self, tmp_path):
        """Create an HTTP link for testing."""
        return Link(
            url="https://httpbin.org/status/200",
            link_type=LinkType.HTTP,
            file_path=tmp_path / "test.md",
            line_number=1,
        )

    @pytest.fixture
    def relative_link(self, tmp_path):
        """Create a relative path link for testing."""
        return Link(
            url="existing_file.md",
            link_type=LinkType.RELATIVE_PATH,
            file_path=tmp_path / "test.md",
            line_number=1,
        )

    @pytest.fixture
    def missing_relative_link(self, tmp_path):
        """Create a relative path link pointing to non-existent file."""
        return Link(
            url="missing_file.md",
            link_type=LinkType.RELATIVE_PATH,
            file_path=tmp_path / "test.md",
            line_number=1,
        )

    @pytest.mark.asyncio
    async def test_check_valid_http_link(self, http_link):
        """Test checking a valid HTTP link."""
        checker = LinkChecker(timeout=10)
        results = await checker.check_links([http_link])

        assert len(results) == 1
        assert results[0].is_valid is True
        assert results[0].status_code == 200

    @pytest.mark.asyncio
    async def test_check_existing_relative_path(self, relative_link, tmp_path):
        """Test checking an existing relative path."""
        (tmp_path / "existing_file.md").touch()

        checker = LinkChecker()
        results = await checker.check_links([relative_link])

        assert len(results) == 1
        assert results[0].is_valid is True

    @pytest.mark.asyncio
    async def test_check_missing_relative_path(self, missing_relative_link):
        """Test checking a missing relative path."""
        checker = LinkChecker()
        results = await checker.check_links([missing_relative_link])

        assert len(results) == 1
        assert results[0].is_valid is False
        assert "not found" in results[0].error_message.lower()

    @pytest.mark.asyncio
    async def test_check_multiple_links(self, http_link, relative_link, tmp_path):
        """Test checking multiple links at once."""
        (tmp_path / "existing_file.md").touch()

        checker = LinkChecker(timeout=10)
        results = await checker.check_links([http_link, relative_link])

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_verbose_flag(self, http_link, capsys):
        """Test that verbose flag enables progress output."""
        checker = LinkChecker(verbose=True)
        await checker.check_links([http_link])

        captured = capsys.readouterr()
        assert "Checking" in captured.err
        assert http_link.url in captured.err

    @pytest.mark.asyncio
    async def test_no_verbose_by_default(self, http_link, capsys):
        """Test that progress is not shown without verbose flag."""
        checker = LinkChecker(verbose=False)
        await checker.check_links([http_link])

        captured = capsys.readouterr()
        assert "Checking" not in captured.err

    @pytest.mark.asyncio
    async def test_timeout_handling(self, tmp_path):
        """Test handling of request timeout."""
        link = Link(
            url="https://httpbin.org/delay/10",
            link_type=LinkType.HTTP,
            file_path=tmp_path / "test.md",
            line_number=1,
        )

        checker = LinkChecker(timeout=1, verbose=False)
        results = await checker.check_links([link])

        assert len(results) == 1
        assert results[0].is_valid is False

    def test_checker_initialization(self):
        """Test checker initialization with custom parameters."""
        checker = LinkChecker(concurrency=5, timeout=15, verbose=True)

        assert checker.concurrency == 5
        assert checker.timeout == 15
        assert checker.verbose is True
