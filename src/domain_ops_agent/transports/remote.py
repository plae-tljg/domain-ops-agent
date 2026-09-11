"""Remote transport — operations live behind an HTTP service.

The service publishes the manifest set at ``GET /operations`` and executes
``POST /operations/{name}/plan`` and ``POST /operations/{name}/apply``.
See docs/WIRE_CONTRACT.md.

The HTTP call is injectable so the client is testable without a network:

    def http(method: str, url: str, body: dict | None) -> tuple[int, dict]
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional
from urllib import request as _urllib_request

HttpFn = Callable[[str, str, Optional[dict]], "tuple[int, dict]"]


def _default_http(method: str, url: str, body: Optional[dict]) -> "tuple[int, dict]":
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = _urllib_request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with _urllib_request.urlopen(req) as resp:
        payload = resp.read().decode("utf-8")
        return resp.status, (json.loads(payload) if payload else {})


class RemoteOperationClient:
    def __init__(self, base_url: str, http: Optional[HttpFn] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = http or _default_http

    def manifests(self) -> List[Dict[str, Any]]:
        _status, body = self._http("GET", f"{self.base_url}/operations", None)
        return body.get("operations", [])

    def plan(self, name: str, params: dict, version: Optional[int] = None) -> Dict[str, Any]:
        _status, body = self._http(
            "POST",
            f"{self.base_url}/operations/{name}/plan",
            {"params": params, "version": version},
        )
        return body

    def apply(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an approved plan dict (as returned by :meth:`plan`)."""
        name = plan["operation"]
        _status, body = self._http(
            "POST",
            f"{self.base_url}/operations/{name}/apply",
            {
                "plan_id": plan.get("plan_id"),
                "params": plan.get("params", {}),
                "version": plan.get("version"),
            },
        )
        return body
