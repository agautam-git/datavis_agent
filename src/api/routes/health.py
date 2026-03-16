from fastapi import APIRouter
from api.schemas import HealthResponse
from observability.langfuse_setup import langfuse
from observability.logger import logger
from mcp_server.client import MCPClient
from config import MCP_SERVER_PATH

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        async with MCPClient(MCP_SERVER_PATH) as mcp:
            tables = await mcp.call_tool("list_tables")
            db_ok  = len(tables) > 0
    except Exception:
        db_ok = False

    try:
        langfuse_ok = langfuse.auth_check()
    except Exception:
        langfuse_ok = False

    logger.debug(f"health check — db: {db_ok} langfuse: {langfuse_ok}")

    return HealthResponse(
        status   = "ok" if db_ok else "degraded",
        db       = db_ok,
        langfuse = langfuse_ok
    )