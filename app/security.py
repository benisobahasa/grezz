"""
Security helpers:
1. SSRF protection — the app fetches arbitrary user-supplied URLs, so before
   any request goes out we resolve the hostname and reject anything pointing
   at private/internal/loopback/link-local addresses. Without this, someone
   could point Grezz at http://localhost or http://169.254.169.254/ (cloud
   metadata endpoints) and use the server as an open proxy into its own
   network.
2. Simple in-memory sliding-window rate limiter per IP, to stop the
   Gemini/scraping quota from being drained by abuse (no external deps
   needed for a single-instance free-tier deployment).
"""
import ipaddress
import socket
import time
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048

BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost")


class UnsafeURLError(Exception):
    pass


def validate_and_resolve_url(url: str) -> str:
    """Raises UnsafeURLError if the URL is malformed or resolves to a
    private/loopback/link-local/reserved address. Returns the normalized URL."""
    if len(url) > MAX_URL_LENGTH:
        raise UnsafeURLError("URL is too long")

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError("Only http/https URLs are supported")
    if not parsed.hostname:
        raise UnsafeURLError("Invalid URL")

    hostname = parsed.hostname.lower()
    if hostname in ("localhost",) or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise UnsafeURLError("URLs pointing to internal hosts are not allowed")

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Could not resolve domain: {hostname}") from exc

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise UnsafeURLError("URL resolves to an internal/private network address")

    return url


class RateLimiter:
    """Sliding-window limiter: max `limit` calls per `window_seconds` per key."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str) -> bool:
        """Returns True if the call is allowed (and records it), False if rate-limited."""
        now = time.time()
        window_start = now - self.window_seconds
        hits = [t for t in self._hits.get(key, []) if t > window_start]
        if len(hits) >= self.limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


analyze_rate_limiter = RateLimiter(limit=10, window_seconds=60)
ask_rate_limiter = RateLimiter(limit=15, window_seconds=60)


def client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
