"""Base class for modem parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from custom_components.cable_modem_monitor.core.auth_config import AuthConfig


class ModemCapability(str, Enum):
    """Standardized capability names for modem parsers.

    These are the common field names that parsers can declare support for.
    The integration uses these to conditionally create entities.

    System Information:
        SYSTEM_UPTIME: Current uptime string (e.g., "7 days 00:00:01")
        LAST_BOOT_TIME: Calculated boot timestamp (ISO format)
        CURRENT_TIME: Current system time from modem
        HARDWARE_VERSION: Hardware/board version
        SOFTWARE_VERSION: Firmware/software version

    Channel Data:
        DOWNSTREAM_CHANNELS: DOCSIS 3.0 downstream channels
        UPSTREAM_CHANNELS: DOCSIS 3.0 upstream channels
        OFDM_DOWNSTREAM: DOCSIS 3.1 OFDM downstream channels
        OFDM_UPSTREAM: DOCSIS 3.1 OFDM upstream channels

    Actions:
        RESTART: Modem can be restarted via the integration
    """

    # System information
    SYSTEM_UPTIME = "system_uptime"
    LAST_BOOT_TIME = "last_boot_time"
    CURRENT_TIME = "current_time"
    HARDWARE_VERSION = "hardware_version"
    SOFTWARE_VERSION = "software_version"

    # Channel data
    DOWNSTREAM_CHANNELS = "downstream_channels"
    UPSTREAM_CHANNELS = "upstream_channels"
    OFDM_DOWNSTREAM = "ofdm_downstream"
    OFDM_UPSTREAM = "ofdm_upstream"

    # Actions
    RESTART = "restart"


class ModemParser(ABC):
    """Abstract base class for modem-specific HTML parsers."""

    # Parser metadata (override in subclasses)
    name: str = "Unknown"
    manufacturer: str = "Unknown"
    models: list[str] = []  # e.g., ["MB7621", "MB8600"]

    # Priority for parser selection (higher = tried first)
    # Use 100 for model-specific parsers, 50 for generic/fallback parsers
    # Default is 50 for backward compatibility
    priority: int = 50

    # Verification status - defaults to False until confirmed by real user
    # Set to True only after verification by maintainer or user report
    verified: bool = False
    # Optional: Link to issue, forum post, or commit confirming verification
    verification_source: str | None = None

    # URL patterns this parser can handle
    # Each pattern is a dict with 'path' and optionally 'auth_required'
    # auth_required: boolean (default True) - if False, can try without auth
    # The scraper will try URLs in the order specified
    url_patterns: list[dict[str, str | bool]] = []

    # Legacy field for backward compatibility (deprecated - use url_patterns)
    auth_type: str = "form"

    # Authentication configuration (new system - optional, for backward compatibility)
    # Parsers should define this as a class attribute
    auth_config: AuthConfig | None = None

    # Capabilities declaration - what data this parser can provide
    # Override in subclasses to declare supported capabilities
    # Format: set of ModemCapability enum values
    # Example: capabilities = {ModemCapability.DOWNSTREAM_CHANNELS, ModemCapability.SYSTEM_UPTIME}
    capabilities: set[ModemCapability] = set()

    @classmethod
    def has_capability(cls, capability: ModemCapability) -> bool:
        """Check if this parser supports a specific capability.

        Args:
            capability: The ModemCapability to check for

        Returns:
            True if the parser declares support for this capability
        """
        return capability in cls.capabilities

    @classmethod
    @abstractmethod
    def can_parse(cls, soup: BeautifulSoup, url: str, html: str) -> bool:
        """
        Detect if this parser can handle the modem's HTML.

        Args:
            soup: BeautifulSoup parsed HTML
            url: The URL that returned this HTML
            html: Raw HTML string

        Returns:
            True if this parser can handle this modem, False otherwise

        Example:
            return soup.find(string="Motorola Cable Modem") is not None
        """
        raise NotImplementedError

    @abstractmethod
    def login(self, session, base_url, username, password) -> bool | tuple[bool, str | None]:
        """
        Log in to the modem.

        Returns:
            bool: True if login successful (old style)
            tuple[bool, str | None]: (success, html) where html is authenticated page content
                                     or None if no credentials provided or login failed
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, soup: BeautifulSoup, session=None, base_url=None) -> dict:
        """
        Parse all data from the modem.

        Args:
            soup: BeautifulSoup object of the main page
            session: Optional requests.Session for fetching additional pages
            base_url: Optional base URL of the modem (e.g., "http://192.168.100.1")

        Returns:
            Dict with all parsed data:
            {
                "downstream": [],
                "upstream": [],
                "system_info": {},
            }
        """
        raise NotImplementedError
