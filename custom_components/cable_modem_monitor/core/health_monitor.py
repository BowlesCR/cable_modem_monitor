"""Modem Health Monitor - Dual-layer network diagnostics."""
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
import aiohttp
import subprocess

_LOGGER = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    timestamp: float
    ping_success: bool
    ping_latency_ms: Optional[float]
    http_success: bool
    http_latency_ms: Optional[float]

    @property
    def is_healthy(self) -> bool:
        """Return True if modem is responding to either ping or HTTP."""
        return self.ping_success or self.http_success

    @property
    def status(self) -> str:
        """Return human-readable status."""
        if self.ping_success and self.http_success:
            return "healthy"
        elif self.ping_success and not self.http_success:
            return "degraded"
        elif not self.ping_success and self.http_success:
            return "icmp_blocked"
        else:
            return "unresponsive"

    @property
    def diagnosis(self) -> str:
        """Return detailed diagnosis."""
        if self.ping_success and self.http_success:
            return "Fully responsive"
        elif self.ping_success and not self.http_success:
            return "Web server issue"
        elif not self.ping_success and self.http_success:
            return "ICMP blocked (firewall)"
        else:
            return "Network down / offline"


class ModemHealthMonitor:
    """
    Monitor modem health using dual-layer diagnostics.

    Performs both ICMP ping (Layer 3) and HTTP HEAD (Layer 7) checks
    to distinguish between network issues, web server issues, and firewall blocks.
    """

    def __init__(self, max_history: int = 100):
        """Initialize health monitor."""
        self.max_history = max_history
        self.history: list[HealthCheckResult] = []
        self.consecutive_failures = 0
        self.total_checks = 0
        self.successful_checks = 0

    async def check_health(self, base_url: str) -> HealthCheckResult:
        """
        Perform dual-layer health check.

        Args:
            base_url: Modem URL (e.g., http://192.168.100.1)

        Returns:
            HealthCheckResult with ping and HTTP status
        """
        # Extract host from URL
        import re
        match = re.search(r'https?://([^:/]+)', base_url)
        host = match.group(1) if match else base_url

        # Run ping and HTTP check in parallel
        ping_result, http_result = await asyncio.gather(
            self._check_ping(host),
            self._check_http(base_url),
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(ping_result, Exception):
            _LOGGER.debug("Ping check exception: %s", ping_result)
            ping_success, ping_latency = False, None
        else:
            ping_success, ping_latency = ping_result

        if isinstance(http_result, Exception):
            _LOGGER.debug("HTTP check exception: %s", http_result)
            http_success, http_latency = False, None
        else:
            http_success, http_latency = http_result

        # Create result
        result = HealthCheckResult(
            timestamp=time.time(),
            ping_success=ping_success,
            ping_latency_ms=ping_latency,
            http_success=http_success,
            http_latency_ms=http_latency,
        )

        # Update statistics
        self._update_stats(result)

        # Store in history
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        _LOGGER.debug(
            "Health check: %s (ping=%s, http=%s)",
            result.status,
            ping_success,
            http_success
        )

        return result

    async def _check_ping(self, host: str) -> tuple[bool, Optional[float]]:
        """
        Perform ICMP ping check.

        Returns:
            tuple: (success: bool, latency_ms: float | None)
        """
        try:
            # Use system ping command (works on Linux and Windows)
            # -c 1 = send 1 packet (Linux)
            # -W 2 = timeout 2 seconds (Linux)
            start_time = time.time()

            # Run ping command
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '2', host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()
            latency_ms = (time.time() - start_time) * 1000

            # Check return code (0 = success)
            success = proc.returncode == 0

            return success, latency_ms if success else None

        except Exception as e:
            _LOGGER.debug("Ping exception for %s: %s", host, e)
            return False, None

    async def _check_http(self, base_url: str) -> tuple[bool, Optional[float]]:
        """
        Perform HTTP HEAD check.

        Returns:
            tuple: (success: bool, latency_ms: float | None)
        """
        try:
            start_time = time.time()

            # Use aiohttp for async HTTP request
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(base_url) as response:
                    latency_ms = (time.time() - start_time) * 1000
                    # Accept any response (2xx, 3xx, 4xx) as "alive"
                    # Even 401 or 404 means the web server is running
                    success = response.status < 500
                    return success, latency_ms if success else None

        except asyncio.TimeoutError:
            _LOGGER.debug("HTTP check timeout for %s", base_url)
            return False, None
        except Exception as e:
            _LOGGER.debug("HTTP check exception for %s: %s", base_url, e)
            return False, None

    def _update_stats(self, result: HealthCheckResult):
        """Update running statistics."""
        self.total_checks += 1

        if result.is_healthy:
            self.consecutive_failures = 0
            self.successful_checks += 1
        else:
            self.consecutive_failures += 1

    @property
    def availability_percent(self) -> float:
        """Calculate availability percentage."""
        if self.total_checks == 0:
            return 100.0
        return (self.successful_checks / self.total_checks) * 100

    @property
    def average_ping_latency(self) -> Optional[float]:
        """Calculate average ping latency from recent history."""
        latencies = [
            h.ping_latency_ms for h in self.history
            if h.ping_success and h.ping_latency_ms is not None
        ]
        if not latencies:
            return None
        return sum(latencies) / len(latencies)

    @property
    def average_http_latency(self) -> Optional[float]:
        """Calculate average HTTP latency from recent history."""
        latencies = [
            h.http_latency_ms for h in self.history
            if h.http_success and h.http_latency_ms is not None
        ]
        if not latencies:
            return None
        return sum(latencies) / len(latencies)

    def get_status_summary(self) -> dict:
        """Get current health status summary."""
        if not self.history:
            return {
                "status": "unknown",
                "availability": 100.0,
                "consecutive_failures": 0,
                "total_checks": 0,
            }

        latest = self.history[-1]
        return {
            "status": latest.status,
            "diagnosis": latest.diagnosis,
            "availability": self.availability_percent,
            "consecutive_failures": self.consecutive_failures,
            "total_checks": self.total_checks,
            "ping_success": latest.ping_success,
            "ping_latency_ms": latest.ping_latency_ms,
            "http_success": latest.http_success,
            "http_latency_ms": latest.http_latency_ms,
            "avg_ping_latency_ms": self.average_ping_latency,
            "avg_http_latency_ms": self.average_http_latency,
        }
