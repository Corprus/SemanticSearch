from __future__ import annotations

from typing import Callable, Awaitable

ASGIApp = Callable[[dict, Callable, Callable], Awaitable[None]]


class ForwardedPrefixMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers") or [])
            prefix = headers.get(b"x-forwarded-prefix")
            if prefix:
                scope["root_path"] = prefix.decode("utf-8").rstrip("/")
        await self.app(scope, receive, send)
