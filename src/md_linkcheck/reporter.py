"""Reporter module for generating link check reports."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


class ReportGenerator:
    """Generates reports from link check results."""

    def __init__(self, verbose: bool = False, console: Optional[Console] = None) -> None:
        """Initialize the report generator.

        Args:
            verbose: Enable verbose output.
            console: Rich console instance for output.
        """
        self.verbose = verbose
        self.console = console or Console()

    def generate_console(
        self,
        results: List[Any],
        stats: Dict[str, Any],
    ) -> None:
        """Generate console output with rich Table.

        Args:
            results: List of CheckResult objects.
            stats: Dictionary with scan statistics (total, valid, broken, duration).
        """
        self.console.print()
        self.console.print("[bold]Link Check Report[/bold]")
        self.console.print(f"Total links: {stats.get('total_links', 0)}")
        self.console.print(
            f"Valid: [green]{stats.get('valid_links', 0)}[/green] | "
            f"Broken: [red]{stats.get('broken_links', 0)}[/red]"
        )
        self.console.print(f"Duration: {stats.get('duration', 0):.2f}s")
        self.console.print()

        broken_results = [r for r in results if not r.is_valid]

        if broken_results:
            table = Table(title="Broken Links")
            table.add_column("File", style="cyan")
            table.add_column("Line", justify="right")
            table.add_column("URL")
            table.add_column("Status", style="red")

            for result in broken_results:
                url = result.link.url
                if len(url) > 60:
                    url = url[:60] + "..."
                status = f"Status {result.status_code}" if result.status_code else result.error_message or "Unknown"
                table.add_row(
                    str(result.link.file_path),
                    str(result.link.line_number),
                    url,
                    status,
                )

            self.console.print(table)
        else:
            self.console.print("[green]All links are valid![/green]")

    def generate_json(
        self,
        results: List[Any],
        stats: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """Generate JSON file report.

        Args:
            results: List of CheckResult objects.
            stats: Dictionary with scan statistics.
            output_path: Path to output JSON file.
        """
        data = {
            "summary": {
                "total_links": stats.get("total_links", 0),
                "valid_links": stats.get("valid_links", 0),
                "broken_links": stats.get("broken_links", 0),
                "scanned_files": stats.get("scanned_files", 0),
                "duration": stats.get("duration", 0.0),
            },
            "results": [
                {
                    "file": str(result.link.file_path),
                    "line": result.link.line_number,
                    "url": result.link.url,
                    "type": result.link.link_type.value,
                    "is_valid": result.is_valid,
                    "status_code": result.status_code,
                    "error_message": result.error_message,
                }
                for result in results
            ],
            "broken_links": [
                {
                    "file": str(result.link.file_path),
                    "line": result.link.line_number,
                    "url": result.link.url,
                    "type": result.link.link_type.value,
                    "error": result.error_message or f"Status {result.status_code}",
                }
                for result in results
                if not result.is_valid
            ],
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def generate_text(
        self,
        results: List[Any],
        stats: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """Generate concise text file report.

        Args:
            results: List of CheckResult objects.
            stats: Dictionary with scan statistics.
            output_path: Path to output text file.
        """
        lines = [
            "Link Check Report",
            "=" * 50,
            f"Total links: {stats.get('total_links', 0)}",
            f"Valid: {stats.get('valid_links', 0)}",
            f"Broken: {stats.get('broken_links', 0)}",
            f"Duration: {stats.get('duration', 0):.2f}s",
            "",
            "Broken Links:",
            "-" * 50,
        ]

        broken_results = [r for r in results if not r.is_valid]

        if broken_results:
            for result in broken_results:
                lines.append(f"  {result.link.file_path}:{result.link.line_number}")
                lines.append(f"    URL: {result.link.url}")
                error = result.error_message or f"Status {result.status_code}"
                lines.append(f"    Error: {error}")
        else:
            lines.append("  No broken links found.")

        output_path.write_text("\n".join(lines), encoding="utf-8")
