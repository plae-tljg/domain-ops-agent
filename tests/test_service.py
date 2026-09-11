import threading

from domain_ops_agent import RemoteOperationClient
from examples.service.service import serve


def _client():
    httpd = serve(port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, RemoteOperationClient(f"http://{host}:{port}")


def test_service_exposes_manifests_and_lifecycle():
    httpd, client = _client()
    try:
        names = {m["name"] for m in client.manifests()}
        assert {"rename_author", "merge_authors", "delete_book"} <= names

        plan = client.plan("rename_author", {"author_id": "a1", "new_name": "Ada King"})
        assert plan["operation"] == "rename_author"
        assert plan["diff"]["after"]["author"]["name"] == "Ada King"

        result = client.apply(plan)
        assert result["status"] == "done"
        assert result["verification"]["ok"] is True
        assert result["revert_token"]
    finally:
        httpd.shutdown()


def test_service_revert_endpoint():
    httpd, client = _client()
    try:
        plan = client.plan("delete_book", {"book_id": "b1"})
        result = client.apply(plan)
        status, body = _post(f"http://{httpd.server_address[0]}:{httpd.server_address[1]}/revert",
                             {"token": result["revert_token"]})
        assert status == 200
        assert body["status"] == "reverted"
    finally:
        httpd.shutdown()


def _post(url, body):
    import json
    from urllib import request

    data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))
