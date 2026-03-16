from fastapi import APIRouter, Depends
from api.schemas import HealthResponse
from api.dependencies import get_db
from db.database import Database
from observability.langfuse_setup import langfuse
from observability.logger import logger

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Database = Depends(get_db)):
    db_ok       = db.ping()
    langfuse_ok = langfuse.auth_check()

    logger.debug(f"health check — db: {db_ok} langfuse: {langfuse_ok}")

    return HealthResponse(
        status   = "ok" if db_ok else "degraded",
        db       = db_ok,
        langfuse = langfuse_ok
    )