from pydantic import BaseModel, Field
from typing import Literal


# ── Request models ────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to ask the agent")


# ── Response models ───────────────────────────────────────────────
class AskResponse(BaseModel):
    answer:     str
    sql_used:   str
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram", "none"]
    success:    bool = True


class HealthResponse(BaseModel):
    status:   str
    db:       bool
    langfuse: bool


class MemoryStatsResponse(BaseModel):
    turns:          int
    cached_schemas: int
    summary:        bool
    tokens:         int


class ErrorResponse(BaseModel):
    success: bool = False
    error:   str