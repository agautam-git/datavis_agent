from openai import OpenAI
from memory.memory import MemoryManager
from graphs.single_query import single_query_graph
from config import OPENAI_API_KEY
from observability.logger import logger
from cache.redis_client import QueryCache

_client = OpenAI(api_key=OPENAI_API_KEY)
_memory = MemoryManager(client=_client)
_cache = QueryCache()

logger.info("dependencies initialised")

def get_client() -> OpenAI:
    return _client

def get_memory() -> MemoryManager:
    return _memory

def get_graph():
    return single_query_graph

def get_cache() -> QueryCache:
    return _cache