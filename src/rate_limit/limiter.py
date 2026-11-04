"""The SLIDING WINDOW algorithm (plain Python: the clock is given from outside, so it is easy to test).
 
For every key (an IP address + a rule group) we remember the times of its recent requests.
A new request is allowed only if fewer than <limit> requests happened in the last <window> seconds.
Old times fall out of the window by themselves, so there is no "reset at the end of the minute"
(a fixed window would allow a burst right before and right after the reset).
"""
import math
import threading
from collections import deque
from dataclasses import dataclass
 
 
@dataclass(frozen=True)
class Result:
    allowed: bool
    limit: int
    remaining: int       # how many more requests are allowed right now
    retry_after: int     # seconds until the next request is allowed (0 when allowed)
 
 
class SlidingWindowLimiter:
    """The counters live in the server's memory (no extra software needed).
    They start from zero when the server restarts. With several server processes each one has
    its own counters (a shared store such as Redis would be used in a big production system)."""
 
    CLEAN_EVERY = 1000          # remove the counters of IPs that went away, once per this many requests
 
    def __init__(self):
        self._hits = {}         # key -> (deque of request times, window in seconds)
        self._lock = threading.Lock()
        self._calls = 0
 
    def hit(self, key: str, limit: int, window: int, now: float) -> Result:
        with self._lock:
            self._calls += 1
            if self._calls % self.CLEAN_EVERY == 0:
                self._clean(now)
 
            times, _ = self._hits.setdefault(key, (deque(), window))
 
            # forget the requests that are older than the window
            while times and times[0] <= now - window:
                times.popleft()
 
            if len(times) >= limit:
                retry_after = max(1, math.ceil(times[0] + window - now))
                return Result(False, limit, 0, retry_after)
 
            times.append(now)                   # only allowed requests are counted
            return Result(True, limit, limit - len(times), 0)
 
    def _clean(self, now: float):
        for key in list(self._hits):
            times, window = self._hits[key]
            while times and times[0] <= now - window:
                times.popleft()
            if not times:
                del self._hits[key]
 
    def size(self) -> int:
        return len(self._hits)
 
 
def client_ip(scope: dict, trust_proxy: bool = False) -> str:
    """Who is making the request.
 
    Normally this is the address of the connection. Behind a proxy (Nginx, Cloudflare) every request would
    look like it comes from the proxy, so the real address is read from the X-Forwarded-For header, but ONLY
    when trust_proxy is on: otherwise anybody could write any IP in that header and escape the limit."""
    if trust_proxy:
        for name, value in scope.get("headers", []):
            if name == b"x-forwarded-for":
                first = value.decode("latin-1").split(",")[0].strip()
                if first:
                    return first[:45]
 
    client = scope.get("client")
    if client and client[0]:
        return str(client[0])
    return "unknown"
 