"""md-linkcheck - Markdown Link Checker CLI Tool."""

__version__ = "0.1.0"
__author__ = "Developer"
__license__ = "MIT"

from .models import Link, LinkType, CheckResult, ScanReport

__all__ = [
    "__version__",
    "Link",
    "LinkType",
    "CheckResult",
    "ScanReport",
]
