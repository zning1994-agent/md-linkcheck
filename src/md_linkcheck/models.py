"""Data models for md-linkcheck."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class LinkType(Enum):
    """Type of link found in Markdown."""

    HTTP = "http"
    RELATIVE_PATH = "relative_path"


@dataclass
class Link:
    """Represents a link found in a Markdown file."""

    url: str
    link_type: LinkType
    file_path: Path
    line_number: int
    line_content: str = ""


@dataclass
class CheckResult:
    """Result of checking a single link."""

    link: Link
    is_valid: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    duration: float = 0.0


@dataclass
class ScanReport:
    """Summary report of a link scan."""

    total_links: int
    valid_links: int
    broken_links: int
    results: List[CheckResult] = field(default_factory=list)
    duration: float = 0.0
    scanned_files: int = 0
