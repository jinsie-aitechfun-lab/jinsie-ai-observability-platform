import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "docs" / "samples"


def print_section(title: str) -> None:
    print()
    print(f"== {title} ==")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"[OK] {message}")


def request_json(method: str, url: str, payload: Any | None = None) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            status = resp.getcode()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"http_status: {exc.code}")
        print(body)
        fail(f"{method} {url} returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"{method} {url} failed: {exc}")

    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        print(body)
        fail(f"{method} {url} did not return valid JSON")


def assert_dict_has_keys(obj: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        fail(f"{label} missing keys: {', '.join(missing)}")
    ok(f"{label} contains required keys")


def assert_number(value: Any, label: str) -> None:
    if not isinstance(value, (int, float)):
        fail(f"{label} is not numeric: {value!r}")
    ok(f"{label} is numeric")


def load_sample(filename: str) -> Any:
    path = SAMPLES_DIR / filename
    if not path.exists():
        fail(f"sample file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_health(base_url: str) -> None:
    print_section("CASE: /health")
    status, body = request_json("GET", f"{base_url}/health")
    print(f"http_status: {status}")

    if status != 200:
        fail("/health did not return 200")

    if not isinstance(body, dict):
        fail("/health response is not an object")

    if body.get("status") != "ok":
        fail("/health response status is not 'ok'")

    ok("/health is healthy")


def check_ingest(base_url: str) -> None:
    print_section("CASE: /metrics/ingest [batch]")
    payload = load_sample("ingest_batch.json")
    status, body = request_json("POST", f"{base_url}/metrics/ingest", payload)
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/ingest did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/ingest response is not an object")

    if "ingested_count" not in body:
        fail("/metrics/ingest response missing ingested_count")

    ingested_count = body["ingested_count"]
    print(f"ingested_count: {ingested_count}")

    if not isinstance(ingested_count, int):
        fail("ingested_count is not int")

    if ingested_count < 1:
        fail("ingested_count < 1")

    ok("/metrics/ingest accepted sample payload")


def check_recent(base_url: str) -> None:
    print_section("CASE: /metrics/recent")
    status, body = request_json("GET", f"{base_url}/metrics/recent")
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/recent did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/recent response is not an object")

    if "recent" not in body:
        fail("/metrics/recent response missing recent")

    recent = body["recent"]
    if not isinstance(recent, list):
        fail("/metrics/recent 'recent' is not a list")

    if len(recent) == 0:
        fail("/metrics/recent returned empty list")

    first = recent[0]
    if not isinstance(first, dict):
        fail("/metrics/recent first item is not an object")

    required_keys = [
        "request_id",
        "engine",
        "status",
        "timestamp",
        "total_ms",
        "llm_ms",
        "retrieval_ms",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost",
    ]
    assert_dict_has_keys(first, required_keys, "recent[0]")

    print("recent[0]:")
    print(json.dumps(first, ensure_ascii=False, indent=2))

    assert_number(first["total_ms"], "recent[0].total_ms")
    assert_number(first["llm_ms"], "recent[0].llm_ms")
    assert_number(first["retrieval_ms"], "recent[0].retrieval_ms")
    assert_number(first["prompt_tokens"], "recent[0].prompt_tokens")
    assert_number(first["completion_tokens"], "recent[0].completion_tokens")
    assert_number(first["total_tokens"], "recent[0].total_tokens")
    assert_number(first["cost"], "recent[0].cost")


def check_cost(base_url: str) -> None:
    print_section("CASE: /metrics/cost")
    status, body = request_json("GET", f"{base_url}/metrics/cost")
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/cost did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/cost response is not an object")

    if "cost" not in body:
        fail("/metrics/cost response missing cost")

    cost = body["cost"]
    if not isinstance(cost, dict):
        fail("/metrics/cost.cost is not an object")

    required_keys = [
        "total_requests",
        "total_prompt_tokens",
        "total_completion_tokens",
        "total_tokens",
        "total_cost",
        "avg_tokens",
        "avg_cost",
    ]
    assert_dict_has_keys(cost, required_keys, "/metrics/cost.cost")

    if "sample_size" not in body:
        fail("/metrics/cost response missing sample_size")

    print(json.dumps(body, ensure_ascii=False, indent=2))

    assert_number(cost["total_requests"], "/metrics/cost.cost.total_requests")
    assert_number(cost["total_prompt_tokens"], "/metrics/cost.cost.total_prompt_tokens")
    assert_number(cost["total_completion_tokens"], "/metrics/cost.cost.total_completion_tokens")
    assert_number(cost["total_tokens"], "/metrics/cost.cost.total_tokens")
    assert_number(cost["total_cost"], "/metrics/cost.cost.total_cost")
    assert_number(cost["avg_tokens"], "/metrics/cost.cost.avg_tokens")
    assert_number(cost["avg_cost"], "/metrics/cost.cost.avg_cost")
    assert_number(body["sample_size"], "/metrics/cost.sample_size")


def check_summary(base_url: str) -> None:
    print_section("CASE: /metrics/summary")
    status, body = request_json("GET", f"{base_url}/metrics/summary")
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/summary did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/summary response is not an object")

    if "summary" not in body:
        fail("/metrics/summary response missing summary")

    summary = body["summary"]
    if not isinstance(summary, dict):
        fail("/metrics/summary.summary is not an object")

    required_keys = [
        "total_calls",
        "avg_total_ms",
        "avg_llm_ms",
        "avg_retrieval_ms",
    ]
    assert_dict_has_keys(summary, required_keys, "/metrics/summary.summary")

    if "sample_size" not in body:
        fail("/metrics/summary response missing sample_size")

    print(json.dumps(body, ensure_ascii=False, indent=2))

    assert_number(summary["total_calls"], "/metrics/summary.summary.total_calls")
    assert_number(summary["avg_total_ms"], "/metrics/summary.summary.avg_total_ms")
    assert_number(summary["avg_llm_ms"], "/metrics/summary.summary.avg_llm_ms")
    assert_number(summary["avg_retrieval_ms"], "/metrics/summary.summary.avg_retrieval_ms")
    assert_number(body["sample_size"], "/metrics/summary.sample_size")


def check_engines(base_url: str) -> None:
    print_section("CASE: /metrics/engines")
    status, body = request_json("GET", f"{base_url}/metrics/engines")
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/engines did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/engines response is not an object")

    if "engines" not in body:
        fail("/metrics/engines response missing engines")

    engines = body["engines"]
    if not isinstance(engines, dict):
        fail("/metrics/engines.engines is not an object")

    if len(engines) == 0:
        fail("/metrics/engines.engines is empty")

    if "sample_size" not in body:
        fail("/metrics/engines response missing sample_size")

    first_engine_name, first_bucket = next(iter(engines.items()))

    if not isinstance(first_engine_name, str) or not first_engine_name.strip():
        fail("/metrics/engines first engine name is empty")

    if not isinstance(first_bucket, dict):
        fail("/metrics/engines first bucket is not an object")

    required_keys = [
        "calls",
        "avg_total_ms",
        "avg_llm_ms",
        "avg_retrieval_ms",
    ]
    assert_dict_has_keys(first_bucket, required_keys, f"/metrics/engines.engines[{first_engine_name}]")

    print(json.dumps(body, ensure_ascii=False, indent=2))

    assert_number(first_bucket["calls"], f"/metrics/engines.engines[{first_engine_name}].calls")
    assert_number(first_bucket["avg_total_ms"], f"/metrics/engines.engines[{first_engine_name}].avg_total_ms")
    assert_number(first_bucket["avg_llm_ms"], f"/metrics/engines.engines[{first_engine_name}].avg_llm_ms")
    assert_number(
        first_bucket["avg_retrieval_ms"],
        f"/metrics/engines.engines[{first_engine_name}].avg_retrieval_ms",
    )
    assert_number(body["sample_size"], "/metrics/engines.sample_size")


def check_top(base_url: str) -> None:
    print_section("CASE: /metrics/top")
    status, body = request_json("GET", f"{base_url}/metrics/top?limit=5")
    print(f"http_status: {status}")

    if status != 200:
        fail("/metrics/top did not return 200")

    if not isinstance(body, dict):
        fail("/metrics/top response is not an object")

    if "top" not in body:
        fail("/metrics/top response missing top")

    top = body["top"]
    if not isinstance(top, list):
        fail("/metrics/top.top is not a list")

    if len(top) == 0:
        fail("/metrics/top.top is empty")

    if "sample_size" not in body:
        fail("/metrics/top response missing sample_size")

    first = top[0]
    last = top[-1]

    if not isinstance(first, dict):
        fail("/metrics/top first item is not an object")

    if not isinstance(last, dict):
        fail("/metrics/top last item is not an object")

    required_keys = [
        "request_id",
        "engine",
        "status",
        "timestamp",
        "total_ms",
    ]
    assert_dict_has_keys(first, required_keys, "/metrics/top.top[0]")

    print("top[0]:")
    print(json.dumps(first, ensure_ascii=False, indent=2))

    assert_number(first["total_ms"], "/metrics/top.top[0].total_ms")
    assert_number(body["sample_size"], "/metrics/top.sample_size")

    if "total_ms" not in last:
        fail("/metrics/top.top[-1] missing total_ms")

    assert_number(last["total_ms"], "/metrics/top.top[-1].total_ms")

    if first["total_ms"] < last["total_ms"]:
        fail("/metrics/top.top is not sorted by total_ms desc")

    ok("/metrics/top is sorted by total_ms desc")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acceptance checks for observability platform")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8003",
        help="Base URL of the running service, e.g. http://127.0.0.1:8003",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print("Observability Acceptance")
    print(f"base_url: {base_url}")

    check_health(base_url)
    check_ingest(base_url)
    check_recent(base_url)
    check_cost(base_url)
    check_summary(base_url)
    check_engines(base_url)
    check_top(base_url)

    print()
    print("[PASS] acceptance completed successfully")


if __name__ == "__main__":
    main()