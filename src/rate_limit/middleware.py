"""The rate limit middleware: the guard at the main gate of the building.
 
Every request goes through here BEFORE the routers and BEFORE deps.py (login / role checks).
It has to be before them, because login and signup have no token, so deps.py never runs there.
"""
import time
 
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
 
from src.rate_limit.limiter import SlidingWindowLimiter, client_ip
from src.rate_limit.rules import find_rule
from src.utils.settings import settings
 
# One limiter (one set of counters) for the whole server
limiter = SlidingWindowLimiter()
 
 
class RateLimitMiddleware:
    """A plain ASGI middleware (it does not wrap the response body, so BackgroundTasks keep working)."""
 
    def __init__(self, app):
        self.app = app
        self.enabled = bool(getattr(settings, "RATE_LIMIT_ENABLED", True))
        self.trust_proxy = bool(getattr(settings, "RATE_LIMIT_TRUST_PROXY", False))
 
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return
 
        rule = find_rule(scope["method"], scope["path"])
        if rule is None:                                   # pages, static files, /docs ... are not limited
            await self.app(scope, receive, send)
            return
 
        ip = client_ip(scope, self.trust_proxy)
        result = limiter.hit(f"{ip}|{rule.name}", rule.limit, rule.window, time.monotonic())
 
        if not result.allowed:
            print(f"[rate-limit] blocked {ip} on '{rule.name}' ({scope['method']} {scope['path']}), retry in {result.retry_after}s")
            response = JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Please try again in {result.retry_after} seconds."},
                headers={
                    "Retry-After": str(result.retry_after),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )
            await response(scope, receive, send)
            return
 
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-RateLimit-Limit"] = str(result.limit)
                headers["X-RateLimit-Remaining"] = str(result.remaining)
            await send(message)
 
        await self.app(scope, receive, send_with_headers)
 