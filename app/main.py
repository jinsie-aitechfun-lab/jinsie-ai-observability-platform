from fastapi import FastAPI

from app.models import InvocationMetrics
from app.service.metrics_collector import (
    build_summary,
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
