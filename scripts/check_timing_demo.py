import asyncio

from app.services.http_timing import timed_request


async def demonstrate(urls, count=5):
    print("URL | Total(ms) | DNS(ms) | Conn(ms) | TLS(ms) | Transfer(ms)")
    print("-" * 65)
    for url in urls:
        for _ in range(count):
            result = await timed_request(url, timeout=10)
            timings = result.get("timings") or {}
            print(
                f"{url:30.30} | "
                f"{(timings.get('total_ms') or 0):7.1f} | "
                f"{(timings.get('name_lookup_ms') or 0):7.1f} | "
                f"{(timings.get('connection_ms') or 0):7.1f} | "
                f"{(timings.get('tls_ms') or 0):7.1f} | "
                f"{(timings.get('transfer_ms') or 0):7.1f}"
            )
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    urls = ["https://www.trezapp.fr/", "https://chatgpt.com/"]
    asyncio.run(demonstrate(urls))
