"""Local web server for the three.js GUI. Standard library only.

Run from the repository root:

    python -m web.server            # then open http://127.0.0.1:8000
    python -m web.server --port 9000 --no-browser
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import threading
import traceback
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from web import api

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 64 * 1024

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


class Handler(BaseHTTPRequestHandler):
    server_version = "BloxorzWeb/1.0"

    # ---------- routing ----------

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/levels":
            self._json(api.list_levels())
        elif path.startswith("/api/levels/"):
            self._call(api.level_payload, unquote(path.removeprefix("/api/levels/")))
        elif path == "/api/options":
            self._json(api.options())
        elif path.startswith("/api/"):
            self._error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        else:
            self._static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._read_json()
        if body is None:
            return
        if path == "/api/step":
            self._call(api.step, body.get("level"), body.get("state"), body.get("action"))
        elif path == "/api/solve":
            self._call(api.solve, body.get("level"), body.get("solver"), body.get("cost"), body.get("heuristic"))
        else:
            self._error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    # ---------- helpers ----------

    def _call(self, fn, *args) -> None:
        try:
            self._json(fn(*args))
        except api.ApiError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception:  # keep the server alive, show the traceback in the terminal
            traceback.print_exc()
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "Server error, see the terminal for details")

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request body too large")
            return None
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._error(HTTPStatus.BAD_REQUEST, "Body must be JSON")
            return None
        if not isinstance(data, dict):
            self._error(HTTPStatus.BAD_REQUEST, "Body must be a JSON object")
            return None
        return data

    def _json(self, payload, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json({"error": message}, status)

    def _static(self, path: str) -> None:
        relative = unquote(path).lstrip("/") or "index.html"
        file = (STATIC_DIR / relative).resolve()
        if not file.is_relative_to(STATIC_DIR) or not file.is_file():
            self._error(HTTPStatus.NOT_FOUND, "Not found")
            return
        data = file.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")  # always serve the latest files while developing
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        if "/api/" in self.path and not self.path.startswith("/api/step"):
            sys.stderr.write(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bloxorz web GUI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Bloxorz web GUI running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
