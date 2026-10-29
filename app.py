"""Backend for the local student page.

Serves frontend/index.html. Student data comes from model.py.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import model

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "index.html"
HOST = "127.0.0.1"
PORT = 8000


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", FRONTEND.read_bytes())
            return
        if path == "/api/students":
            body = json.dumps(model.list_students()).encode()
            self._send(200, "application/json; charset=utf-8", body)
            return
        if path == "/api/competencies":
            body = json.dumps(model.average_competencies()).encode()
            self._send(200, "application/json; charset=utf-8", body)
            return
        self.send_error(404)

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}")
    server.serve_forever()
