from openai import OpenAI
from memory.memory import MemoryManager
from mcp_server.client import MCPClient
from config import OPENAI_API_KEY, MCP_SERVER_PATH
from observability.logger import logger


# ── Created once at startup ───────────────────────────────────────
_client = OpenAI(api_key=OPENAI_API_KEY)
_memory = MemoryManager(client=_client)

logger.info("dependencies initialised")


def get_client() -> OpenAI:
    return _client

def get_memory() -> MemoryManager:
    return _memory