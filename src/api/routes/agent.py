from fastapi import APIRouter, Depends, HTTPException
from api.schemas import AskRequest, AskResponse
from api.dependencies import get_memory
from agent.agent import run_agent_async
from memory.memory import MemoryManager
from observability.logger import logger

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    memory:  MemoryManager = Depends(get_memory)
):
    logger.info(f"API request: {request.question}")

    result = await run_agent_async(
        question = request.question,
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