from fastapi import FastAPI

from app.service.metrics_collector import build_summary, get_mock_invocations

app = FastAPI(
    title="Jinsie AI Observability Platform",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics/summary")
def metrics_summary():
    invocations = get_mock_invocations()
    summary = build_summary(invocations)
    return {
        "summary": summary,
        "sample_size": len(invocations),
    }