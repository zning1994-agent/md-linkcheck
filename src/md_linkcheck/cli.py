"""CLI module for md-linkcheck."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click

from md_linkcheck.checker import LinkChecker
from md_linkcheck.models import Link, ScanReport
from md_linkcheck.parser import LinkParser
from md_linkcheck.reporter import ReportGenerator
from md_linkcheck.scanner import DirectoryScanner


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
        valid_links=sum(1 for r in results if r.is_valid),
        broken_links=sum(1 for r in results if not r.is_valid),
        results=results,
        duration=checker.last_duration,
        scanned_files=len(md_files),
    )

    stats = {
        "total_links": report.total_links,
        "valid_links": report.valid_links,
        "broken_links": report.broken_links,
        "scanned_files": report.scanned_files,
        "duration": report.duration,
    }

    reporter = ReportGenerator(verbose=verbose)

    if output_format == "json":
        if not output_path:
            click.echo("Error: --output required for JSON format", err=True)
            sys.exit(1)
        reporter.generate_json(results, stats, Path(output_path))
        click.echo(f"JSON report saved to: {output_path}")
    elif output_format == "text":
        if not output_path:
            click.echo("Error: --output required for text format", err=True)
            sys.exit(1)
        reporter.generate_text(results, stats, Path(output_path))
        click.echo(f"Text report saved to: {output_path}")
    else:
        reporter.generate_console(results, stats)

    # Exit with error code if broken links found
    if report.broken_links > 0:
        sys.exit(1)


if __name__ == "__main__":
    cli()
