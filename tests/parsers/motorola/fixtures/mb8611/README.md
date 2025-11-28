# Motorola MB8611 Test Fixtures

**Captured:** October 2025 by @dlindnegm (Issue #4)
**Firmware:** 8611-19.2.18

> Parser verification status is defined in `mb8611.py` - do not duplicate here.

## Modem Info

- **Model:** Motorola MB8611 (DOCSIS 3.1)
- **Channels:** 32 DS / 8 US + 2 OFDM
- **Protocol:** HNAP (HTTPS with self-signed certificate)

## Files

### HNAP API Response

- **hnap_full_status.json** - Complete `GetMultipleHNAPs` response with channel data
  - 33 downstream channels (including OFDM PLC)
  - 4 upstream channels
  - Format: Caret-delimited (`ID^Status^Mod^ChID^Freq^Power^SNR^Corr^Uncorr^`)

### HTML Pages (for field mapping reference)

| File | Purpose |
|------|---------|
| Login.html | Authentication page, HNAP JS init |
| MotoHome.html | Main dashboard |
| MotoStatusConnection.html | Channel data tables |
| MotoStatusSoftware.html | Hardware/software versions |
| MotoStatusSecurity.html | Reboot/restart functionality |
| MotoStatusLog.html | Event logs |

## Authentication

Uses HNAP challenge-response authentication (HMAC-MD5).
- Default credentials: `admin` / `motorola`
- Implementation credit: @BowlesCR (Chris Bowles)

## References

- Issue #4: Original fixture capture by @dlindnegm
- Issue #6: HNAP authentication implementation
- Prior art: xNinjaKittyx/mb8600 repository
