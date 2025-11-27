"""Parser for Motorola MB8600 cable modem using HNAP protocol."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time

from bs4 import BeautifulSoup

from custom_components.cable_modem_monitor.core.auth_config import HNAPAuthConfig
from custom_components.cable_modem_monitor.core.authentication import AuthStrategyType
from custom_components.cable_modem_monitor.core.hnap_builder import HNAPRequestBuilder
from custom_components.cable_modem_monitor.core.hnap_json_builder import HNAPJsonRequestBuilder

from ..base_parser import ModemCapability, ModemParser

_LOGGER = logging.getLogger(__name__)


class MotorolaMB8600HnapParser(ModemParser):
    """Parser for Motorola MB8600 cable modem using HNAP/SOAP protocol."""

    name = "Motorola MB8600 (HNAP)"
    manufacturer = "Motorola"
    models = ["MB8600"]
    priority = 101  # Higher priority for the API-based method

    # Verification status
    verified = False
    verification_source = "WIP"

    # HNAP authentication configuration
    auth_config = HNAPAuthConfig(
        strategy=AuthStrategyType.HNAP_SESSION,
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
        return (
            "MB8600" in html
            or "MB 8600" in html
            or (("HNAP" in html or "purenetworks.com/HNAP1" in html) and "Motorola" in html and "MB8600" in html)
        )

    @staticmethod
    def _hmac_md5_upper(key: str, message: str) -> str:
        """Generate HMAC-MD5 hash in uppercase (as used by MB8600)."""
        mac = hmac.new(key.encode(), message.encode(), digestmod=hashlib.md5)
        return mac.hexdigest().upper()

    def _send_soap_action(
        self,
        session,
        base_url: str,
        action: str,
        params: dict[str, str],
        private_key: str = "withoutloginkey",
    ) -> dict[str, str]:
        """
        Send a SOAP action using MB8600 authentication method.

        Based on modemLogin.py authentication logic.
        """
        soap_action_uri = f'"{self.auth_config.soap_action_namespace}{action}"'

        # Magic number from modem's JavaScript
        TIME_MODULO = 2_000_000_000_000
        current_time = str(round(time.time() * 1000) % TIME_MODULO)

        # Generate HNAP_AUTH header
        auth = f"{self._hmac_md5_upper(private_key, f'{current_time}{soap_action_uri}')} {current_time}"

        endpoint_url = f"{base_url.rstrip('/')}{self.auth_config.hnap_endpoint}"

        _LOGGER.debug("MB8600: Sending SOAP action %s to %s", action, endpoint_url)

        response = session.post(
            endpoint_url,
            headers={
                "SOAPAction": soap_action_uri,
                "HNAP_AUTH": auth,
            },
            json={action: {**params}},
            timeout=10,
        )
        response.raise_for_status()

        json_response = response.json()
        return json_response.get(f"{action}Response", {})

    def login(self, session, base_url, username, password) -> tuple[bool, str | None]:
        """
        Log in using MB8600 HNAP authentication.

        This implements the two-step authentication process used by MB8600:
        1. Request challenge with username
        2. Respond with hashed password using challenge
        """
        try:
            _LOGGER.debug("MB8600: Starting authentication process")

            # Step 1: Request login challenge
            resp = self._send_soap_action(
                session,
                base_url,
                "Login",
                {
                    "Action": "request",
                    "Username": username,
                },
            )

            # Set cookie from initial response
            cookie = resp.get("Cookie", "")
            if cookie:
                session.cookies.set("uid", cookie)

            # Generate private key from public key, password, and challenge
            public_key = resp.get("PublicKey", "")
            challenge = resp.get("Challenge", "")

            if not public_key or not challenge:
                _LOGGER.error("MB8600: Missing PublicKey or Challenge in login response")
                return (False, "Missing authentication parameters")

            private_key = self._hmac_md5_upper(
                f"{public_key}{password}",
                challenge,
            )
            session.cookies.set("PrivateKey", private_key)

            # Step 2: Complete login with hashed password
            login_password = self._hmac_md5_upper(private_key, challenge)

            resp = self._send_soap_action(
                session,
                base_url,
                "Login",
                {
                    "Action": "login",
                    "Username": username,
                    "LoginPassword": login_password,
                },
                private_key=private_key,
            )

            login_result = resp.get("LoginResult", "")
            _LOGGER.debug("MB8600: Login result: %s", login_result)

            if login_result == "OK" or login_result == "success":
                _LOGGER.info("MB8600: Authentication successful")
                return (True, login_result)
            else:
                _LOGGER.warning("MB8600: Authentication failed with result: %s", login_result)
                return (False, login_result)

        except Exception as e:
            _LOGGER.error("MB8600: Authentication error: %s", str(e), exc_info=True)
            return (False, str(e))

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
        """Parse modem data using HNAP requests with MB8600 authentication."""
        _LOGGER.debug("MB8600: Attempting HNAP communication")

        # Get private key from session cookies for authenticated requests
        private_key = session.cookies.get("PrivateKey", "withoutloginkey")

        # Make individual HNAP requests for all data
        hnap_actions = [
            "GetMotoStatusStartupSequence",
            "GetMotoStatusConnectionInfo",
            "GetMotoStatusDownstreamChannelInfo",
            "GetMotoStatusUpstreamChannelInfo",
            "GetMotoLagStatus",
        ]

        hnap_data = {}

        for action in hnap_actions:
            try:
                _LOGGER.debug("MB8600: Fetching %s", action)
                response = self._send_soap_action(session, base_url, action, {}, private_key=private_key)
                hnap_data[f"{action}Response"] = response
            except Exception as e:
                _LOGGER.warning("MB8600: Failed to fetch %s: %s", action, str(e))
                # Continue with other actions even if one fails
                hnap_data[f"{action}Response"] = {}

        # Enhanced logging to help diagnose response structure
        _LOGGER.debug("MB8600: HNAP responses received. Actions completed: %d", len(hnap_data))

        # Parse channels and system info
        downstream = self._parse_downstream_from_hnap(hnap_data)
        upstream = self._parse_upstream_from_hnap(hnap_data)
        system_info = self._parse_system_info_from_hnap(hnap_data)

        _LOGGER.info(
            "MB8600: Successfully parsed data using HNAP (downstream: %d channels, upstream: %d channels)",
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

