from pydantic import BaseModel


class InvocationMetrics(BaseModel):
    request_id: str
    total_ms: float
    llm_ms: float
    retrieval_ms: float
    engine: str
    status: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    timestamp: str