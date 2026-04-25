"""Link checker module with async HTTP and path validation."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

import aiohttp

from md_linkcheck.models import CheckResult, Link, LinkType


class LinkChecker:
    """Checks links for validity using async HTTP requests and path validation."""

    def __init__(self, timeout: int = 10, verbose: bool = False) -> None:
        """Initialize the link checker.

        Args:
            timeout: Timeout in seconds for HTTP requests.
            verbose: Enable verbose output during checking.
        """
        self.timeout = timeout
        self.verbose = verbose
        self.last_duration: float = 0.0

    async def _on_request_start(
        self,
        session: aiohttp.ClientSession,
        trace_config_ctx: dict,
        params: aiohttp.TraceRequestStartParams,
    ) -> None:
        """Callback when HTTP request starts.

        Args:
            session: aiohttp client session.
            trace_config_ctx: Trace context dictionary.
            params: Request start parameters.
        """
        if self.verbose:
            task_data = trace_config_ctx.get("task_data", {})
            idx = task_data.get("index", 0)
            total = task_data.get("total", 0)
            url = str(params.url)
            print(f"Checking {idx}/{total}: {url}")

    def _create_trace_config(self) -> aiohttp.TraceConfig:
        """Create aiohttp trace config for verbose logging.

        Returns:
            Configured TraceConfig instance.
        """
        trace_config = aiohttp.TraceConfig()

        if self.verbose:
            trace_config.on_request_start.append(self._on_request_start)

        return trace_config

    async def _check_http_link(
        self, session: aiohttp.ClientSession, link: Link
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

    async def _check_link(
        self,
        session: Optional[aiohttp.ClientSession],
        link: Link,
    ) -> CheckResult:
        """Check a single link based on its type.

        Args:
            session: aiohttp client session.
            link: The link to check.

        Returns:
            CheckResult with validity status.
        """
        if link.link_type == LinkType.HTTP:
            return await self._check_http_link(session, link)
        else:
            return self._check_relative_path(link)

    async def _check_links_async(
        self, links: List[Link], concurrency: int
    ) -> List[CheckResult]:
        """Check links asynchronously with limited concurrency.

        Args:
            links: List of links to check.
            concurrency: Maximum concurrent checks.

        Returns:
            List of CheckResult objects.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[CheckResult] = []
        total = len(links)

        async def check_with_semaphore(
            link: Link, index: int
        ) -> CheckResult:
            trace_config_ctx = {"task_data": {"index": index, "total": total}}
            async with semaphore:
                if link.link_type == LinkType.HTTP:
                    return await self._check_http_link(None, link)
                else:
                    return self._check_relative_path(link)

        trace_config = self._create_trace_config()

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            trace_configs=[trace_config],
        ) as session:
            tasks = [
                check_with_semaphore(link, idx + 1)
                for idx, link in enumerate(links)
            ]
            results = await asyncio.gather(*tasks)

        return list(results)

    def check_links(
        self, links: List[Link], concurrency: int = 10
    ) -> List[CheckResult]:
        """Check links synchronously.

        Args:
            links: List of links to check.
            concurrency: Maximum concurrent checks.

        Returns:
            List of CheckResult objects.
        """
        start_time = time.time()
        results = asyncio.run(self._check_links_async(links, concurrency))
        self.last_duration = time.time() - start_time
        return results
