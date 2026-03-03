# Architecture

- Goal: Turn runtime invocation data into observability assets for AI applications.
- Core atom: InvocationMetrics (request_id + latency breakdown + engine + status + timestamp).
- Minimal API: GET /metrics/summary aggregates mock invocations for quick validation.
- Future: ingest from RAG/Agent projects as a standard metrics payload.
- Extendable: multi-tenant, per-engine breakdown, storage + dashboards later.