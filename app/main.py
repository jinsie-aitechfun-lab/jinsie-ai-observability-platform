from fastapi import FastAPI
from fastapi import Query

from app.models import InvocationMetrics
from app.service.metrics_collector import (
    build_summary,
    build_engine_summary,
    build_top_slowest,
    build_recent_invocations,
    build_cost_summary,
    ingest_metrics,
    get_all_metrics,
)

app = FastAPI(
    title="Jinsie AI Observability Platform",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/metrics/ingest")
def metrics_ingest(metrics: list[InvocationMetrics]):
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