"""Standalone HAR and HTML sanitization utilities.

This module provides PII sanitization for HAR (HTTP Archive) and HTML files
WITHOUT requiring Home Assistant installation. It's designed for use with
the capture_modem.py script and other standalone tools.

The sanitization logic is duplicated from custom_components/.../utils/ to
allow the capture script to run without installing the full integration.
Both copies should be kept in sync for consistency.

PII Categories Removed:
    - MAC addresses (all formats)
    - Serial numbers
    - Account/Subscriber IDs
    - Private/Public IP addresses (except common modem IPs)
    - IPv6 addresses
    - Passwords and passphrases
    - Session tokens and cookies
    - CSRF tokens
    - Email addresses
    - Config file paths (may contain ISP/customer info)
"""

from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

***REMOVED*** =============================================================================
***REMOVED*** HTML Sanitization (from html_helper.py)
***REMOVED*** =============================================================================


def sanitize_html(html: str) -> str:
    """Remove sensitive information from HTML.

    This function sanitizes modem HTML to remove PII before inclusion in
    diagnostics or fixture files. It's designed to be thorough while
    preserving data structure for debugging.

    Args:
        html: Raw HTML from modem

    Returns:
        Sanitized HTML with personal info removed
    """
    ***REMOVED*** 1. MAC Addresses (various formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
    html = re.sub(r"\b([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b", "XX:XX:XX:XX:XX:XX", html)

    ***REMOVED*** 2. Serial Numbers (various label formats)
    html = re.sub(
        r"(Serial\s*Number|SerialNum|SN|S/N)\s*[:\s=]*(?:<[^>]*>)*\s*([a-zA-Z0-9\-]{5,})",
        r"\1: ***REDACTED***",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 3. Account/Subscriber IDs
    html = re.sub(
        r"(Account|Subscriber|Customer|Device)\s*(ID|Number)\s*[:\s=]+\S+",
        r"\1 \2: ***REDACTED***",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 4. Private IP addresses (keep common modem IPs for context)
    ***REMOVED*** Preserves: 192.168.100.1, 192.168.0.1, 192.168.1.1, 10.0.0.1
    html = re.sub(
        r"\b(?!192\.168\.100\.1\b)(?!192\.168\.0\.1\b)(?!192\.168\.1\.1\b)(?!10\.0\.0\.1\b)"
        r"(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b",
        "***PRIVATE_IP***",
        html,
    )

    ***REMOVED*** 5. Public IP addresses (any non-private, non-localhost IP)
    html = re.sub(
        r"\b(?!10\.)(?!172\.(?:1[6-9]|2[0-9]|3[01])\.)(?!192\.168\.)"
        r"(?!127\.)(?!0\.)(?!255\.)"
        r"(?:[1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\."
        r"(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\."
        r"(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\."
        r"(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\b",
        "***PUBLIC_IP***",
        html,
    )

    ***REMOVED*** 6. IPv6 Addresses (full and compressed)
    ***REMOVED*** Only match if it contains at least one hex letter (a-f) to avoid matching
    ***REMOVED*** time formats like "12:34:56" which only contain digits
    def replace_ipv6(match: re.Match[str]) -> str:
        text: str = match.group(0)
        if re.search(r"[a-f]", text, re.IGNORECASE):
            return "***IPv6***"
        return text

    html = re.sub(
        r"\b([0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}\b",
        replace_ipv6,
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 7. Passwords/Passphrases in HTML forms or text
    html = re.sub(
        r'(password|passphrase|psk|key|wpa[0-9]*key)\s*[=:]\s*["\\]?([^"\'<>\s]+)',
        r"\1=***REDACTED***",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 8. Password input fields
    html = re.sub(
        r'(<input[^>]*type=["\\]?password["\\]?[^>]*value=["\\]?)([^"\\]+)(["\\]?)',
        r"\1***REDACTED***\3",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 9. Session tokens/cookies (long alphanumeric strings)
    html = re.sub(
        r'(session|token|auth|cookie)\s*[=:]\s*["\\]?([^"\'<>\s]{20,})',
        r"\1=***REDACTED***",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 10. CSRF tokens in meta tags
    html = re.sub(
        r'(<meta[^>]*name=["\\]?csrf-token["\\]?[^>]*content=["\\]?)([^"\\]+)(["\\]?)',
        r"\1***REDACTED***\3",
        html,
        flags=re.IGNORECASE,
    )

    ***REMOVED*** 11. Email addresses
    html = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "***EMAIL***",
        html,
    )

    ***REMOVED*** 12. Config file paths (may contain ISP/customer identifiers)
    html = re.sub(
        r"(Config\s*File\s*Name|config\s*file)\s*[:\s=]+([^\s<>]+\.cfg)",
        r"\1: ***CONFIG_PATH***",
        html,
        flags=re.IGNORECASE,
    )

    return html


***REMOVED*** =============================================================================
***REMOVED*** HAR Sanitization (from har_sanitizer.py)
***REMOVED*** =============================================================================

***REMOVED*** Sensitive header names (case-insensitive)
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "x-api-key",
    "x-session-id",
    "x-csrf-token",
}

***REMOVED*** Sensitive form field names (case-insensitive patterns)
SENSITIVE_FIELD_PATTERNS = [
    r"password",
    r"passwd",
    r"pwd",
    r"pass",
    r"secret",
    r"token",
    r"key",
    r"auth",
    r"credential",
    r"apikey",
    r"api_key",
]

***REMOVED*** Compile patterns for efficiency
_SENSITIVE_FIELD_RE = re.compile(
    "|".join(SENSITIVE_FIELD_PATTERNS),
    re.IGNORECASE,
)


def is_sensitive_field(field_name: str) -> bool:
    """Check if a form field name is sensitive."""
    return bool(_SENSITIVE_FIELD_RE.search(field_name))


def sanitize_header_value(name: str, value: str) -> str:
    """Sanitize a header value if it's sensitive."""
    if name.lower() in SENSITIVE_HEADERS:
        if name.lower() in ("cookie", "set-cookie"):
            ***REMOVED*** Preserve cookie names, redact values
            def redact_cookie(match: re.Match) -> str:
                cookie_name = match.group(1)
                return f"{cookie_name}=[REDACTED]"

            return re.sub(r"([^=;\s]+)=([^;]*)", redact_cookie, value)

        return "[REDACTED]"

    return value


def _sanitize_form_urlencoded(text: str) -> str:
    """Sanitize form-urlencoded text by redacting sensitive fields."""
    pairs = []
    for pair in text.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            if is_sensitive_field(key):
                value = "[REDACTED]"
            pairs.append(f"{key}={value}")
        else:
            pairs.append(pair)
    return "&".join(pairs)


def _sanitize_json_text(text: str) -> str:
    """Sanitize JSON text by redacting sensitive fields."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in data:
                if is_sensitive_field(key):
                    data[key] = "[REDACTED]"
        return json.dumps(data)
    except json.JSONDecodeError:
        return text


def sanitize_post_data(post_data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Sanitize POST data while preserving field names."""
    if not post_data:
        return post_data

    result = copy.deepcopy(post_data)

    ***REMOVED*** Sanitize params array
    if "params" in result and isinstance(result["params"], list):
        for param in result["params"]:
            if isinstance(param, dict) and "name" in param and is_sensitive_field(param["name"]):
                param["value"] = "[REDACTED]"

    ***REMOVED*** Sanitize raw text (form-urlencoded or JSON)
    if "text" in result and result["text"]:
        text = result["text"]
        mime_type = result.get("mimeType", "")

        if "application/x-www-form-urlencoded" in mime_type:
            result["text"] = _sanitize_form_urlencoded(text)
        elif "application/json" in mime_type:
            result["text"] = _sanitize_json_text(text)

    return result


def _sanitize_json_recursive(data: Any) -> Any:
    """Recursively sanitize JSON data."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if is_sensitive_field(key) and isinstance(value, str):
                result[key] = "[REDACTED]"
            else:
                result[key] = _sanitize_json_recursive(value)
        return result
    elif isinstance(data, list):
        return [_sanitize_json_recursive(item) for item in data]
    return data


def _sanitize_headers(headers: list[dict[str, Any]]) -> None:
    """Sanitize a list of headers in-place."""
    for header in headers:
        if isinstance(header, dict) and "name" in header and "value" in header:
            header["value"] = sanitize_header_value(header["name"], header["value"])


def _sanitize_request(req: dict[str, Any]) -> None:
    """Sanitize a HAR request object in-place."""
    if "headers" in req and isinstance(req["headers"], list):
        _sanitize_headers(req["headers"])

    if "postData" in req:
        req["postData"] = sanitize_post_data(req["postData"])

    if "queryString" in req and isinstance(req["queryString"], list):
        for param in req["queryString"]:
            if isinstance(param, dict) and "name" in param and is_sensitive_field(param["name"]):
                param["value"] = "[REDACTED]"


def _sanitize_response_content(content: dict[str, Any]) -> None:
    """Sanitize response content in-place."""
    if "text" not in content or not content["text"]:
        return

    mime_type = content.get("mimeType", "")

    if "text/html" in mime_type or "text/xml" in mime_type:
        content["text"] = sanitize_html(content["text"])
    elif "application/json" in mime_type:
        try:
            data = json.loads(content["text"])
            content["text"] = json.dumps(_sanitize_json_recursive(data))
        except json.JSONDecodeError:
            pass


def _sanitize_response(resp: dict[str, Any]) -> None:
    """Sanitize a HAR response object in-place."""
    if "headers" in resp and isinstance(resp["headers"], list):
        _sanitize_headers(resp["headers"])

    if "content" in resp and isinstance(resp["content"], dict):
        _sanitize_response_content(resp["content"])


def sanitize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a single HAR entry (request/response pair)."""
    result = copy.deepcopy(entry)

    if "request" in result:
        _sanitize_request(result["request"])

    if "response" in result:
        _sanitize_response(result["response"])

    return result


def sanitize_har(har_data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize an entire HAR file."""
    result = copy.deepcopy(har_data)

    if "log" not in result:
        _LOGGER.warning("HAR data missing 'log' key")
        return result

    log = result["log"]

    ***REMOVED*** Sanitize all entries
    if "entries" in log and isinstance(log["entries"], list):
        log["entries"] = [sanitize_entry(entry) for entry in log["entries"]]

    ***REMOVED*** Sanitize pages (if present)
    if "pages" in log and isinstance(log["pages"], list):
        for page in log["pages"]:
            if isinstance(page, dict) and "title" in page:
                page["title"] = sanitize_html(page["title"])

    return result


def sanitize_har_file(input_path: str, output_path: str | None = None) -> str:
    """Sanitize a HAR file and optionally write to a new file.

    Args:
        input_path: Path to input HAR file
        output_path: Path to output file (default: input_path with .sanitized.har suffix)

    Returns:
        Path to the sanitized file
    """
    if output_path is None:
        if input_path.endswith(".har"):
            output_path = input_path[:-4] + ".sanitized.har"
        else:
            output_path = input_path + ".sanitized.har"

    with open(input_path, encoding="utf-8") as f:
        har_data = json.load(f)

    sanitized = sanitize_har(har_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, indent=2)

    _LOGGER.info("Sanitized HAR written to: %s", output_path)
    return output_path
