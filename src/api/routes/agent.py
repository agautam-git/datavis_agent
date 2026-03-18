from fastapi import APIRouter, Depends, HTTPException
import plotly.express as px
import plotly.graph_objects as go

from api.schemas import AskRequest, AskResponse
from api.dependencies import get_memory, get_graph, get_cache
from cache.redis_client import QueryCache
from graphs.state import AgentState, make_initial_state
from graphs.state import get_df
from memory.memory import MemoryManager
from observability.logger import logger
from observability.langfuse_setup import langfuse, langfuse_handler
import time

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    memory:  MemoryManager = Depends(get_memory),
    graph                  = Depends(get_graph),
    cache:   QueryCache    = Depends(get_cache)
):
    logger.info(f"API request: {request.question}")

    # ── 1. Check Cache ────────────────────────────────────────────
    cached_data = cache.get(request.question)
    if cached_data:
        # If found, return immediately without running the graph
        return AskResponse(
            answer=cached_data["answer"],
            sql_used=cached_data["sql_used"],
            chart_type=cached_data["chart_type"],
            success=True
        )

    # Cache Miss: Run Graph
    config = {"configurable": {"thread_id": request.thread_id},
              "callbacks" : [langfuse_handler],
              "metadata" : {
                  "user_id": request.thread_id,
                  "interface":"fastapi"
                }
              }

    initial_state = make_initial_state(request.question, thread_id = request.thread_id)

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"graph failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if not result.get("answer"):
        raise HTTPException(status_code=500, detail="Agent failed to answer")

    memory.add_question(request.question)
    memory.add_answer(result["answer"])

    df = get_df(request.thread_id)

    # Save the result to Redis
    cache.set(request.question, result, df=df)

    if result.get("plotly_code") and result.get("chart_type") != "none" and df is not None:
        try:
            exec(result["plotly_code"], {"df": df, "px": px, "go": go})
        except Exception as e:
            logger.warning(f"chart render error: {e}")

    langfuse_handler.flush()

    return AskResponse(
        answer     = result["answer"],
        sql_used   = result["sql_used"],
        chart_type = result["chart_type"],
        success    = True
    )