"""Dependency-free local server for the WebXR HapticSight observer."""
from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Type

from .state import XRState


class XRStateStore:
    def __init__(self, initial: XRState | None = None) -> None:
        self._state = initial
        self._lock = Lock()

    def set(self, state: XRState) -> None:
        with self._lock:
            self._state = state

    def get(self) -> XRState | None:
        with self._lock:
            return self._state


def make_handler(web_root: str | Path, store: XRStateStore) -> Type[SimpleHTTPRequestHandler]:
    root = str(Path(web_root).resolve())

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def do_GET(self):  # noqa: N802
            if self.path == "/state.json":
                state = store.get()
                body = json.dumps({} if state is None else state.to_dict(), sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def log_message(self, format, *args):  # noqa: A002
            return

    return Handler


def serve(web_root: str | Path, store: XRStateStore, *, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, int(port)), make_handler(web_root, store))
    return server
