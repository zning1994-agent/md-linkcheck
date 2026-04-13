"""Integration tests for md-linkcheck CLI."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from md_linkcheck.cli import cli


class TestCLI:
    """Integration tests for CLI."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with markdown files."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (tmp_path / "README.md").write_text("[GitHub](https://github.com)")
        (docs_dir / "guide.md").write_text("[Python](https://python.org)")

        return tmp_path

    def test_cli_help(self, runner):
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Check links in markdown files" in result.output

    def test_cli_version(self, runner):
        """Test CLI version output."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_scan_directory(self, runner, temp_project):
        """Test scanning a directory."""
        result = runner.invoke(cli, [str(temp_project)])
        assert result.exit_code in [0, 1]

    def test_scan_with_verbose(self, runner, temp_project):
        """Test verbose output flag."""
        result = runner.invoke(cli, ["-v", str(temp_project)])
        assert result.exit_code in [0, 1]
        assert "Scanning" in result.output or "Found" in result.output

    def test_json_output(self, runner, temp_project, tmp_path):
        """Test JSON output format."""
        output_file = tmp_path / "report.json"
        result = runner.invoke(cli, ["-f", "json", "-o", str(output_file), str(temp_project)])

        assert result.exit_code in [0, 1]
        if output_file.exists():
            data = json.loads(output_file.read_text())
            assert "total_links" in data
            assert "results" in data

    def test_concise_output(self, runner, temp_project):
        """Test concise output format."""
        result = runner.invoke(cli, ["-f", "concise", str(temp_project)])
        assert result.exit_code in [0, 1]
        assert "Total:" in result.output

    def test_no_markdown_files(self, runner, tmp_path):
        """Test handling of directory with no markdown files."""
        result = runner.invoke(cli, [str(tmp_path)])
        assert result.exit_code == 0
        assert "No markdown files found" in result.output

    def test_custom_concurrency(self, runner, temp_project):
        """Test custom concurrency setting."""
        result = runner.invoke(cli, ["-c", "5", str(temp_project)])
        assert result.exit_code in [0, 1]

    def test_custom_timeout(self, runner, temp_project):
        """Test custom timeout setting."""
        result = runner.invoke(cli, ["-t", "5", str(temp_project)])
        assert result.exit_code in [0, 1]
