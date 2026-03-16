from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import health, agent, memory
from api.dependencies import get_db
from observability.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Good place to verify connections before accepting requests.
    """
    # ── Startup ───────────────────────────────────────────────────
    logger.info("starting data agent API")
    db = get_db()
    if not db.ping():
        logger.error("database connection failed on startup")
    else:
        logger.info(f"database connected — tables: {db.get_tables()}")

    yield  # ← app runs here

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("shutting down data agent API")
    db.close()


# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Data Agent API",
    description = "AI data analyst agent with DuckDB backend",
    version     = "0.1.0",
    lifespan    = lifespan
)

# ── Register routers ──────────────────────────────────────────────
app.include_router(health.router,  tags=["health"])
app.include_router(agent.router,   tags=["agent"])
app.include_router(memory.router,  tags=["memory"])