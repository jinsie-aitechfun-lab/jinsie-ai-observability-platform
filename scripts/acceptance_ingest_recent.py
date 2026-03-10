#!/usr/bin/env python3
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def http_json(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8")
            if not body.strip():
                return status, None
            try:
                return status, json.loads(body)
            except json.JSONDecodeError:
                return status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return e.code, parsed
    except urllib.error.URLError as e:
        raise RuntimeError(f"request failed: {e}") from e


def extract_recent_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    candidate_keys = [
        "items",
        "data",
        "results",
        "records",
        "recent",
        "metrics",
    ]
    for key in candidate_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Acceptance guardrail for ingest -> recent")
    parser.add_argument("--base-url", default="http://127.0.0.1:8003")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    request_id = f"acc-ingest-recent-{int(time.time() * 1000)}"

    ingest_url = f"{base_url}/metrics/ingest"
    recent_url = f"{base_url}/metrics/recent?limit=1"

    payload = {
        "request_id": request_id,
        "engine": "acceptance-engine",
        "status": "success",
        "total_ms": 123.4,
        "retrieval_ms": 12.3,
        "llm_ms": 111.1,
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
        "cost": 0.001,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    print("== CASE: ingest -> recent ==")
    print(f"  base_url: {base_url}")
    print(f"  request_id: {request_id}")

    try:
        ingest_status, ingest_body = http_json("POST", ingest_url, payload)
    except Exception as e:
        print(f"[FAIL] POST /metrics/ingest error: {e}")
        return 1

    print(f"  POST /metrics/ingest -> http_status: {ingest_status}")
    if ingest_status < 200 or ingest_status >= 300:
        print("[FAIL] ingest did not return 2xx")
        print(f"  response: {json.dumps(ingest_body, ensure_ascii=False, indent=2) if not isinstance(ingest_body, str) else ingest_body}")
        return 1

    try:
        recent_status, recent_body = http_json("GET", recent_url)
    except Exception as e:
        print(f"[FAIL] GET /metrics/recent error: {e}")
        return 1

    print(f"  GET /metrics/recent?limit=1 -> http_status: {recent_status}")
    if recent_status < 200 or recent_status >= 300:
        print("[FAIL] recent did not return 2xx")
        print(f"  response: {json.dumps(recent_body, ensure_ascii=False, indent=2) if not isinstance(recent_body, str) else recent_body}")
        return 1

    items = extract_recent_items(recent_body)
    if not items:
        print("[FAIL] recent response has no readable items")
        print(f"  response: {json.dumps(recent_body, ensure_ascii=False, indent=2) if not isinstance(recent_body, str) else recent_body}")
        return 1

    latest = items[0]
    latest_request_id = latest.get("request_id")
    print(f"  latest.request_id: {latest_request_id}")

    if latest_request_id != request_id:
        print("[FAIL] recent first item is not the just-ingested request_id")
        print(f"  expected: {request_id}")
        print(f"  actual:   {latest_request_id}")
        print(f"  response: {json.dumps(recent_body, ensure_ascii=False, indent=2) if not isinstance(recent_body, str) else recent_body}")
        return 1

    print("[PASS] ingest -> recent acceptance passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())