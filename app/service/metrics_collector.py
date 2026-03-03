from __future__ import annotations

from typing import Any, Dict, List

from app.models import InvocationMetrics


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