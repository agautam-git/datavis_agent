from fastapi import APIRouter, Depends
from api.schemas import MemoryStatsResponse
from api.dependencies import get_memory, get_db
from memory.memory import MemoryManager
from db.database import Database
from agent.prompts import SYSTEM_PROMPT
from observability.logger import logger

router = APIRouter()


@router.get("/memory/stats", response_model=MemoryStatsResponse)
async def memory_stats(memory: MemoryManager = Depends(get_memory)):
    """Return current memory state."""
    tokens = memory.count_tokens(memory.get_messages(SYSTEM_PROMPT))
    turns  = len([m for m in memory.history if m["role"] == "user"])

    return MemoryStatsResponse(
        turns          = turns,
        cached_schemas = len(memory.schema_cache),
        summary        = memory.summary is not None,
        tokens         = tokens
    )


@router.delete("/memory", response_model=dict)
async def reset_memory(memory: MemoryManager = Depends(get_memory)):
    """Reset conversation history. Preserves schema cache."""
    memory.reset()
    logger.info("memory reset via API")
    return {"status": "reset", "message": "conversation history cleared"}