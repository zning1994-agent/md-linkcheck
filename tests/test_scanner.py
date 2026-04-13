"""Tests for scanner module."""

import pytest
from pathlib import Path

from md_linkcheck.cli import DirectoryScanner


class TestDirectoryScanner:
    """Test cases for DirectoryScanner."""

    def test_scan_finds_markdown_files(self, tmp_path):
        """Test that scanner finds all markdown files."""
        (tmp_path / "file1.md").touch()
        (tmp_path / "file2.md").touch()
        (tmp_path / "file3.txt").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_scan_recursive(self, tmp_path):
        """Test recursive scanning of subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.md").touch()
        (subdir / "nested.md").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 2
        assert any(f.name == "root.md" for f in files)
        assert any(f.name == "nested.md" for f in files)

    def test_exclude_node_modules(self, tmp_path):
        """Test that node_modules is excluded."""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.md").touch()
        (tmp_path / "project.md").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 1
        assert files[0].name == "project.md"

    def test_exclude_git(self, tmp_path):
        """Test that .git directory is excluded."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "readme.md").touch()
        (tmp_path / "project.md").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 1

    def test_custom_exclude_patterns(self, tmp_path):
        """Test custom exclude patterns."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (tmp_path / "root.md").touch()
        (docs_dir / "excluded.md").touch()

        scanner = DirectoryScanner(exclude_patterns=["docs"])
        files = scanner.scan(tmp_path)

        assert len(files) == 1
        assert files[0].name == "root.md"

    def test_no_markdown_files(self, tmp_path):
        """Test handling of directory with no markdown files."""
        (tmp_path / "file.txt").touch()
        (tmp_path / "file.py").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 0

    def test_sorted_results(self, tmp_path):
        """Test that results are sorted."""
        (tmp_path / "z_file.md").touch()
        (tmp_path / "a_file.md").touch()
        (tmp_path / "m_file.md").touch()

        scanner = DirectoryScanner()
        files = scanner.scan(tmp_path)

        names = [f.name for f in files]
        assert names == sorted(names)
