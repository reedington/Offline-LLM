from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    index_ready: bool
    documents_count: int


class DocumentMetadata(BaseModel):
    filename: str
    file_type: str
    characters: int
    chunks: int = 0


class UploadResponse(BaseModel):
    documents: list[DocumentMetadata]
    chunks: int
    index_ready: bool
    message: str


class ChatRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)


class EvidenceItem(BaseModel):
    source_document: str
    chunk_id: str
    quote: str
    confidence: str


class RetrievedChunk(BaseModel):
    source_document: str
    chunk_id: str
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    evidence: list[EvidenceItem]
    retrieved_chunks: list[RetrievedChunk]
    latency_ms: int


class CalculateRequest(BaseModel):
    operation: str
    cost: float | None = None
    revenue: float | None = None
    original_price: float | None = None
    discount_percent: float | None = None
    items: list[dict] | None = None
