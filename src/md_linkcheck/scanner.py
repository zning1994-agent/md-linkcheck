"""CLI module for md-linkcheck."""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

from md_linkcheck.checker import LinkChecker
from md_linkcheck.models import CheckResult, Link, LinkType, ScanReport
from md_linkcheck.parser import LinkParser


class DirectoryScanner:
    """Scans directories for Markdown files."""

    DEFAULT_EXCLUDES = [
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    ]

    def __init__(self) -> None:
        """Initialize the scanner."""
        pass

    def scan(self, dir_path: Path, exclude: Optional[List[str]] = None) -> List[Path]:
        """Recursively find .md files excluding specified directories.

        Args:
            dir_path: Directory path to scan.
            exclude: List of directory names to exclude.

        Returns:
            List of Path objects for found Markdown files.
        """
        exclude_list = list(exclude) if exclude else []
        exclude_list.extend(self.DEFAULT_EXCLUDES)

        md_files: List[Path] = []

        if dir_path.is_file():
            if dir_path.suffix == ".md":
                md_files.append(dir_path)
            return md_files

        for md_file in dir_path.rglob("*.md"):
            should_exclude = False
            for pattern in exclude_list:
                if pattern in md_file.parts:
                    should_exclude = True
                    break
            if not should_exclude:
                md_files.append(md_file)

        return sorted(md_files)


class ReportGenerator:
    """Generates reports from scan results."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the report generator.

        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()

    def generate_console_report(self, report: ScanReport) -> None:
        """Generate report for console output using rich table.

        Args:
            report: The scan report data.
        """
        self.console.print()
        self.console.print("[bold]Link Check Report[/bold]")
        self.console.print(f"Total links: {report.total_links}")
        self.console.print(
            f"Valid: [green]{report.valid_count}[/green] | "
            f"Broken: [red]{report.broken_count}[/red]"
        )
        self.console.print(f"Duration: {report.duration:.2f}s")
        self.console.print()

        broken = [r for r in report.results if not r.is_valid]
        if broken:
            table = Table(title="Broken Links")
            table.add_column("File", style="cyan")
            table.add_column("Line", justify="right")
            table.add_column("URL")
            table.add_column("Error", style="red")

            for result in broken:
                url = result.link.url
                if len(url) > 60:
                    url = url[:60] + "..."
                table.add_row(
                    str(result.link.file_path),
                    str(result.link.line_number),
                    url,
                    result.error_message or f"Status {result.status_code}",
                )

            self.console.print(table)
        else:
            self.console.print("[green]All links are valid![/green]")

    def generate_json_report(self, report: ScanReport, output_path: Path) -> None:
        """Generate JSON file report.

        Args:
            report: The scan report data.
            output_path: Path to output JSON file.
        """
        data = {
            "total_links": report.total_links,
            "valid_count": report.valid_count,
            "broken_count": report.broken_count,
            "duration": report.duration,
            "broken_links": [
                {
                    "file": str(result.link.file_path),
                    "line": result.link.line_number,
                    "url": result.link.url,
                    "type": result.link.link_type.value,
                    "error": result.error_message or f"Status {result.status_code}",
                }
                for result in report.results
                if not result.is_valid
            ],
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        click.echo(f"JSON report saved to: {output_path}")

    def generate_text_report(self, report: ScanReport, output_path: Path) -> None:
        """Generate plain text file report.

        Args:
            report: The scan report data.
            output_path: Path to output text file.
        """
        lines = [
            "Link Check Report",
            "=" * 50,
            f"Total links: {report.total_links}",
            f"Valid: {report.valid_count}",
            f"Broken: {report.broken_count}",
            f"Duration: {report.duration:.2f}s",
            "",
            "Broken Links:",
            "-" * 50,
        ]

        for result in report.results:
            if not result.is_valid:
                lines.append(f"  {result.link.file_path}:{result.link.line_number}")
                lines.append(f"    URL: {result.link.url}")
                lines.append(
                    f"    Error: {result.error_message or f'Status {result.status_code}'}"
                )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        click.echo(f"Text report saved to: {output_path}")

    def generate_report(
        self,
        report: ScanReport,
        format: str,
        output_path: Optional[Path] = None,
    ) -> None:
        """Generate a report in the specified format.

        Args:
            report: The scan report data.
            format: Output format (console, json, text).
            output_path: Optional file path for file outputs.
        """
        if format == "json":
            if not output_path:
                click.echo("Error: --output required for JSON format", err=True)
                sys.exit(1)
            self.generate_json_report(report, output_path)
        elif format == "text":
            if not output_path:
                click.echo("Error: --output required for text format", err=True)
                sys.exit(1)
            self.generate_text_report(report, output_path)
        else:
            self.generate_console_report(report)


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(),
    default=None,
    help="Output file path for the report.",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["console", "json", "text"], case_sensitive=False),
    default="console",
    help="Output format for the report.",
)
@click.option(
    "--exclude",
    "-e",
    "exclude_patterns",
    multiple=True,
    default=[],
    help="Directory names to exclude from scanning.",
)
@click.option(
    "--concurrency",
    "-c",
    type=int,
    default=10,
    help="Maximum number of concurrent link checks.",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=10,
    help="Timeout in seconds for HTTP requests.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show progress during link checking.",
)
def cli(
    path: str,
    output_path: Optional[str],
    output_format: str,
    exclude_patterns: tuple,
    concurrency: int,
    timeout: int,
    verbose: bool,
) -> None:
    """Scan Markdown files for broken links.

    PATH is the directory or file to scan. Defaults to current directory.
    """
    scan_path = Path(path)
    exclude_list = list(exclude_patterns)

    if verbose:
        click.echo(f"Scanning: {scan_path}")

    # Step 1: Scan for Markdown files
    scanner = DirectoryScanner()
    md_files = scanner.scan(scan_path, exclude_list)

    if not md_files:
        click.echo("No Markdown files found.")
        sys.exit(0)

    if verbose:
        click.echo(f"Found {len(md_files)} Markdown files.")

    # Step 2: Extract links from files
    parser = LinkParser()
    all_links: List[Link] = []

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        links = parser.extract_links(content, md_file)
        all_links.extend(links)

    if verbose:
        click.echo(f"Found {len(all_links)} links.")

    if not all_links:
        click.echo("No links found.")
        sys.exit(0)

    # Step 3: Check links
    checker = LinkChecker(
        timeout=timeout,
        concurrency=concurrency,
        verbose=verbose,
    )
    results = asyncio.run(checker.check_links(all_links))

    # Step 4: Generate report
    report = ScanReport(
        total_links=len(results),
        valid_count=sum(1 for r in results if r.is_valid),
        broken_count=sum(1 for r in results if not r.is_valid),
        results=results,
        duration=checker.last_duration,
    )

    reporter = ReportGenerator()
    output_file = Path(output_path) if output_path else None
    reporter.generate_report(report, format=output_format, output_path=output_file)

    # Exit with error code if broken links found
    if report.broken_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    cli()
