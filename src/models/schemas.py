from pydantic import BaseModel, Field
from typing import Literal


# ── Tool inputs ───────────────────────────────────────────────────
class RunSqlInput(BaseModel):
    sql: str = Field(..., description="Valid DuckDB SQL query")


# ── Agent final answer ────────────────────────────────────────────
class AgentAnswer(BaseModel):
    answer: str = Field(..., description="Plain English explanation")
    sql_used: str = Field(..., description="SQL that produced the result")
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram", "none"]
    plotly_code: str = Field(..., description="Complete plotly code using df and fig")


# ── Evaluation ────────────────────────────────────────────────────
class EvaluationResult(BaseModel):
    answer_relevance: float = Field(..., ge=0, le=1)
    sql_correctness: float = Field(..., ge=0, le=1)
    chart_appropriateness: float = Field(..., ge=0, le=1)
    tool_efficiency: float = Field(..., ge=0, le=1)
    reasoning: str
