import os
from dotenv import load_dotenv

load_dotenv()

# ── API keys ──────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")

# ── Models ────────────────────────────────────────────────────────
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4.1-mini")
FINAL_MODEL = os.getenv("FINAL_MODEL", "gpt-5-mini")

CRITIQUE_MODEL    = os.getenv("CRITIQUE_MODEL",   AGENT_MODEL)
EVALUATION_MODEL  = os.getenv("EVALUATION_MODEL", AGENT_MODEL)
CHART_MODEL       = os.getenv("CHART_MODEL",      FINAL_MODEL)

# ── Agent settings ────────────────────────────────────────────────
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
MAX_TURNS = int(os.getenv("MAX_TURNS", 6))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 6000))

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# ── Database ──────────────────────────────────────────────────────
# DB_PATH = os.path.join(BASE_DIR, os.getenv("DB_PATH"))
DB_PATH = os.getenv("DB_PATH", "/app/data/AdventureWorks.duckdb")

# ── Model costs (per 1M tokens in USD) ───────────────────────────
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
}

# ──  MCP  ─────────────────────────────────────────────────────────
MCP_SERVER_PATH = os.path.join(BASE_DIR, "src", "mcp_server", "server.py")

