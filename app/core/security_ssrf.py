"""
SSRF Protection Module

Protects against Server-Side Request Forgery attacks by validating URLs
and blocking access to private networks, localhost, and cloud metadata endpoints.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional


# Private IP ranges to block
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),  # Localhost
    ipaddress.ip_network('169.254.0.0/16'),  # Link-local
    ipaddress.ip_network('::1/128'),  # IPv6 localhost
    ipaddress.ip_network('fc00::/7'),  # IPv6 private
    ipaddress.ip_network('fe80::/10'),  # IPv6 link-local
]

# Cloud metadata endpoints to block
BLOCKED_HOSTNAMES = [
    'metadata.google.internal',  # GCP
    '169.254.169.254',  # AWS, Azure, GCP metadata
    'metadata.azure.com',  # Azure
    'instance-data',  # AWS alternative
    'metadata',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]


def is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is private/internal."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for private_range in PRIVATE_IP_RANGES:
            if ip in private_range:
                return True
        return False
    except ValueError:
        return False


def is_blocked_hostname(hostname: str) -> bool:
    """Check if hostname is in blocklist."""
    hostname_lower = hostname.lower()
    for blocked in BLOCKED_HOSTNAMES:
        if blocked in hostname_lower:
            return True
    return False


def resolve_hostname_safely(hostname: str) -> Optional[str]:
    """
    Resolve hostname to IP address and validate it's not private.

    Returns:
        IP address if valid, None if blocked or resolution fails
    """
    try:
        # First check if hostname itself is blocked
        if is_blocked_hostname(hostname):
            return None

        # Resolve hostname to IP
        ip = socket.gethostbyname(hostname)

        # Check if resolved IP is private
        if is_private_ip(ip):
            return None

        return ip
    except (socket.gaierror, socket.herror):
        # DNS resolution failed
        return None


def validate_url_for_ssrf(url: str) -> Tuple[bool, str]:
    """
    Validate URL against SSRF attacks.

    Args:
        url: The URL to validate

    Returns:
        (is_valid, error_message) tuple
        - is_valid: True if URL is safe, False if blocked
        - error_message: Description of why URL was blocked (empty if valid)
    """
    try:
        parsed = urlparse(url)

        # 1. Check scheme (only http/https allowed)
        if parsed.scheme not in ['http', 'https']:
            return False, f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed."

        # 2. Check hostname exists
        if not parsed.hostname:
            return False, "URL must have a valid hostname."

        hostname = parsed.hostname.lower()

        # 3. Check if hostname is blocked
        if is_blocked_hostname(hostname):
            return False, f"Access to '{hostname}' is not allowed (blocked hostname)."

        # 4. Check if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # If we get here, hostname is already an IP
            if is_private_ip(hostname):
                return False, f"Access to private IP address '{hostname}' is not allowed."
        except ValueError:
            # Hostname is not an IP, need to resolve it
            pass

        # 5. Resolve hostname and check resolved IP
        resolved_ip = resolve_hostname_safely(hostname)
        if resolved_ip is None:
            return False, f"Cannot resolve '{hostname}' or it resolves to a blocked IP address."

        # 6. Double-check resolved IP (DNS rebinding protection)
        if is_private_ip(resolved_ip):
            return False, f"Hostname '{hostname}' resolves to private IP '{resolved_ip}' which is not allowed."

        return True, ""

    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def validate_url_before_check(url: str) -> None:
    """
    Validate URL before performing a check. Raises exception if invalid.

    Args:
        url: The URL to validate

    Raises:
        ValueError: If URL is not safe for SSRF
    """
    is_valid, error_msg = validate_url_for_ssrf(url)
    if not is_valid:
        raise ValueError(f"SSRF Protection: {error_msg}")
