"""Data models for md-linkcheck."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class LinkType(Enum):
    """Type of link found in markdown."""

    HTTP = "http"
    RELATIVE_PATH = "relative_path"


@dataclass
class Link:
    """Represents a link found in a markdown file."""

    url: str
    link_type: LinkType
    file_path: Path
    line_number: int

    def __str__(self) -> str:
        return f"{self.url} (line {self.line_number} in {self.file_path})"


@dataclass
class CheckResult:
    """Result of checking a single link."""

    link: Link
    is_valid: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None

    def __str__(self) -> str:
        if self.is_valid:
            return f"✓ {self.link.url} ({self.status_code})"
        return f"✗ {self.link.url} - {self.error_message}"


@dataclass
class ScanReport:
    """Complete scan report containing all results."""

    total_links: int
    valid_count: int
    broken_count: int
    results: List[CheckResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_links == 0:
            return 100.0
        return (self.valid_count / self.total_links) * 100
