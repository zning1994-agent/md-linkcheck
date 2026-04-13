"""Link checker module with async HTTP checking and verbose progress support."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import aiohttp

from .models import CheckResult, Link, LinkType


class LinkChecker:
    """Asynchronous link checker with verbose progress display."""

    def __init__(self, concurrency: int = 10, timeout: int = 10, verbose: bool = False):
        """
        Initialize the link checker.

        Args:
            concurrency: Maximum number of concurrent requests.
            timeout: Request timeout in seconds.
            verbose: Enable verbose progress output.
        """
        self.concurrency = concurrency
        self.timeout = timeout
        self.verbose = verbose
        self._checked_count = 0
        self._total_count = 0

    async def check_links(
        self, links: List[Link], concurrency: Optional[int] = None, timeout: Optional[int] = None, verbose: Optional[bool] = None
    ) -> List[CheckResult]:
        """
        Check all links asynchronously with progress display.

        Args:
            links: List of links to check.
            concurrency: Override default concurrency.
            timeout: Override default timeout.
            verbose: Override default verbose setting.

        Returns:
            List of check results.
        """
        if concurrency is not None:
            self.concurrency = concurrency
        if timeout is not None:
            self.timeout = timeout
        if verbose is not None:
            self.verbose = verbose

        self._total_count = len(links)
        self._checked_count = 0

        if self.verbose:
            print(f"Starting link check for {self._total_count} links...", file=sys.stderr)

        semaphore = asyncio.Semaphore(self.concurrency)

        async with aiohttp.ClientSession() as session:
            tasks = [self._check_with_semaphore(semaphore, session, link) for link in links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    CheckResult(
                        link=links[i],
                        is_valid=False,
                        error_message=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _check_with_semaphore(self, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, link: Link) -> CheckResult:
        """Check a link with semaphore control."""
        async with semaphore:
            return await self._check_link(session, link)

    async def _check_link(self, session: aiohttp.ClientSession, link: Link) -> CheckResult:
        """Check a single link and display progress if verbose."""
        self._checked_count += 1

        if self.verbose:
            print(f"Checking {self._checked_count}/{self._total_count}: {link.url}", file=sys.stderr)

        if link.link_type == LinkType.HTTP:
            return await self._check_http(session, link)
        elif link.link_type == LinkType.RELATIVE_PATH:
            return self._check_relative_path(link)

        return CheckResult(
            link=link,
            is_valid=False,
            error_message="Unknown link type",
        )

    async def _check_http(self, session: aiohttp.ClientSession, link: Link) -> CheckResult:
        """Check an HTTP/HTTPS link."""
        try:
            async with session.head(link.url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                is_valid = 200 <= response.status < 400
                return CheckResult(
                    link=link,
                    is_valid=is_valid,
                    status_code=response.status,
                    error_message=None if is_valid else f"HTTP {response.status}",
                )
        except asyncio.TimeoutError:
            return CheckResult(
                link=link,
                is_valid=False,
                error_message="Timeout",
            )
        except aiohttp.ClientError as e:
            return CheckResult(
                link=link,
                is_valid=False,
                error_message=str(e),
            )
        except Exception as e:
            return CheckResult(
                link=link,
                is_valid=False,
                error_message=str(e),
            )

    def _check_relative_path(self, link: Link) -> CheckResult:
        """Check if a relative path file exists."""
        base_dir = link.file_path.parent
        target_path = base_dir / link.url

        is_valid = target_path.exists()
        return CheckResult(
            link=link,
            is_valid=is_valid,
            status_code=200 if is_valid else None,
            error_message=None if is_valid else "File not found",
        )
