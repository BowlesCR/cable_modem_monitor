***REMOVED*** Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

***REMOVED******REMOVED*** [1.0.0] - 2025-10-20

***REMOVED******REMOVED******REMOVED*** Added
- Initial release of Cable Modem Monitor integration
- Config flow for easy UI-based setup
- Support for Motorola MB series modems (DOCSIS 3.0)
- Per-channel sensors for downstream channels:
  - Power levels (dBmV)
  - Signal-to-Noise Ratio (SNR in dB)
  - Frequency (MHz)
  - Corrected errors
  - Uncorrected errors
- Per-channel sensors for upstream channels:
  - Power levels (dBmV)
  - Frequency (MHz)
- Summary sensors for total corrected/uncorrected errors
- Connection status sensor
- Session-based authentication for password-protected modems
- Automatic detection of modem page URLs
- Integration reload support (no restart required for updates)
- Custom integration icons and branding
- Comprehensive documentation and examples
- HACS compatibility

***REMOVED******REMOVED******REMOVED*** Security
- Credentials stored securely in Home Assistant's encrypted storage
- Session-based authentication with proper cookie handling
- No cloud services - all data stays local

***REMOVED******REMOVED******REMOVED*** Known Issues
- Modem-specific HTML parsing may need adjustment for some models
- Limited to HTTP (no HTTPS support for modem connections)

[1.0.0]: https://github.com/kwschulz/cable_modem_monitor/releases/tag/v1.0.0
