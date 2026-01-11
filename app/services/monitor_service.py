import json
import subprocess
import ssl
from datetime import datetime, timedelta
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.security_ssrf import validate_url_before_check
from app.models.check import Check
from app.models.monitor import Monitor
from app.services.http_timing import timed_request


def get_ip_address(hostname: str) -> str:
    """Get IP address using multiple methods."""
    # Try with getent first (works well in containers)
    try:
        result = subprocess.run(
            ['getent', 'hosts', hostname],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            ip = result.stdout.split()[0]
            if ip:
                return ip
    except Exception:
        pass

    # Try with socket
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        pass

    # Try with nslookup as fallback
    try:
        result = subprocess.run(
            ['nslookup', hostname],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.split('\n'):
                if 'Address:' in line and '#' not in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        if ip and not ip.startswith('127.'):
                            return ip
    except Exception:
        pass

    return None


async def perform_check(db: Session, monitor: Monitor) -> Check:
    """Perform an HTTP check on a monitor and record the result."""
    start_time = datetime.utcnow()

    try:
        validate_url_before_check(monitor.url)
        timing_result = await timed_request(monitor.url, timeout=monitor.timeout)
        timings = timing_result.get("timings", {})
        error = timing_result.get("error")
        status_code = timing_result.get("status_code") or 0
        response_time = timings.get("total_ms") or 0
        acceptable_error_codes = [400, 401, 403, 429]
        is_up = (status_code < 400 and status_code > 0) or (status_code in acceptable_error_codes)

        ip_address = None
        ssl_expires_at = None

        try:
            parsed_url = urlparse(monitor.url)
            hostname = parsed_url.hostname
            if hostname:
                ip_address = get_ip_address(hostname)
        except Exception as e:
            print(f"Error getting IP for {monitor.url}: {e}")

        if monitor.url.startswith('https://'):
            try:
                parsed_url = urlparse(monitor.url)
                hostname = parsed_url.hostname
                port = parsed_url.port or 443
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        if cert:
                            expiry_str = cert.get('notAfter')
                            if expiry_str:
                                ssl_expires_at = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
            except Exception as e:
                print(f"Error getting SSL info for {monitor.url}: {e}")

        headers_dict = timing_result.get("headers", {})

        check = Check(
            monitor_id=monitor.id,
            status="up" if is_up and not error else "down",
            status_code=status_code or None,
            response_time=response_time,
            name_lookup_ms=timings.get("name_lookup_ms"),
            connection_ms=timings.get("connection_ms"),
            tls_ms=timings.get("tls_ms"),
            transfer_ms=timings.get("transfer_ms"),
            total_ms=timings.get("total_ms"),
            checked_at=datetime.utcnow(),
            ip_address=ip_address,
            server=headers_dict.get('server'),
            content_type=headers_dict.get('content-type'),
            ssl_expires_at=ssl_expires_at,
            response_headers=json.dumps(headers_dict) if headers_dict else None,
            error_message=error
        )
    except Exception as e:
        check = Check(
            monitor_id=monitor.id,
            status="down",
            error_message=str(e)[:500],
            name_lookup_ms=None,
            connection_ms=None,
            tls_ms=None,
            transfer_ms=None,
            total_ms=None,
            checked_at=datetime.utcnow()
        )

    db.add(check)
    db.commit()
    db.refresh(check)

    # Update monitor's last status
    monitor.last_status = check.status
    monitor.last_checked_at = check.checked_at
    db.commit()

    return check
