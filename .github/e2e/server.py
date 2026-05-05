"""
GitHub Actions E2E HTTP server for OpenDoor.

The server exposes deterministic routes so the workflow can verify
OpenDoor CLI scan behavior, JSON reporting and SARIF reporting.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


ROUTES: dict[str, tuple[int, str]] = {
    "/admin": (200, "Admin panel"),
    "/backup": (200, "Backup index"),
    "/health": (200, "Health OK"),
    "/uploads": (200, "Uploads directory"),
    "/login": (200, "Login page"),
    "/forbidden": (403, "Forbidden"),
    "/auth-required": (401, "Unauthorized"),
    "/redirect": (301, "Moved"),
}


class Handler(BaseHTTPRequestHandler):
    """Deterministic request handler for OpenDoor E2E."""

    def do_HEAD(self) -> None:
        self._respond(with_body=False)

    def do_GET(self) -> None:
        self._respond(with_body=True)

    def _respond(self, with_body: bool = False) -> None:
        path = self.path.split("?")[0]
        status, body = ROUTES.get(path, (404, "Not Found"))

        self.send_response(status)
        self.send_header("Content-Type", "text/plain")

        if status == 301:
            self.send_header("Location", "https://example.com/")

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if with_body:
            self.wfile.write(body.encode("utf-8"))

    def log_message(self, fmt: str, *args: object) -> None:
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8088), Handler)
    print("E2E server listening on http://127.0.0.1:8088", flush=True)
    server.serve_forever()