"""Constants for the Cable Modem Monitor integration."""

DOMAIN = "cable_modem_monitor"
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_HISTORY_DAYS = "history_days"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENTITY_PREFIX = "entity_prefix"

# Entity naming options
ENTITY_PREFIX_DEFAULT = "default"  # No prefix (current behavior)
ENTITY_PREFIX_DOMAIN = "domain"  # Prefix with "cable_modem_"
ENTITY_PREFIX_IP = "ip_address"  # Prefix with IP address (e.g., "192_168_100_1_")
ENTITY_PREFIX_CUSTOM = "custom"  # User-defined custom prefix
CONF_CUSTOM_PREFIX = "custom_prefix"  # Store user's custom prefix text

# Polling interval defaults based on industry best practices
# References:
# - SNMP Polling: https://obkio.com/blog/snmp-polling/
#   "5-10 minute intervals are standard for network devices"
# - API Polling Best Practices: https://www.merge.dev/blog/api-polling-best-practices
#   "Polling more than once per second can overload servers"
# - Network Device Polling: https://community.broadcom.com/communities/community-home/digestviewer/viewthread?MID=824934
#   "Client data polling should not be lower than 5 minutes"
DEFAULT_SCAN_INTERVAL = 600  # 10 minutes - balanced default for network monitoring
DEFAULT_HISTORY_DAYS = 30  # Default number of days to keep history
MIN_SCAN_INTERVAL = 60  # 1 minute - minimum to avoid device strain
MAX_SCAN_INTERVAL = 1800  # 30 minutes - maximum useful interval
