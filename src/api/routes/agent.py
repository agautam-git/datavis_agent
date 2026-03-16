from fastapi import APIRouter, Depends, HTTPException
from api.schemas import AskRequest, AskResponse, ErrorResponse
from api.dependencies import get_db, get_memory
from agent.agent import run_agent
from db.database import Database
from memory.memory import MemoryManager
from observability.logger import logger

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    db:      Database      = Depends(get_db),
    memory:  MemoryManager = Depends(get_memory)
):
    """
    Ask the agent a question.
    Returns answer, SQL used, and chart type.
    """
    logger.info(f"API request: {request.question}")

    result = run_agent(
        question = request.question,
        db       = db,
        memory   = memory
    )

    if result is None:
        raise HTTPException(
            status_code = 500,
            detail      = "Agent failed to answer. Please try again."
        )

    return AskResponse(
        answer     = result.answer,
        sql_used   = result.sql_used,
        chart_type = result.chart_type,
        success    = True
    )