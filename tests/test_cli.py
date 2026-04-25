"""Tests for CLI module."""

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from md_linkcheck.cli import cli


class TestCLI:
    """Test suite for CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Create a CliRunner instance."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_help_output(self, runner):
        """Test that --help shows all expected options."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "--help" in result.output
        assert "--output" in result.output
        assert "-o" in result.output
        assert "--format" in result.output
        assert "-f" in result.output
        assert "--exclude" in result.output
        assert "-e" in result.output
        assert "--concurrency" in result.output
        assert "-c" in result.output
        assert "--timeout" in result.output
        assert "-t" in result.output
        assert "--verbose" in result.output
        assert "-v" in result.output

    def test_scan_directory(self, runner, temp_dir):
        """Test scanning a directory for markdown files."""
        # Create test markdown file
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](https://example.com)")

        result = runner.invoke(cli, [str(temp_dir)])

        assert result.exit_code in [0, 1]  # 0 = success, 1 = broken links
        assert "Markdown" in result.output or "Link Check" in result.output

    def test_verbose_flag(self, runner, temp_dir):
        """Test that -v flag enables verbose output."""
        # Create test markdown file
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](https://example.com)")

        result = runner.invoke(cli, ["-v", str(temp_dir)])

        # Verbose mode should output scanning progress
        assert "Scanning" in result.output or "Found" in result.output

    def test_output_option(self, runner, temp_dir):
        """Test -o output file path option."""
        # Create test markdown file
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](./existing_file.md)")

        # Create the referenced file to make it valid
        (temp_dir / "existing_file.md").write_text("# Referenced file")

        output_file = temp_dir / "report.json"
        result = runner.invoke(cli, ["-o", str(output_file), "-f", "json", str(temp_dir)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_exclude_option(self, runner, temp_dir):
        """Test --exclude pattern option."""
        # Create markdown files in different directories
        (temp_dir / "included.md").write_text("# Included\n\n[link1](./file1.md)")
        (temp_dir / "included_file.md").write_text("# Included file")
        excluded_dir = temp_dir / "node_modules"
        excluded_dir.mkdir()
        (excluded_dir / "excluded.md").write_text("# Excluded\n\n[link](./file.md")

        # Scan without exclusion
        result_all = runner.invoke(cli, [str(temp_dir)])

        # Scan with exclusion
        result_filtered = runner.invoke(
            cli, ["--exclude", "node_modules", str(temp_dir)]
        )

        # Both should complete (may have different exit codes due to link validation)
        assert result_all.exit_code in [0, 1]
        assert result_filtered.exit_code in [0, 1]

    def test_timeout_option(self, runner, temp_dir):
        """Test --timeout value option."""
        # Create test markdown file
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](https://httpbin.org/delay/1)")

        # Run with custom timeout
        result = runner.invoke(cli, ["--timeout", "30", str(temp_dir)])

        # Should complete (either success or timeout)
        assert result.exit_code in [0, 1]

    def test_format_option_console(self, runner, temp_dir):
        """Test --format console output."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](./file.md)")

        result = runner.invoke(cli, ["--format", "console", str(temp_dir)])

        assert result.exit_code in [0, 1]

    def test_format_option_json(self, runner, temp_dir):
        """Test --format json output."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](./file.md)")

        output_file = temp_dir / "output.json"
        result = runner.invoke(
            cli, ["--format", "json", "-o", str(output_file), str(temp_dir)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_format_option_text(self, runner, temp_dir):
        """Test --format text output."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](./file.md)")

        output_file = temp_dir / "output.txt"
        result = runner.invoke(
            cli, ["--format", "text", "-o", str(output_file), str(temp_dir)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_concurrency_option(self, runner, temp_dir):
        """Test --concurrency option."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\n[link](https://example.com)")

        result = runner.invoke(cli, ["--concurrency", "5", str(temp_dir)])

        assert result.exit_code in [0, 1]

    def test_multiple_excludes(self, runner, temp_dir):
        """Test multiple --exclude options."""
        (temp_dir / "included.md").write_text("# Included")

        excluded1 = temp_dir / "exclude1"
        excluded1.mkdir()
        (excluded1 / "file.md").write_text("# Excluded 1")

        excluded2 = temp_dir / "exclude2"
        excluded2.mkdir()
        (excluded2 / "file.md").write_text("# Excluded 2")

        result = runner.invoke(
            cli,
            [
                "--exclude", "exclude1",
                "--exclude", "exclude2",
                str(temp_dir)
            ],
        )

        assert result.exit_code in [0, 1]

    def test_no_markdown_files(self, runner, temp_dir):
        """Test behavior when no markdown files found."""
        # Create a non-markdown file
        (temp_dir / "readme.txt").write_text("Plain text file")

        result = runner.invoke(cli, [str(temp_dir)])

        assert result.exit_code == 0
        assert "No Markdown files" in result.output or "No markdown" in result.output.lower()

    def test_nonexistent_path(self, runner):
        """Test behavior with nonexistent path."""
        result = runner.invoke(cli, ["/nonexistent/path/to/directory"])

        assert result.exit_code != 0
