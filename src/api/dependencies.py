from openai import OpenAI
from db.database import Database
from memory.memory import MemoryManager
from config import OPENAI_API_KEY
from observability.logger import logger


# ── Created once at startup — shared across all requests ──────────
_client = OpenAI(api_key=OPENAI_API_KEY)
_db     = Database()
_memory = MemoryManager(client=_client)

logger.info("dependencies initialised")


# ── Dependency functions — FastAPI calls these ────────────────────
def get_client() -> OpenAI:
    return _client

def get_db() -> Database:
    return _db

def get_memory() -> MemoryManager:
    return _memory