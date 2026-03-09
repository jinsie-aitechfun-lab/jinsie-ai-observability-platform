from __future__ import annotations

from typing import Any, Dict, List

from app.models import InvocationMetrics


# -----------------------------
# In-memory metrics buffer
# -----------------------------
_METRICS_BUFFER: List[InvocationMetrics] = []


def ingest_metrics(metrics: List[InvocationMetrics]) -> Dict[str, Any]:
    """
    Store invocation metrics in memory buffer.
    """
    global _METRICS_BUFFER

    _METRICS_BUFFER.extend(metrics)

    latest_ts = metrics[-1].timestamp if metrics else None

    return {
        "ingested_count": len(metrics),
        "latest_timestamp": latest_ts,
    }


def get_all_metrics() -> List[InvocationMetrics]:
    """
    Return current buffered metrics.
    """
    return _METRICS_BUFFER


def get_mock_invocations() -> List[InvocationMetrics]:
    return [
        InvocationMetrics(
            request_id="req_001",
            total_ms=1200.5,
            llm_ms=980.2,
            retrieval_ms=120.1,
            engine="qwen",
            status="COMPLETED",
            timestamp="2026-03-03T10:01:02Z",
        ),
        InvocationMetrics(
            request_id="req_002",
            total_ms=800.0,
            llm_ms=610.0,
            retrieval_ms=95.0,
            engine="qwen",
            status="COMPLETED",
            timestamp="2026-03-03T10:03:10Z",
        ),
        InvocationMetrics(
            request_id="req_003",
            total_ms=2100.2,
            llm_ms=1850.3,
            retrieval_ms=180.4,
            engine="siliconflow",
            status="DEGRADED",
            timestamp="2026-03-03T10:05:55Z",
        ),
    ]


def build_summary(invocations: List[InvocationMetrics]) -> Dict[str, Any]:
    if not invocations:
        return {
            "total_calls": 0,
            "avg_total_ms": 0.0,
            "avg_llm_ms": 0.0,
            "avg_retrieval_ms": 0.0,
        }

    total_calls = len(invocations)
    sum_total = sum(i.total_ms for i in invocations)
    sum_llm = sum(i.llm_ms for i in invocations)
    sum_retrieval = sum(i.retrieval_ms for i in invocations)

    return {
        "total_calls": total_calls,
        "avg_total_ms": round(sum_total / total_calls, 2),
        "avg_llm_ms": round(sum_llm / total_calls, 2),
        "avg_retrieval_ms": round(sum_retrieval / total_calls, 2),
    }


def build_engine_summary(invocations: List[InvocationMetrics]) -> Dict[str, Any]:
    """
    Aggregate metrics by engine.
    Return shape:
      {
        "<engine>": {
          "calls": <int>,
          "avg_total_ms": <float>,
          "avg_llm_ms": <float>,
          "avg_retrieval_ms": <float>
        },
        ...
      }
    """
    if not invocations:
        return {}

    buckets: Dict[str, List[InvocationMetrics]] = {}
    for i in invocations:
        key = (i.engine or "unknown").strip() or "unknown"
        buckets.setdefault(key, []).append(i)

    out: Dict[str, Any] = {}
    for engine, items in buckets.items():
        calls = len(items)
        sum_total = sum(x.total_ms for x in items)
        sum_llm = sum(x.llm_ms for x in items)
        sum_retrieval = sum(x.retrieval_ms for x in items)

        out[engine] = {
            "calls": calls,
            "avg_total_ms": round(sum_total / calls, 2),
            "avg_llm_ms": round(sum_llm / calls, 2),
            "avg_retrieval_ms": round(sum_retrieval / calls, 2),
        }

    return out


def build_top_slowest(
    invocations: List[InvocationMetrics],
    *,
    limit: int = 5,
    engine: str | None = None,
    status: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Return top-N slowest invocations by total_ms, optionally filtered by engine/status.
    """
    if not invocations:
        return []

    try:
        n = int(limit)
    except Exception:
        n = 5

    if n <= 0:
        n = 5
    if n > 50:
        n = 50

    engine_norm = (engine or "").strip().lower()
    status_norm = (status or "").strip().lower()

    filtered: List[InvocationMetrics] = []
    for i in invocations:
        if engine_norm:
            if ((i.engine or "").strip().lower() != engine_norm):
                continue
        if status_norm:
            if ((i.status or "").strip().lower() != status_norm):
                continue
        filtered.append(i)

    items = sorted(filtered, key=lambda x: (x.total_ms or 0.0), reverse=True)[:n]

    return [
        {
            "request_id": i.request_id,
            "engine": i.engine,
            "status": i.status,
            "timestamp": i.timestamp,
            "total_ms": i.total_ms,
            "llm_ms": i.llm_ms,
            "retrieval_ms": i.retrieval_ms,
        }
        for i in items
    ]