from __future__ import annotations

import json
from typing import Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os

from .agents import run_pipeline, DEEPAGENTS_AVAILABLE

HOST = os.environ.get("NPC_HOST", "127.0.0.1")
PORT = int(os.environ.get("NPC_PORT", "8089"))

# Basic structured logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')


class Handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):  # noqa: N802
        if self.path != "/npc":
            self.send_response(404)
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Not Found")
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
        except Exception:
            self.send_response(400)
            self._set_cors()
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return
        try:
            result = run_pipeline(data)
            out = json.dumps(result).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors()
            self.end_headers()
            self.wfile.write(out)
        except Exception as e:  # pragma: no cover
            self.send_response(500)
            self._set_cors()
            self.end_headers()
            msg = {"error": str(e)}
            self.wfile.write(json.dumps(msg).encode('utf-8'))


def run_server():
    mode = "DEEP AGENTS" if DEEPAGENTS_AVAILABLE else "FALLBACK"
    print(f"NPC backend listening on http://{HOST}:{PORT}/npc | Mode: {mode}")
    with HTTPServer((HOST, PORT), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
