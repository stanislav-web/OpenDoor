#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deterministic local HTTP lab for the Mastering OpenDoor article series.

The fixture is intentionally small, local-only and safe to run on a developer
machine. It exposes a mixed set of routes that demonstrate common discovery
signals without requiring a third-party target.
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Final
from urllib.parse import urlsplit


HOST: Final = "127.0.0.1"
DEFAULT_PORT: Final = 8080


class Route:
    """Static route definition used by the local lab server."""

    def __init__(
        self,
        status: int,
        body: str | bytes,
        content_type: str = "text/plain; charset=utf-8",
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Create a route response.

        :param status: HTTP status code returned by the route.
        :param body: Response body as text or bytes.
        :param content_type: Response Content-Type header.
        :param headers: Optional extra response headers.
        :return: None.
        """
        self.status = status
        self.body = body
        self.content_type = content_type
        self.headers = headers or {}

    def body_bytes(self) -> bytes:
        """
        Return the route body encoded as bytes.

        :return: Response body bytes.
        """
        if isinstance(self.body, bytes):
            return self.body

        return self.body.encode("utf-8")


ROUTES: Final[dict[str, Route]] = {
    "/": Route(
        HTTPStatus.OK,
        """<!doctype html>
<html>
  <head><title>OpenDoor Mastering Lab</title></head>
  <body>
    <h1>OpenDoor Mastering Lab</h1>
    <a href="/admin">Admin</a>
    <a href="/login">Login</a>
    <a href="/api/users">API users</a>
    <a href="/uploads/">Uploads</a>
  </body>
</html>
""",
        "text/html; charset=utf-8",
        {"X-Lab": "opendoor-mastering"},
    ),
    "/admin": Route(
        HTTPStatus.OK,
        """<!doctype html>
<html>
  <head><title>Demo Admin Panel</title></head>
  <body>
    <h1>Demo Admin Panel</h1>
    <form action="/login" method="post">
      <input name="username" autocomplete="off">
      <input name="password" type="password">
      <button type="submit">Sign in</button>
    </form>
  </body>
</html>
""",
        "text/html; charset=utf-8",
    ),
    "/login": Route(
        HTTPStatus.OK,
        """<!doctype html>
<html>
  <head><title>Demo Login</title></head>
  <body><h1>Demo Login</h1><p>This is a local training fixture.</p></body>
</html>
""",
        "text/html; charset=utf-8",
        {"Set-Cookie": "opendoor_demo_session=placeholder; Path=/; HttpOnly"},
    ),
    "/api/users": Route(
        HTTPStatus.OK,
        json.dumps(
            {
                "users": [
                    {"id": 1, "role": "admin", "name": "Alice"},
                    {"id": 2, "role": "analyst", "name": "Bob"},
                ]
            },
            indent=2,
        ),
        "application/json; charset=utf-8",
    ),
    "/uploads/": Route(
        HTTPStatus.OK,
        """<!doctype html>
<html>
  <head><title>Index of /uploads/</title></head>
  <body>
    <h1>Index of /uploads/</h1>
    <a href="report.pdf">report.pdf</a>
    <a href="avatar.png">avatar.png</a>
  </body>
</html>
""",
        "text/html; charset=utf-8",
    ),
    "/backup.zip": Route(
        HTTPStatus.OK,
        b"PK\x03\x04\x14\x00opendoor-demo-backup-placeholder\n",
        "application/zip",
        {"Content-Disposition": "attachment; filename=backup.zip"},
    ),
    "/.git/HEAD": Route(
        HTTPStatus.OK,
        "ref: refs/heads/main\n",
        "text/plain; charset=utf-8",
    ),
    "/.env": Route(
        HTTPStatus.OK,
        "APP_ENV=demo\nOPENDOOR_PLACEHOLDER_TOKEN=replace-me\nDATABASE_URL=sqlite:///demo.db\n",
        "text/plain; charset=utf-8",
    ),
    "/forbidden": Route(
        HTTPStatus.FORBIDDEN,
        "Forbidden\n",
        "text/plain; charset=utf-8",
    ),
    "/auth-required": Route(
        HTTPStatus.UNAUTHORIZED,
        "Unauthorized\n",
        "text/plain; charset=utf-8",
        {"WWW-Authenticate": "Basic realm=OpenDoor Demo"},
    ),
    "/redirect": Route(
        HTTPStatus.MOVED_PERMANENTLY,
        "Moved\n",
        "text/plain; charset=utf-8",
        {"Location": "/login"},
    ),
    "/server-error": Route(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        """Traceback (most recent call last):
  File \"/srv/app/demo.py\", line 42, in handler
    raise RuntimeError(\"OpenDoor demo stack trace\")
RuntimeError: OpenDoor demo stack trace
""",
        "text/plain; charset=utf-8",
    ),
}


class MasteringLabHandler(BaseHTTPRequestHandler):
    """HTTP handler for deterministic OpenDoor training routes."""

    def do_HEAD(self) -> None:
        """
        Serve a deterministic HEAD response.

        :return: None.
        """
        self._respond(with_body=False)

    def do_GET(self) -> None:
        """
        Serve a deterministic GET response.

        :return: None.
        """
        self._respond(with_body=True)

    def _respond(self, with_body: bool) -> None:
        """
        Send a response for the requested path.

        :param with_body: Whether the response body should be written.
        :return: None.
        """
        path = urlsplit(self.path).path
        route = ROUTES.get(path, Route(HTTPStatus.NOT_FOUND, "Not Found\n"))
        body = route.body_bytes()

        self.send_response(route.status)
        self.send_header("Content-Type", route.content_type)
        self.send_header("Content-Length", str(len(body)))

        for name, value in route.headers.items():
            self.send_header(name, value)

        self.end_headers()

        if with_body:
            self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        """
        Silence per-request access logs to keep article screenshots clean.

        :param fmt: BaseHTTPRequestHandler format string.
        :param args: Format arguments.
        :return: None.
        """
        return


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the local lab server.

    :return: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run the OpenDoor Mastering local lab server.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Local TCP port to listen on.")
    return parser.parse_args()


def main() -> int:
    """
    Start the local-only HTTP lab server.

    :return: Process exit code.
    """
    args = parse_args()
    server = HTTPServer((HOST, args.port), MasteringLabHandler)
    print(f"OpenDoor Mastering lab listening on http://{HOST}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
