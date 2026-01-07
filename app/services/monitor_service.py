import httpx
import socket
import ssl
import json
import subprocess
from datetime import datetime, timedelta
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.models.monitor import Monitor
from app.models.check import Check


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
        async with httpx.AsyncClient(timeout=monitor.timeout, follow_redirects=True) as client:
            response = await client.get(monitor.url)
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000

            # Extract metadata
            ip_address = None
            ssl_expires_at = None

            # Get IP address
            try:
                parsed_url = urlparse(monitor.url)
                hostname = parsed_url.hostname
                if hostname:
                    ip_address = get_ip_address(hostname)
            except Exception as e:
                print(f"Error getting IP for {monitor.url}: {e}")

            # Get SSL certificate expiry for HTTPS
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
                                # Parse expiry date
                                expiry_str = cert.get('notAfter')
                                if expiry_str:
                                    ssl_expires_at = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                except Exception as e:
                    print(f"Error getting SSL info for {monitor.url}: {e}")

            # Extract headers
            headers_dict = {}
            for key in ['server', 'content-type', 'x-powered-by', 'cache-control', 'content-length']:
                if key in response.headers:
                    headers_dict[key] = response.headers[key]

            check = Check(
                monitor_id=monitor.id,
                status="up" if response.status_code < 400 else "down",
                status_code=response.status_code,
                response_time=response_time,
                checked_at=datetime.utcnow(),
                ip_address=ip_address,
                server=response.headers.get('server'),
                content_type=response.headers.get('content-type'),
                ssl_expires_at=ssl_expires_at,
                response_headers=json.dumps(headers_dict) if headers_dict else None
            )
    except httpx.TimeoutException:
        check = Check(
            monitor_id=monitor.id,
            status="down",
            error_message="Request timeout",
            checked_at=datetime.utcnow()
        )
    except Exception as e:
        check = Check(
            monitor_id=monitor.id,
            status="down",
            error_message=str(e)[:500],
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
