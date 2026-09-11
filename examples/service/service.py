"""A reference operation service: the remote transport's server side.

Serves the wire contract from docs/WIRE_CONTRACT.md with the standard library
only:

    GET  /operations                    -> { "operations": [ <manifest>, ... ] }
    POST /operations/{name}/plan        -> { plan }
    POST /operations/{name}/apply       -> { result }

Run it:

    PYTHONPATH=src python examples/service/service.py
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from domain_ops_agent import OperationContext, OperationRuntime  # noqa: E402
from examples.library_catalog.domain import seed  # noqa: E402
from examples.library_catalog.operations import build_runtime  # noqa: E402


def build_app() -> "tuple[OperationRuntime, OperationContext]":
    db = seed()
    runtime = build_runtime(db)
    ctx = OperationContext(services={"db": db})
    return runtime, ctx


class Handler(BaseHTTPRequestHandler):
    runtime: OperationRuntime
    ctx: OperationContext

    def log_message(self, *args) -> None:  # keep the demo output clean
        return None

    # -- helpers ---------------------------------------------------------

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length) or b"{}")

    # -- routes ----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/operations":
            return self._send(200, {"operations": self.runtime.registry.manifests()})
        return self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parts = [p for p in self.path.split("/") if p]
        if len(parts) == 3 and parts[0] == "operations" and parts[2] in ("plan", "apply"):
            name, action = parts[1], parts[2]
            body = self._body()
            if action == "plan":
                plan = self.runtime.plan(name, body.get("params", {}), body.get("version"), self.ctx)
                return self._send(200, plan.to_dict())
            result = self.runtime.apply(body["plan_id"], self.ctx)
            return self._send(200, result.to_dict())
        return self._send(404, {"error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 8765) -> HTTPServer:
    runtime, ctx = build_app()
    Handler.runtime = runtime
    Handler.ctx = ctx
    return HTTPServer((host, port), Handler)


if __name__ == "__main__":
    httpd = serve()
    host, port = httpd.server_address
    print(f"operation service on http://{host}:{port}")
    httpd.serve_forever()
