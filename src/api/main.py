from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import health, agent, memory
from mcp_server.client import MCPClient
from config import MCP_SERVER_PATH
from observability.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────
    logger.info("starting data agent API")
    try:
        async with MCPClient(MCP_SERVER_PATH) as mcp:
            tables = await mcp.call_tool("list_tables")
            logger.info(f"MCP server healthy — tables: {tables}")
    except Exception as e:
        logger.error(f"MCP server check failed: {e}")

    yield

    logger.info("shutting down data agent API")


app = FastAPI(
    title       = "Data Agent API",
    description = "AI data analyst agent with DuckDB backend",
    version     = "0.1.0",
    lifespan    = lifespan
)

app.include_router(health.router,  tags=["health"])
app.include_router(agent.router,   tags=["agent"])
app.include_router(memory.router,  tags=["memory"])