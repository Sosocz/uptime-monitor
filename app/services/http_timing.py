import asyncio
import ssl
import time
from urllib.parse import urlparse

import aiohttp


class TimingContext:
    def __init__(self):
        self.start = asyncio.get_event_loop().time()
        self.dns_start = None
        self.dns_end = None
        self.conn_start = None
        self.conn_end = None
        self.request_start = None
        self.response_start = None
        self.response_end = None

    def duration(self, start, end) -> float | None:
        if start is None or end is None:
            return None
        return (end - start) * 1000

    def get_timings(self) -> dict:
        return {
            "name_lookup_ms": self.duration(self.dns_start, self.dns_end),
            "connection_ms": self.duration(self.conn_start, self.conn_end),
            "tls_ms": self.duration(self.conn_start, self.conn_end),
            "transfer_ms": self.duration(self.response_start, self.response_end),
            "total_ms": self.duration(self.dns_start or self.start, self.response_end),
        }


async def timed_request(url: str, timeout: float):
    timings = TimingContext()
    trace_config = aiohttp.TraceConfig()

    @trace_config.on_dns_resolvehost_start
    async def on_dns_start(session, context, params):
        timings.dns_start = asyncio.get_event_loop().time()

    @trace_config.on_dns_resolvehost_end
    async def on_dns_end(session, context, params):
        timings.dns_end = asyncio.get_event_loop().time()

    @trace_config.on_connection_create_start
    async def on_conn_start(session, context, params):
        timings.conn_start = asyncio.get_event_loop().time()

    @trace_config.on_connection_create_end
    async def on_conn_end(session, context, params):
        timings.conn_end = asyncio.get_event_loop().time()

    @trace_config.on_request_start
    async def on_request_start(session, context, params):
        timings.request_start = asyncio.get_event_loop().time()

    @trace_config.on_response_chunk_received
    async def on_response_chunk(session, context, chunk):
        now = asyncio.get_event_loop().time()
        if timings.response_start is None:
            timings.response_start = now
        timings.response_end = now

    @trace_config.on_request_end
    async def on_request_end(session, context, params):
        timings.response_end = timings.response_end or asyncio.get_event_loop().time()

    parsed = urlparse(url)
    ssl_context = None
    if parsed.scheme == "https":
        ssl_context = ssl.create_default_context()

    connector = aiohttp.TCPConnector(force_close=True, limit=4)

    async with aiohttp.ClientSession(
        trace_configs=[trace_config],
        connector=connector
    ) as session:
        try:
            async with session.get(url, timeout=timeout, ssl=ssl_context) as response:
                await response.read()
                data = await response.text()
                return {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": data,
                    "timings": timings.get_timings(),
                }
        except asyncio.TimeoutError as exc:
            return {"error": "timeout", "exception": exc, "timings": timings.get_timings()}
        except Exception as exc:
            return {"error": str(exc), "exception": exc, "timings": timings.get_timings()}
