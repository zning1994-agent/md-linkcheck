"""Link parser module using markdown-it-py."""

from pathlib import Path
from typing import List

from markdown_it import MarkdownIt

from md_linkcheck.models import Link, LinkType


class LinkParser:
    """Parses Markdown files to extract links."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.md = MarkdownIt()

    def _is_http_link(self, url: str) -> bool:
        """Check if URL is an HTTP/HTTPS link.

        Args:
            url: URL to check.

        Returns:
            True if URL is HTTP/HTTPS.
        """
        return url.startswith("http://") or url.startswith("https://")

    def extract_links(self, content: str, file_path: Path) -> List[Link]:
        """Extract all links from Markdown content.

        Args:
            content: Markdown file content.
            file_path: Path to the Markdown file.

        Returns:
            List of Link objects.
        """
        links: List[Link] = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            tokens = self.md.parse(line)

            for token in tokens:
                if token.type == "link":
                    url = token.get("href", "")
                    if url:
                        link_type = (
                            LinkType.HTTP
                            if self._is_http_link(url)
                            else LinkType.RELATIVE_PATH
                        )
                        links.append(
                            Link(
                                url=url,
                                link_type=link_type,
                                file_path=file_path,
                                line_number=line_num,
                                line_content=line.strip(),
                            )
                        )
                elif token.type == "image":
                    url = token.get("src", "")
                    if url:
                        link_type = (
                            LinkType.HTTP
                            if self._is_http_link(url)
                            else LinkType.RELATIVE_PATH
                        )
                        links.append(
                            Link(
                                url=url,
                                link_type=link_type,
                                file_path=file_path,
                                line_number=line_num,
                                line_content=line.strip(),
                            )
                        )

        return links
