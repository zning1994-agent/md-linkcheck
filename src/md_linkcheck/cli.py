"""CLI module for md-linkcheck."""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .checker import LinkChecker
from .models import Link, LinkType, ScanReport


console = Console()


class MarkdownParser:
    """Simple markdown link parser."""

    def extract_links(self, file_path: Path) -> List[Link]:
        """Extract all links from a markdown file."""
        links = []
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return links

        lines = content.split("\n")
        for line_num, line in enumerate(lines, start=1):
            links.extend(self._extract_links_from_line(line, file_path, line_num))

        return links

    def _extract_links_from_line(self, line: str, file_path: Path, line_number: int) -> List[Link]:
        """Extract links from a single line of markdown."""
        links = []

        import re

        md_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for match in md_link_pattern.finditer(line):
            url = match.group(2)

            if url.startswith(("http://", "https://")):
                links.append(
                    Link(
                        url=url,
                        link_type=LinkType.HTTP,
                        file_path=file_path,
                        line_number=line_number,
                    )
                )
            elif not url.startswith(("mailto:", "tel:", "#", "/")):
                links.append(
                    Link(
                        url=url,
                        link_type=LinkType.RELATIVE_PATH,
                        file_path=file_path,
                        line_number=line_number,
                    )
                )

        return links


class DirectoryScanner:
    """Scans directories for markdown files."""

    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        """Initialize scanner with optional exclude patterns."""
        self.exclude_patterns = exclude_patterns or []

    def scan(self, directory: Path) -> List[Path]:
        """Recursively find all markdown files in directory."""
        md_files = []
        exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

        for item in directory.rglob("*.md"):
            if self._should_include(item):
                md_files.append(item)

        return sorted(md_files)

    def _should_include(self, path: Path) -> bool:
        """Check if path should be included based on exclude patterns."""
        for part in path.parts:
            if part in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}:
                return False

        for pattern in self.exclude_patterns:
            if pattern in path.parts:
                return False

        return True


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--output", "-o", "output_path", type=click.Path(), help="Output file path for JSON report")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "concise"]), default="table", help="Output format")
@click.option("--exclude", "-e", multiple=True, help="Patterns to exclude from scanning")
@click.option("--concurrency", "-c", type=int, default=10, help="Maximum concurrent requests (default: 10)")
@click.option("--timeout", "-t", type=int, default=10, help="Request timeout in seconds (default: 10)")
@click.option("--verbose", "-v", is_flag=True, help="Show progress during link checking")
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context, path: str, output_path: Optional[str], output_format: str, exclude: tuple, concurrency: int, timeout: int, verbose: bool) -> None:
    """
    Check links in markdown files.

    PATH: Directory or file to scan (default: current directory)
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    target_path = Path(path)

    if verbose:
        console.print(f"[bold blue]Scanning:[/bold blue] {target_path}")

    parser = MarkdownParser()
    scanner = DirectoryScanner(list(exclude))

    if target_path.is_file():
        md_files = [target_path]
    else:
        md_files = scanner.scan(target_path)

    if not md_files:
        console.print("[yellow]No markdown files found.[/yellow]")
        ctx.exit(0)

    if verbose:
        console.print(f"[bold blue]Found {len(md_files)} markdown file(s)[/bold blue]")

    all_links: List[Link] = []
    for md_file in md_files:
        links = parser.extract_links(md_file)
        all_links.extend(links)

    if not all_links:
        console.print("[yellow]No links found in markdown files.[/yellow]")
        ctx.exit(0)

    if verbose:
        console.print(f"[bold blue]Checking {len(all_links)} link(s)...[/bold blue]")

    start_time = time.time()
    checker = LinkChecker(concurrency=concurrency, timeout=timeout, verbose=verbose)
    results = asyncio.run(checker.check_links(all_links))
    duration = time.time() - start_time

    valid_count = sum(1 for r in results if r.is_valid)
    broken_count = len(results) - valid_count

    report = ScanReport(
        total_links=len(results),
        valid_count=valid_count,
        broken_count=broken_count,
        results=results,
        duration=duration,
    )

    if output_format == "json" and output_path:
        _save_json_report(report, Path(output_path))
    elif output_format == "concise":
        _print_concise_report(report)
    else:
        _print_table_report(report)

    if broken_count > 0:
        ctx.exit(1)


def _print_table_report(report: ScanReport) -> None:
    """Print results as a rich table."""
    table = Table(title=f"Link Check Results ({report.success_rate:.1f}% valid)")

    table.add_column("Status", style="green" if report.broken_count == 0 else "red")
    table.add_column("URL", style="cyan")
    table.add_column("File", style="blue")
    table.add_column("Line", justify="right")
    table.add_column("Message")

    for result in report.results:
        status = "✓" if result.is_valid else "✗"
        file_name = result.link.file_path.name
        message = f"[{result.status_code}]" if result.status_code else result.error_message or ""

        table.add_row(status, result.link.url, file_name, str(result.link.line_number), message)

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {report.valid_count}/{report.total_links} valid | Duration: {report.duration:.2f}s")


def _print_concise_report(report: ScanReport) -> None:
    """Print concise summary report."""
    console.print(f"Total: {report.total_links}, Valid: {report.valid_count}, Broken: {report.broken_count}, Time: {report.duration:.2f}s")

    for result in report.results:
        if not result.is_valid:
            status = f"[{result.status_code}]" if result.status_code else result.error_message or "ERROR"
            console.print(f"  ✗ {result.link.url} ({result.link.file_path}:{result.link.line_number}) - {status}")


def _save_json_report(report: ScanReport, output_path: Path) -> None:
    """Save report as JSON file."""
    data = {
        "total_links": report.total_links,
        "valid_count": report.valid_count,
        "broken_count": report.broken_count,
        "success_rate": report.success_rate,
        "duration": report.duration,
        "results": [
            {
                "url": r.link.url,
                "type": r.link.link_type.value,
                "file": str(r.link.file_path),
                "line": r.link.line_number,
                "is_valid": r.is_valid,
                "status_code": r.status_code,
                "error": r.error_message,
            }
            for r in report.results
        ],
    }

    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]Report saved to:[/green] {output_path}")


if __name__ == "__main__":
    cli()
