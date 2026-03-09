from typing import Any, List

from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import ValidationError

from app.models import InvocationMetrics
from app.service.metrics_collector import (
    build_cost_summary,
    build_engine_summary,
    build_recent_invocations,
    build_summary,
    build_top_slowest,
    get_all_metrics,
    ingest_metrics,
)

app = FastAPI(
    title="Jinsie AI Observability Platform",
    version="0.1.0",
)


def _parse_invocation_metrics(obj: Any) -> InvocationMetrics:
    """
    Compatible with Pydantic v1/v2.
    """
    if hasattr(InvocationMetrics, "model_validate"):
        return InvocationMetrics.model_validate(obj)  # pydantic v2
    return InvocationMetrics.parse_obj(obj)  # pydantic v1


def _normalize_metrics_payload(payload: Any) -> List[InvocationMetrics]:
    """
    Accept payload shapes:
      1) [ {...}, {...} ]
      2) { ... }                      (single metric)
      3) { "metrics": [ {...}, ... ] } (wrapped)
    """
    if isinstance(payload, dict) and "metrics" in payload:
        payload = payload["metrics"]

    if isinstance(payload, list):
        items = payload
    else:
        items = [payload]

    out: List[InvocationMetrics] = []
    for x in items:
        out.append(_parse_invocation_metrics(x))
    return out


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/metrics/ingest")
def metrics_ingest(payload: Any = Body(...)):
    try:
        metrics = _normalize_metrics_payload(payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = ingest_metrics(metrics)
    return result


@app.get("/metrics/summary")
def metrics_summary():
    invocations = get_all_metrics()
    summary = build_summary(invocations)
    return {
        "summary": summary,
        "sample_size": len(invocations),
    }


@app.get("/metrics/engines")
def metrics_engines():
    invocations = get_all_metrics()
    engines = build_engine_summary(invocations)
    return {
        "engines": engines,
        "sample_size": len(invocations),
    }


@app.get("/metrics/top")
def metrics_top(
    limit: int = Query(default=5, ge=1, le=50),
    engine: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    invocations = get_all_metrics()
    top = build_top_slowest(invocations, limit=limit, engine=engine, status=status)
    return {
        "top": top,
        "sample_size": len(invocations),
    }


@app.get("/metrics/recent")
def metrics_recent(limit: int = Query(default=10, ge=1, le=100)):
    invocations = get_all_metrics()
    recent = build_recent_invocations(invocations, limit=limit)
    return {
        "recent": recent,
        "sample_size": len(invocations),
    }


@app.get("/metrics/cost")
def metrics_cost():
    invocations = get_all_metrics()
    cost_summary = build_cost_summary(invocations)
    return {
        "cost": cost_summary,
        "sample_size": len(invocations),
    }