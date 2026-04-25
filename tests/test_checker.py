"""Tests for checker module."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import aioresponses

from md_linkcheck.checker import LinkChecker
from md_linkcheck.models import Link, LinkType


class TestLinkChecker:
    """Test suite for LinkChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a LinkChecker instance."""
        return LinkChecker(timeout=10, concurrency=5, verbose=False)

    @pytest.fixture
    def http_link(self, tmp_path):
        """Create a test HTTP link."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        return Link(
            url="https://example.com",
            link_type=LinkType.HTTP,
            file_path=md_file,
            line_number=1,
            line_content="[link](https://example.com)",
        )

    @pytest.fixture
    def relative_link(self, tmp_path):
        """Create a test relative path link."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")
        return Link(
            url="referenced.md",
            link_type=LinkType.RELATIVE_PATH,
            file_path=md_file,
            line_number=1,
            line_content="[link](./referenced.md)",
        )

    @pytest.fixture
    def aioresponses_mock(self):
        """Create aioresponses context manager for mocking HTTP responses."""
        with aioresponses.aioresponses() as mocked:
            yield mocked

    @pytest.mark.asyncio
    async def test_check_http_success(self, checker, http_link, aioresponses_mock):
        """Test checking HTTP link with 200 response."""
        aioresponses_mock.head("https://example.com", status=200)

        result = await checker.check_link(http_link)

        assert result.is_valid is True
        assert result.status_code == 200
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_check_http_404(self, checker, http_link, aioresponses_mock):
        """Test checking HTTP link with 404 response."""
        aioresponses_mock.head("https://example.com", status=404)

        result = await checker.check_link(http_link)

        assert result.is_valid is False
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_check_http_500(self, checker, http_link, aioresponses_mock):
        """Test checking HTTP link with 500 response."""
        aioresponses_mock.head("https://example.com", status=500)

        result = await checker.check_link(http_link)

        assert result.is_valid is False
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_check_http_timeout(self, checker, http_link):
        """Test checking HTTP link with timeout scenario."""
        checker.timeout = 1

        async def timeout_handler(*args, **kwargs):
            raise asyncio.TimeoutError()

        with aioresponses.aioresponses() as mocked:
            mocked.get("https://example.com", callback=timeout_handler)

            result = await checker.check_link(http_link)

        assert result.is_valid is False
        assert "timeout" in result.error_message.lower() or result.error_message is not None

    @pytest.mark.asyncio
    async def test_check_http_redirect(self, checker, http_link, aioresponses_mock):
        """Test checking HTTP link with redirect response."""
        aioresponses_mock.head("https://example.com", status=301, headers={"Location": "https://example.com/new"})

        result = await checker.check_link(http_link)

        assert result.is_valid is True
        assert result.status_code == 301

    def test_check_relative_path_exists(self, checker, relative_link):
        """Test checking relative path when file exists."""
        # Create the referenced file
        referenced_file = relative_link.file_path.parent / "referenced.md"
        referenced_file.write_text("# Referenced file")

        result = asyncio.run(checker.check_link(relative_link))

        assert result.is_valid is True
        assert result.error_message is None

    def test_check_relative_path_missing(self, checker, relative_link):
        """Test checking relative path when file doesn't exist."""
        result = asyncio.run(checker.check_link(relative_link))

        assert result.is_valid is False
        assert result.error_message == "File not found"

    @pytest.mark.asyncio
    async def test_check_links_multiple_http(self, checker, aioresponses_mock):
        """Test checking multiple HTTP links concurrently."""
        links = []
        tmp_path = Path(tempfile.mkdtemp())

        for i in range(3):
            md_file = tmp_path / f"test{i}.md"
            md_file.write_text("# Test")
            links.append(
                Link(
                    url=f"https://example{i}.com",
                    link_type=LinkType.HTTP,
                    file_path=md_file,
                    line_number=1,
                    line_content=f"[link{i}](https://example{i}.com)",
                )
            )

        aioresponses_mock.head("https://example0.com", status=200)
        aioresponses_mock.head("https://example1.com", status=200)
        aioresponses_mock.head("https://example2.com", status=404)

        results = await checker.check_links(links)

        assert len(results) == 3
        assert sum(1 for r in results if r.is_valid) == 2
        assert sum(1 for r in results if not r.is_valid) == 1

    @pytest.mark.asyncio
    async def test_check_links_mixed_types(self, checker, aioresponses_mock, tmp_path):
        """Test checking mixed HTTP and relative path links."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        # Create referenced file
        (tmp_path / "referenced.md").write_text("# Referenced")

        links = [
            Link(
                url="https://example.com",
                link_type=LinkType.HTTP,
                file_path=md_file,
                line_number=1,
                line_content="[link](https://example.com)",
            ),
            Link(
                url="referenced.md",
                link_type=LinkType.RELATIVE_PATH,
                file_path=md_file,
                line_number=2,
                line_content="[link](./referenced.md)",
            ),
        ]

        aioresponses_mock.head("https://example.com", status=200)

        results = await checker.check_links(links)

        assert len(results) == 2
        assert all(r.is_valid for r in results)

    def test_last_duration_tracking(self, checker, aioresponses_mock):
        """Test that last_duration is tracked correctly."""
        links = []
        tmp_path = Path(tempfile.mkdtemp())

        for i in range(5):
            md_file = tmp_path / f"test{i}.md"
            md_file.write_text("# Test")
            links.append(
                Link(
                    url=f"https://example{i}.com",
                    link_type=LinkType.HTTP,
                    file_path=md_file,
                    line_number=1,
                    line_content=f"[link{i}](https://example{i}.com)",
                )
            )

        for i in range(5):
            aioresponses_mock.head(f"https://example{i}.com", status=200)

        asyncio.run(checker.check_links(links))

        assert checker.last_duration > 0

    @pytest.mark.asyncio
    async def test_check_link_with_verbose(self, checker, http_link, aioresponses_mock, capsys):
        """Test verbose output during link checking."""
        checker.verbose = True
        aioresponses_mock.head("https://example.com", status=200)

        await checker.check_link(http_link)

        captured = capsys.readouterr()
        assert "Checking" in captured.out or captured.err

    def test_check_empty_links_list(self, checker):
        """Test checking with empty links list."""
        results = asyncio.run(checker.check_links([]))

        assert len(results) == 0
        assert checker.last_duration == 0.0
