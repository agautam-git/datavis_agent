import redis
import hashlib
import json
import pandas as pd
from typing import Optional
from observability.logger import logger


class QueryCache:

    def __init__(self, host: str = "localhost", port: int = 6379, ttl: int = 3600):
        self.ttl = ttl
        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            self.client.ping()
            self.enabled = True
            logger.info(f"Redis connected: {host}:{port}")
        except Exception as e:
            self.enabled = False
            logger.warning(f"Redis unavailable — cache disabled: {e}")

    def _make_key(self, question: str) -> str:
        return f"query:{hashlib.sha256(question.strip().lower().encode()).hexdigest()}"

    def get(self, question: str) -> Optional[dict]:
        if not self.enabled:
            return None
        try:
            data = self.client.get(self._make_key(question))
            if data:
                logger.info(f"[Cache] HIT: {question[:50]}")
                return json.loads(data)
            logger.info(f"[Cache] MISS: {question[:50]}")
            return None
        except Exception as e:
            logger.warning(f"[Cache] get error: {e}")
            return None

    def set(self, question: str, result: dict, df: pd.DataFrame | None = None) -> bool:
        if not self.enabled:
            return False
        try:
            cacheable = {
                "answer":      result.get("answer", ""),
                "sql_used":    result.get("sql_used", ""),
                "chart_type":  result.get("chart_type", "none"),
                "plotly_code": result.get("plotly_code", ""),
                "df_columns":  result.get("df_columns", []),
                "df_json":     df.to_json(orient="records") if df is not None else ""
            }
            self.client.setex(self._make_key(question), self.ttl, json.dumps(cacheable))
            logger.info(f"[Cache] SET: {question[:50]} (TTL={self.ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"[Cache] set error: {e}")
            return False

    def invalidate(self, question: str) -> bool:
        if not self.enabled:
            return False
        try:
            self.client.delete(self._make_key(question))
            logger.info(f"[Cache] INVALIDATED: {question[:50]}")
            return True
        except Exception as e:
            logger.warning(f"[Cache] invalidate error: {e}")
            return False

    def flush(self) -> bool:
        if not self.enabled:
            return False
        try:
            self.client.flushdb()
            logger.info("[Cache] flushed")
            return True
        except Exception as e:
            logger.warning(f"[Cache] flush error: {e}")
            return False

    def stats(self) -> dict:
        if not self.enabled:
            return {"enabled": False}
        try:
            info = self.client.info()
            return {
                "enabled":     True,
                "keys":        self.client.dbsize(),
                "memory_used": info.get("used_memory_human", "unknown"),
                "hits":        info.get("keyspace_hits", 0),
                "misses":      info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}