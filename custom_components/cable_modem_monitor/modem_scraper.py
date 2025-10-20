"""Web scraper for cable modem data."""
import logging
import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class ModemScraper:
    """Scrape data from cable modem web interface."""

    def __init__(self, host: str, username: str = None, password: str = None):
        """Initialize the modem scraper."""
        self.host = host
        self.base_url = f"http://{host}"
        self.username = username
        self.password = password
        self.session = requests.Session()

    def _login(self) -> bool:
        """Log in to the modem web interface."""
        if not self.username or not self.password:
            _LOGGER.debug("No credentials provided, skipping login")
            return True

        try:
            login_url = f"{self.base_url}/goform/login"
            login_data = {
                "loginUsername": self.username,
                "loginPassword": self.password,
            }
            _LOGGER.info(f"Attempting login to {login_url} as user '{self.username}'")

            ***REMOVED*** Don't follow redirects automatically so we can check the response
            response = self.session.post(login_url, data=login_data, timeout=10, allow_redirects=True)

            _LOGGER.info(f"Login response: status={response.status_code}, url={response.url}")

            ***REMOVED*** Motorola modems have unusual behavior - they redirect to login.asp
            ***REMOVED*** even on successful login, but the session cookie is set correctly.
            ***REMOVED*** Test if we can access a protected page to verify login success.
            test_response = self.session.get(f"{self.base_url}/MotoConnection.asp", timeout=10)
            _LOGGER.info(f"Login verification: test page status={test_response.status_code}")

            if test_response.status_code == 200 and len(test_response.text) > 1000:
                _LOGGER.info("Login successful - verified by accessing protected page")
                return True
            else:
                _LOGGER.error(f"Login failed - could not access protected page (status={test_response.status_code}, length={len(test_response.text)})")
                return False

        except requests.RequestException as e:
            _LOGGER.error(f"Login failed: {type(e).__name__}: {e}")
            return False

    def get_modem_data(self) -> dict:
        """Fetch and parse modem data."""
        try:
            ***REMOVED*** Login first if credentials are provided
            if not self._login():
                _LOGGER.error("Failed to log in to modem")
                return {"connection_status": "offline", "downstream": [], "upstream": []}

            ***REMOVED*** Try common Motorola modem signal data URLs
            ***REMOVED*** MotoConnection.asp is the primary page for Motorola modems (MB series)
            urls_to_try = [
                f"{self.base_url}/MotoConnection.asp",
                f"{self.base_url}/MotoHome.asp",
                f"{self.base_url}/cmSignalData.htm",
                f"{self.base_url}/cmSignal.html",
                f"{self.base_url}/",
            ]

            html = None
            for url in urls_to_try:
                try:
                    _LOGGER.info(f"Attempting to fetch {url}")
                    response = self.session.get(url, timeout=10)
                    _LOGGER.info(f"Response from {url}: status={response.status_code}")
                    if response.status_code == 200:
                        html = response.text
                        _LOGGER.info(f"Successfully fetched data from {url}")
                        break
                    else:
                        _LOGGER.warning(f"Got status {response.status_code} from {url}")
                except requests.RequestException as e:
                    _LOGGER.error(f"Failed to fetch from {url}: {type(e).__name__}: {e}")
                    continue

            if not html:
                _LOGGER.error("Could not fetch data from any known modem URL")
                return {"connection_status": "offline", "downstream": [], "upstream": []}

            soup = BeautifulSoup(html, "html.parser")

            ***REMOVED*** Parse downstream channels
            downstream_channels = self._parse_downstream_channels(soup)

            ***REMOVED*** Parse upstream channels
            upstream_channels = self._parse_upstream_channels(soup)

            ***REMOVED*** Calculate totals
            total_corrected = sum(
                ch.get("corrected", 0) for ch in downstream_channels
            )
            total_uncorrected = sum(
                ch.get("uncorrected", 0) for ch in downstream_channels
            )

            return {
                "connection_status": "online" if downstream_channels else "offline",
                "downstream": downstream_channels,
                "upstream": upstream_channels,
                "total_corrected": total_corrected,
                "total_uncorrected": total_uncorrected,
            }

        except Exception as e:
            _LOGGER.error(f"Error fetching modem data: {e}")
            return {"connection_status": "offline", "downstream": [], "upstream": []}

    def _parse_downstream_channels(self, soup: BeautifulSoup) -> list:
        """Parse downstream channel data from HTML."""
        channels = []

        try:
            ***REMOVED*** Motorola MB series modems use specific table structure
            ***REMOVED*** Look for table with "Downstream Bonded Channels" title
            tables = soup.find_all("table")
            _LOGGER.debug(f"Found {len(tables)} tables to parse")

            for table in tables:
                ***REMOVED*** Check if this table contains downstream channel data
                ***REMOVED*** Look for headers: Channel, Lock Status, Modulation, etc.
                header_row = table.find("tr")
                if not header_row:
                    continue

                headers = [td.text.strip() for td in header_row.find_all("td", class_="moto-param-header-s")]

                ***REMOVED*** If we found the header row with channel data headers
                if headers and "Channel" in headers:
                    _LOGGER.debug(f"Found downstream channel table with headers: {headers}")
                    rows = table.find_all("tr")[1:]  ***REMOVED*** Skip header row

                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 9:  ***REMOVED*** Channel, Lock, Modulation, ID, Freq, Pwr, SNR, Corrected, Uncorrected
                            try:
                                channel_data = {
                                    "channel": self._extract_number(cols[0].text),
                                    "frequency": self._extract_float(cols[4].text),  ***REMOVED*** Freq column
                                    "power": self._extract_float(cols[5].text),      ***REMOVED*** Pwr column
                                    "snr": self._extract_float(cols[6].text),        ***REMOVED*** SNR column
                                    "corrected": self._extract_number(cols[7].text),
                                    "uncorrected": self._extract_number(cols[8].text),
                                }
                                channels.append(channel_data)
                                _LOGGER.debug(f"Parsed downstream channel {channel_data['channel']}: {channel_data}")
                            except Exception as e:
                                _LOGGER.error(f"Error parsing downstream channel row: {e}")
                                continue

            _LOGGER.debug(f"Total downstream channels parsed: {len(channels)}")

        except Exception as e:
            _LOGGER.error(f"Error parsing downstream channels: {e}")

        return channels

    def _parse_upstream_channels(self, soup: BeautifulSoup) -> list:
        """Parse upstream channel data from HTML."""
        channels = []

        try:
            ***REMOVED*** Look for upstream channel table (similar structure to downstream)
            tables = soup.find_all("table")

            for table in tables:
                header_row = table.find("tr")
                if not header_row:
                    continue

                headers = [td.text.strip() for td in header_row.find_all("td", class_="moto-param-header-s")]

                ***REMOVED*** Look for upstream-specific headers
                if headers and any(keyword in " ".join(headers).lower() for keyword in ["upstream", "transmit", "symbol rate"]):
                    _LOGGER.debug(f"Found upstream channel table with headers: {headers}")
                    rows = table.find_all("tr")[1:]  ***REMOVED*** Skip header row

                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 6:  ***REMOVED*** Typical upstream: Channel, Lock, Type, ID, Freq, Power
                            try:
                                channel_data = {
                                    "channel": self._extract_number(cols[0].text),
                                    "frequency": self._extract_float(cols[4].text),  ***REMOVED*** Freq column
                                    "power": self._extract_float(cols[5].text),      ***REMOVED*** Power column
                                }
                                channels.append(channel_data)
                                _LOGGER.debug(f"Parsed upstream channel {channel_data['channel']}: {channel_data}")
                            except Exception as e:
                                _LOGGER.error(f"Error parsing upstream channel row: {e}")
                                continue

            _LOGGER.debug(f"Total upstream channels parsed: {len(channels)}")

        except Exception as e:
            _LOGGER.error(f"Error parsing upstream channels: {e}")

        return channels

    def _extract_number(self, text: str) -> int:
        """Extract integer from text."""
        try:
            ***REMOVED*** Remove common units and extract number
            cleaned = "".join(c for c in text if c.isdigit() or c == "-")
            return int(cleaned) if cleaned else 0
        except ValueError:
            return 0

    def _extract_float(self, text: str) -> float:
        """Extract float from text."""
        try:
            ***REMOVED*** Remove units (dB, dBmV, MHz, etc.) and extract number
            cleaned = "".join(c for c in text if c.isdigit() or c in ".-")
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
