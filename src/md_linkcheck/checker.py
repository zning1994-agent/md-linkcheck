"""Link checker module with async HTTP and path validation."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

import aiohttp

from md_linkcheck.models import CheckResult, Link, LinkType


class LinkChecker:
    """Checks links for validity using async HTTP requests and path validation."""

    def __init__(
        self,
        timeout: int = 10,
        concurrency: int = 10,
        verbose: bool = False,
    ) -> None:
        """Initialize the link checker.

        Args:
            timeout: Timeout in seconds for HTTP requests.
            concurrency: Maximum number of concurrent checks.
            verbose: Enable verbose output during checking.
        """
        self.timeout = timeout
        self.concurrency = concurrency
        self.verbose = verbose
        self.last_duration: float = 0.0

    async def _check_http_link(
        self,
        session: aiohttp.ClientSession,
        link: Link,
    ) -> CheckResult:
        """Check an HTTP/HTTPS link.

        Args:
            session: aiohttp client session.
            link: The link to check.

        Returns:
            CheckResult with validity status.
        """
        try:
            async with session.head(link.url, allow_redirects=True) as response:
                is_valid = 200 <= response.status < 400
                return CheckResult(
                    link=link,
                    is_valid=is_valid,
                    status_code=response.status,
                )
        except aiohttp.ClientError as e:
            return CheckResult(
                link=link,
                is_valid=False,
                error_message=str(e),
            )
        except asyncio.TimeoutError:
            return CheckResult(
                link=link,
                is_valid=False,
                error_message="Request timeout",
            )

    def _check_relative_path(self, link: Link) -> CheckResult:
        """Check if a relative path exists.

        Args:
            link: The link to check.

        Returns:
            CheckResult with validity status.
        """
        base_dir = link.file_path.parent
        target_path = base_dir / link.url

        is_valid = target_path.exists() and target_path.is_file()
        return CheckResult(
            link=link,
            is_valid=is_valid,
            error_message=None if is_valid else "File not found",
        )

    async def check_link(self, link: Link) -> CheckResult:
        """Check a single link.

        Args:
            link: The link to check.

        Returns:
            CheckResult with validity status.
        """
        if link.link_type == LinkType.HTTP:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                return await self._check_http_link(session, link)
        else:
            return self._check_relative_path(link)

    async def _check_link_with_semaphore(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        link: Link,
        index: int,
        total: int,
    ) -> CheckResult:
        """Check a link with semaphore-based concurrency control.

        Args:
            session: aiohttp client session.
            semaphore: Semaphore for concurrency control.
            link: The link to check.
            index: Current link index (1-based).
            total: Total number of links.

        Returns:
            CheckResult with validity status.
        """
        async with semaphore:
            if self.verbose:
                print(f"Checking {index}/{total}: {link.url}")

            if link.link_type == LinkType.HTTP:
                return await self._check_http_link(session, link)
            else:
                return self._check_relative_path(link)

    async def check_links(self, links: List[Link]) -> List[CheckResult]:
        """Check multiple links concurrently.

        Args:
            links: List of links to check.

        Returns:
            List of CheckResult objects.
        """
        start_time = time.time()
        total = len(links)

        if total == 0:
            self.last_duration = 0.0
            return []

        semaphore = asyncio.Semaphore(self.concurrency)
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [
                self._check_link_with_semaphore(
                    session, semaphore, link, idx + 1, total
                )
                for idx, link in enumerate(links)
            ]
            results = await asyncio.gather(*tasks)

        self.last_duration = time.time() - start_time
        return list(results)
