"""Drive the operation service through the remote transport.

    PYTHONPATH=src python examples/service/remote_demo.py
"""
from __future__ import annotations

import os
import sys
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from domain_ops_agent import RemoteOperationClient  # noqa: E402
from examples.service.service import serve  # noqa: E402


def main() -> None:
    httpd = serve(port=0)  # ephemeral port
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        client = RemoteOperationClient(f"http://{host}:{port}")
        print("manifests:", [m["name"] for m in client.manifests()])

        plan = client.plan("rename_author", {"author_id": "a1", "new_name": "Ada King"})
        print("plan diff:", plan["diff"])

        result = client.apply(plan)
        print("apply:", result["status"], "| verified:", result["verification"]["ok"])
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
