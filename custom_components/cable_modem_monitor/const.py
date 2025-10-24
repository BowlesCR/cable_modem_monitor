"""Constants for the Cable Modem Monitor integration."""

DOMAIN = "cable_modem_monitor"
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_HISTORY_DAYS = "history_days"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENTITY_PREFIX = "entity_prefix"

***REMOVED*** Entity naming options
ENTITY_PREFIX_DEFAULT = "default"  ***REMOVED*** No prefix (current behavior)
ENTITY_PREFIX_DOMAIN = "domain"  ***REMOVED*** Prefix with "cable_modem_"
ENTITY_PREFIX_IP = "ip_address"  ***REMOVED*** Prefix with IP address (e.g., "192_168_100_1_")
ENTITY_PREFIX_CUSTOM = "custom"  ***REMOVED*** User-defined custom prefix
CONF_CUSTOM_PREFIX = "custom_prefix"  ***REMOVED*** Store user's custom prefix text

***REMOVED*** Polling interval defaults based on industry best practices
***REMOVED*** References:
***REMOVED*** - SNMP Polling: https://obkio.com/blog/snmp-polling/
***REMOVED***   "5-10 minute intervals are standard for network devices"
***REMOVED*** - API Polling Best Practices: https://www.merge.dev/blog/api-polling-best-practices
***REMOVED***   "Polling more than once per second can overload servers"
***REMOVED*** - Network Device Polling: https://community.broadcom.com/communities/community-home/digestviewer/viewthread?MID=824934
***REMOVED***   "Client data polling should not be lower than 5 minutes"
DEFAULT_SCAN_INTERVAL = 600  ***REMOVED*** 10 minutes - balanced default for network monitoring
DEFAULT_HISTORY_DAYS = 30  ***REMOVED*** Default number of days to keep history
MIN_SCAN_INTERVAL = 60  ***REMOVED*** 1 minute - minimum to avoid device strain
MAX_SCAN_INTERVAL = 1800  ***REMOVED*** 30 minutes - maximum useful interval
