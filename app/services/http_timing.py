import asyncio
import subprocess
from urllib.parse import urlparse


MAX_DOWNLOAD_BYTES = 1024 * 1024


def _parse_headers(header_text: str) -> dict:
    if not header_text:
        return {}

    normalized = header_text.replace("\r\n", "\n")
    blocks = [block for block in normalized.split("\n\n") if block.strip()]
    if not blocks:
        return {}

    last_block = blocks[-1]
    lines = last_block.split("\n")
    headers = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _seconds_to_ms(seconds: str | None) -> float | None:
    if seconds is None:
        return None
    try:
        value = float(seconds)
    except ValueError:
        return None
    if value < 0:
        return None
    return value * 1000


def _compute_breakdowns(
    name_lookup_ms: float | None,
    connect_ms: float | None,
    appconnect_ms: float | None,
    starttransfer_ms: float | None,
    total_ms: float | None,
    is_https: bool,
) -> dict:
    connection_ms = None
    tls_ms = None
    transfer_ms = None

    if name_lookup_ms is not None and connect_ms is not None and connect_ms >= name_lookup_ms:
        connection_ms = connect_ms - name_lookup_ms
    if is_https and connect_ms is not None and appconnect_ms is not None and appconnect_ms >= connect_ms:
        tls_ms = appconnect_ms - connect_ms
    if starttransfer_ms is not None and total_ms is not None and total_ms >= starttransfer_ms:
        transfer_ms = total_ms - starttransfer_ms

    return {
        "name_lookup_ms": name_lookup_ms,
        "connection_ms": connection_ms,
        "tls_ms": tls_ms,
        "transfer_ms": transfer_ms,
        "total_ms": total_ms,
    }


def _run_curl_request(url: str, timeout: float) -> dict:
    parsed_url = urlparse(url)
    is_https = parsed_url.scheme.lower() == "https"
    write_out = "CURL_TIMINGS:%{http_code}|%{time_namelookup}|%{time_connect}|%{time_appconnect}|%{time_starttransfer}|%{time_total}\\n"
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--location",
        "--max-redirs", "5",
        "--proto", "=http,https",
        "--proto-redir", "=http,https",
        "--max-time", str(timeout),
        "--connect-timeout", str(timeout),
        "--max-filesize", str(MAX_DOWNLOAD_BYTES),
        "--dump-header", "-",
        "--output", "/dev/null",
        "--write-out", write_out,
        url,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=max(timeout + 5, 10),
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    timings_line = None
    header_text = stdout
    for line in stdout.splitlines():
        if line.startswith("CURL_TIMINGS:"):
            timings_line = line
            break

    if timings_line:
        header_text = stdout.split(timings_line, 1)[0]

    headers = _parse_headers(header_text)

    status_code = None
    timings = {
        "name_lookup_ms": None,
        "connection_ms": None,
        "tls_ms": None,
        "transfer_ms": None,
        "total_ms": None,
    }
    breakdown_unavailable = True

    if timings_line:
        parts = timings_line.replace("CURL_TIMINGS:", "", 1).split("|")
        if len(parts) >= 6:
            http_code = parts[0]
            try:
                status_code = int(http_code)
            except ValueError:
                status_code = None

            name_lookup_ms = _seconds_to_ms(parts[1])
            connect_ms = _seconds_to_ms(parts[2])
            appconnect_ms = _seconds_to_ms(parts[3])
            starttransfer_ms = _seconds_to_ms(parts[4])
            total_ms = _seconds_to_ms(parts[5])
            required_missing = (
                name_lookup_ms is None
                or connect_ms is None
                or starttransfer_ms is None
                or total_ms is None
            )
            tls_missing = is_https and (
                appconnect_ms is None
                or (connect_ms is not None and appconnect_ms < connect_ms)
            )
            timings = _compute_breakdowns(
                name_lookup_ms,
                connect_ms,
                appconnect_ms,
                starttransfer_ms,
                total_ms,
                is_https,
            )
            breakdown_unavailable = required_missing or tls_missing

    error = None
    if result.returncode != 0:
        error = stderr.strip() or "curl_error"
    elif status_code == 0:
        error = "no_response"

    if error:
        timings = {
            "name_lookup_ms": None,
            "connection_ms": None,
            "tls_ms": None,
            "transfer_ms": None,
            "total_ms": None,
        }
        breakdown_unavailable = True

    return {
        "status_code": status_code or 0,
        "headers": headers,
        "timings": timings,
        "breakdown_unavailable": breakdown_unavailable,
        "error": error,
    }


async def timed_request(url: str, timeout: float) -> dict:
    return await asyncio.to_thread(_run_curl_request, url, timeout)
