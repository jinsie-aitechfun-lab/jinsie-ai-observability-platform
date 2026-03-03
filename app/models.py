from pydantic import BaseModel


class InvocationMetrics(BaseModel):
    request_id: str
    total_ms: float
    llm_ms: float
    retrieval_ms: float
    engine: str
    status: str
    timestamp: str