"""Parser for Motorola MB8600 cable modem using HNAP protocol."""

from __future__ import annotations

import json
import logging

from bs4 import BeautifulSoup

from ...core.auth_config import HNAPAuthConfig
from ...core.authentication import AuthStrategyType
from ...core.hnap_json_builder import HNAPJsonRequestBuilder

from ..base_parser import ModemCapability, ModemParser

_LOGGER = logging.getLogger(__name__)


class MotorolaMB8600HnapParser(ModemParser):
    """Parser for Motorola MB8600 cable modem using HNAP JSON protocol."""

    name = "Motorola MB8600 (HNAP)"
    manufacturer = "Motorola"
    models = ["MB8600"]
    priority = 101  # Higher priority for the API-based method

    # Verification status
    verified = False
    verification_source = "WIP"

    # HNAP authentication configuration
    auth_config = HNAPAuthConfig(
        strategy=AuthStrategyType.HNAP_JSON,
        login_url="/Login.html",
        hnap_endpoint="/HNAP1/",
        session_timeout_indicator="UN-AUTH",
        soap_action_namespace="http://purenetworks.com/HNAP1/",
    )

    url_patterns = [
        {"path": "/HNAP1/", "auth_method": "hnap", "auth_required": True},
        {"path": "/MotoStatusConnection.html", "auth_method": "hnap", "auth_required": True},
    ]

    # Capabilities - MB8600 HNAP parser
    capabilities = {
        ModemCapability.DOWNSTREAM_CHANNELS,
        ModemCapability.UPSTREAM_CHANNELS,
        ModemCapability.SYSTEM_UPTIME,
    }

    @classmethod
    def can_parse(cls, soup: BeautifulSoup, url: str, html: str) -> bool:
        """Detect if this is a Motorola MB8600 modem."""
        return ("HNAP" in html or "purenetworks.com/HNAP1" in html) and "Motorola" in html and "MB8600" in html

    def login(self, session, base_url, username, password) -> tuple[bool, str | None]:
        """Perform login using HNAP JSON authentication.

        Args:
            session: Requests session
            base_url: Modem base URL
            username: Username for authentication
            password: Password for authentication

        Returns:
            Tuple of (success: bool, login_result: str | None)
        """
        from ...core.authentication import AuthFactory

        auth_strategy = AuthFactory.get_strategy(self.auth_config.strategy)
        success, result = auth_strategy.login(session, base_url, username, password, self.auth_config)
        return (success, result)

    def _is_auth_failure(self, error: Exception) -> bool:
        """
        Detect if an exception indicates an authentication failure.

        Common auth failure indicators:
        - HTTP 401/403 status codes
        - "LoginResult":"FAILED" in response
        - "Unauthorized" or "Forbidden" in error message
        - Session timeout or invalid session errors
        """
        error_str = str(error).lower()

        # Check for common auth failure indicators
        auth_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "authentication failed",
            "login failed",
            "invalid credentials",
            "session timeout",
            "invalid session",
            '"loginresult":"failed"',
            '"loginresult": "failed"',
        ]

        return any(indicator in error_str for indicator in auth_indicators)

    def parse(self, soup: BeautifulSoup, session=None, base_url=None) -> dict:
        """
        Parse data using HNAP calls with MB8600 authentication.

        Args:
            soup: BeautifulSoup object (may not be used for HNAP modems)
            session: requests.Session with authenticated session
            base_url: Modem base URL

        Returns:
            Dict with downstream, upstream, and system_info
        """
        if not session or not base_url:
            raise ValueError("MB8600 requires session and base_url for HNAP calls")

        try:
            return self._parse_with_hnap(session, base_url)
        except Exception as error:
            _LOGGER.error("MB8600: HNAP parsing failed: %s", str(error), exc_info=True)

            # Check if failure is due to authentication issues
            auth_failure = self._is_auth_failure(error)

            result: dict[str, list | dict] = {"downstream": [], "upstream": [], "system_info": {}}

            if auth_failure:
                # Mark as auth failure so config_flow can block setup
                result["_auth_failure"] = True  # type: ignore[assignment]
                result["_login_page_detected"] = True  # type: ignore[assignment]
                result["_diagnostic_context"] = {
                    "parser": "MB8600 HNAP",
                    "error": str(error)[:200],
                    "error_type": "HNAP authentication failure",
                }
                _LOGGER.warning("MB8600: HNAP authentication failure detected - modem requires valid credentials")

            return result

    def _parse_with_hnap(self, session, base_url: str) -> dict:
        """Parse modem data using JSON-based HNAP requests."""
        _LOGGER.debug("MB8600: Attempting JSON-based HNAP communication")

        # Build JSON HNAP request builder
        builder = HNAPJsonRequestBuilder(
            endpoint=self.auth_config.hnap_endpoint, namespace=self.auth_config.soap_action_namespace
        )

        # Make batched HNAP request for all data
        hnap_actions = [
            "GetMotoStatusStartupSequence",
            "GetMotoStatusConnectionInfo",
            "GetMotoStatusDownstreamChannelInfo",
            "GetMotoStatusUpstreamChannelInfo",
            "GetMotoLagStatus",
        ]

        _LOGGER.debug("MB8600: Fetching modem data via JSON HNAP GetMultipleHNAPs")
        json_response = builder.call_multiple(session, base_url, hnap_actions)

        # Parse JSON response
        response_data = json.loads(json_response)

        # Extract nested response
        hnap_data = response_data.get("GetMultipleHNAPsResponse", response_data)

        # Enhanced logging to help diagnose response structure
        _LOGGER.debug(
            "MB8600: JSON HNAP response received. Top-level keys: %s, response size: %d bytes",
            list(hnap_data.keys()),
            len(json_response),
        )

        # Parse channels and system info
        downstream = self._parse_downstream_from_hnap(hnap_data)
        upstream = self._parse_upstream_from_hnap(hnap_data)
        system_info = self._parse_system_info_from_hnap(hnap_data)

        _LOGGER.info(
            "MB8600: Successfully parsed data using JSON HNAP. (downstream: %d channels, upstream: %d channels)",
            len(downstream),
            len(upstream),
        )

        return {
            "downstream": downstream,
            "upstream": upstream,
            "system_info": system_info,
        }

    def _parse_downstream_from_hnap(self, hnap_data: dict) -> list[dict]:
        """
        Parse downstream channels from HNAP JSON response.

        Format: "ID^Status^Mod^ChID^Freq^Power^SNR^Corr^Uncorr^|+|..."
        Example: "1^Locked^QAM256^20^543.0^ 1.4^45.1^41^0^"
        """
        channels: list[dict] = []

        try:
            downstream_response = hnap_data.get("GetMotoStatusDownstreamChannelInfoResponse", {})
            channel_data = downstream_response.get("MotoConnDownstreamChannel", "")

            if not channel_data:
                # Enhanced logging to help diagnose the issue
                _LOGGER.warning(
                    "MB8600: No downstream channel data found. "
                    "Response keys: %s, downstream_response type: %s, content: %s",
                    list(hnap_data.keys()),
                    type(downstream_response).__name__,
                    str(downstream_response)[:500] if downstream_response else "empty",
                )
                return channels

            # Split by |+| delimiter
            channel_entries = channel_data.split("|+|")

            for entry in channel_entries:
                if not entry.strip():
                    continue

                # Split by ^ delimiter
                fields = entry.split("^")

                if len(fields) < 9:
                    _LOGGER.warning("MB8600: Invalid downstream channel entry: %s", entry)
                    continue

                try:
                    # Parse channel fields
                    channel_id = int(fields[0])
                    lock_status = fields[1].strip()
                    modulation = fields[2].strip()
                    ch_id = int(fields[3])
                    frequency = int(round(float(fields[4].strip()) * 1_000_000))  # MHz to Hz
                    power = float(fields[5].strip())
                    snr = float(fields[6].strip())
                    corrected = int(fields[7])
                    uncorrected = int(fields[8])

                    channel_info = {
                        "channel_id": channel_id,
                        "lock_status": lock_status,
                        "modulation": modulation,
                        "ch_id": ch_id,
                        "frequency": int(frequency),
                        "power": power,
                        "snr": snr,
                        "corrected": corrected,
                        "uncorrected": uncorrected,
                    }

                    channels.append(channel_info)

                except (ValueError, IndexError) as e:
                    _LOGGER.warning("MB8600: Error parsing downstream channel: %s - %s", entry, e)
                    continue

        except Exception as e:
            _LOGGER.error("MB8600: Error parsing downstream channels: %s", e)

        return channels

    def _parse_upstream_from_hnap(self, hnap_data: dict) -> list[dict]:
        """
        Parse upstream channels from HNAP JSON response.

        Format: "ID^Status^Mod^ChID^SymbolRate^Freq^Power^|+|..."
        Example: "1^Locked^SC-QAM^17^5120^16.4^44.3^"
        """
        channels: list[dict] = []

        try:
            upstream_response = hnap_data.get("GetMotoStatusUpstreamChannelInfoResponse", {})
            channel_data = upstream_response.get("MotoConnUpstreamChannel", "")

            if not channel_data:
                # Enhanced logging to help diagnose the issue
                _LOGGER.warning(
                    "MB8600: No upstream channel data found. "
                    "Response keys: %s, upstream_response type: %s, content: %s",
                    list(hnap_data.keys()),
                    type(upstream_response).__name__,
                    str(upstream_response)[:500] if upstream_response else "empty",
                )
                return channels

            # Split by |+| delimiter
            channel_entries = channel_data.split("|+|")

            for entry in channel_entries:
                if not entry.strip():
                    continue

                # Split by ^ delimiter
                fields = entry.split("^")

                if len(fields) < 7:
                    _LOGGER.warning("MB8600: Invalid upstream channel entry: %s", entry)
                    continue

                try:
                    # Parse channel fields
                    channel_id = int(fields[0])
                    lock_status = fields[1].strip()
                    modulation = fields[2].strip()
                    ch_id = int(fields[3])
                    symbol_rate = int(fields[4])
                    frequency = int(round(float(fields[5].strip()) * 1_000_000))  # MHz to Hz
                    power = float(fields[6].strip())

                    channel_info = {
                        "channel_id": channel_id,
                        "lock_status": lock_status,
                        "modulation": modulation,
                        "ch_id": ch_id,
                        "symbol_rate": symbol_rate,
                        "frequency": int(frequency),
                        "power": power,
                    }

                    channels.append(channel_info)

                except (ValueError, IndexError) as e:
                    _LOGGER.warning("MB8600: Error parsing upstream channel: %s - %s", entry, e)
                    continue

        except Exception as e:
            _LOGGER.error("MB8600: Error parsing upstream channels: %s", e)

        return channels

    def _parse_system_info_from_hnap(self, hnap_data: dict) -> dict:
        """Parse system info from HNAP JSON response."""
        system_info: dict[str, str] = {}

        try:
            self._extract_connection_info(hnap_data, system_info)
            self._extract_startup_info(hnap_data, system_info)
        except Exception as e:
            _LOGGER.error("MB8600: Error parsing system info: %s", e)

        return system_info

    def _extract_connection_info(self, hnap_data: dict, system_info: dict) -> None:
        """Extract connection info fields from HNAP data."""
        conn_info = hnap_data.get("GetMotoStatusConnectionInfoResponse", {})
        if not conn_info:
            return

        self._set_if_present(conn_info, "MotoConnSystemUpTime", system_info, "system_uptime")
        self._set_if_present(conn_info, "MotoConnNetworkAccess", system_info, "network_access")

    def _extract_startup_info(self, hnap_data: dict, system_info: dict) -> None:
        """Extract startup sequence info fields from HNAP data."""
        startup_info = hnap_data.get("GetMotoStatusStartupSequenceResponse", {})
        if not startup_info:
            return

        self._set_if_present(startup_info, "MotoConnDSFreq", system_info, "downstream_frequency")
        self._set_if_present(startup_info, "MotoConnConnectivityStatus", system_info, "connectivity_status")
        self._set_if_present(startup_info, "MotoConnBootStatus", system_info, "boot_status")
        self._set_if_present(startup_info, "MotoConnSecurityStatus", system_info, "security_status")
        self._set_if_present(startup_info, "MotoConnSecurityComment", system_info, "security_comment")

    def _set_if_present(self, source: dict, source_key: str, target: dict, target_key: str) -> None:
        """Set target[key] if source[source_key] exists and is non-empty."""
        value = source.get(source_key, "")
        if value:
            target[target_key] = value
