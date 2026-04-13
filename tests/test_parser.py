"""Tests for parser module."""

import pytest
from pathlib import Path

from md_linkcheck.cli import MarkdownParser
from md_linkcheck.models import Link, LinkType


class TestMarkdownParser:
    """Test cases for MarkdownParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_extract_http_links(self, tmp_path):
        """Test extraction of HTTP links."""
        md_content = "[GitHub](https://github.com)\n[Python](https://python.org)"
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        links = self.parser.extract_links(md_file)

        assert len(links) == 2
        assert all(link.link_type == LinkType.HTTP for link in links)
        assert links[0].url == "https://github.com"
        assert links[1].url == "https://python.org"

    def test_extract_relative_links(self, tmp_path):
        """Test extraction of relative path links."""
        md_content = "[Image](./images/logo.png)\n[README](./README.md)"
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        links = self.parser.extract_links(md_file)

        assert len(links) == 2
        assert all(link.link_type == LinkType.RELATIVE_PATH for link in links)

    def test_ignore_anchors_and_mailtos(self, tmp_path):
        """Test that anchors and mailto links are ignored."""
        md_content = "[Top](#top)\n[Email](mailto:test@example.com)\n[Valid](https://example.com)"
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        links = self.parser.extract_links(md_file)

        assert len(links) == 1
        assert links[0].url == "https://example.com"

    def test_line_number_tracking(self, tmp_path):
        """Test that line numbers are correctly tracked."""
        md_content = "Line 1\nLine 2\n[Link](https://example.com)\nLine 4"
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        links = self.parser.extract_links(md_file)

        assert len(links) == 1
        assert links[0].line_number == 3

    def test_file_path_tracking(self, tmp_path):
        """Test that file path is correctly stored."""
        md_file = tmp_path / "test.md"
        md_file.write_text("[Link](https://example.com)")

        links = self.parser.extract_links(md_file)

        assert len(links) == 1
        assert links[0].file_path == md_file

    def test_empty_file(self, tmp_path):
        """Test handling of empty markdown file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        links = self.parser.extract_links(md_file)

        assert len(links) == 0

    def test_no_links_in_file(self, tmp_path):
        """Test handling of file with no links."""
        md_file = tmp_path / "no_links.md"
        md_file.write_text("# Just a heading\n\nSome plain text.")

        links = self.parser.extract_links(md_file)

        assert len(links) == 0

    def test_mixed_link_types(self, tmp_path):
        """Test extraction of mixed link types."""
        md_content = "[HTTP](https://example.com)\n[Relative](./file.md)\n[Another HTTP](https://test.com)"
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        links = self.parser.extract_links(md_file)

        assert len(links) == 3
        assert links[0].link_type == LinkType.HTTP
        assert links[1].link_type == LinkType.RELATIVE_PATH
        assert links[2].link_type == LinkType.HTTP
