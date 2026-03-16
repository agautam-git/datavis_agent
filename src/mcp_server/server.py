import asyncio
import duckdb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from config import DB_PATH
from observability.logger import logger
import sys
from loguru import logger

server = Server("datavis-agent")
conn   = None

# remove default handler
logger.remove()

# log to stderr only — stdout is reserved for MCP protocol
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}"
)

def get_connection():
    """Get or create DB connection."""
    global conn
    if conn is None:
        conn = duckdb.connect(DB_PATH)
        logger.info(f"MCP server connected to: {DB_PATH}")
    return conn


# ── Tool 1: list_tables ───────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Register all available tools with MCP."""
    return [
        types.Tool(
            name="list_tables",
            description="List all available tables in the database. Call this first to discover what data is available.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_schema",
            description="Get schema, row count and sample row for a specific table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to inspect"
                    }
                },
                "required": ["table_name"]
            }
        ),
        types.Tool(
            name="run_sql",
            description="Run a DuckDB SQL query. Use JOINs across tables when needed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Valid DuckDB SQL query"
                    }
                },
                "required": ["sql"]
            }
        )
    ]


# ── Tool execution ────────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a tool call and return result."""

    if name == "list_tables":
        tables = conn.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchdf()["table_name"].tolist()
        result = str(tables)

    elif name == "get_schema":
        table  = arguments.get("table_name")
        cols   = conn.execute(f"DESCRIBE {table}").fetchdf()
        count  = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        sample = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchdf()
        result = (
            f"TABLE: {table} | rows: {count}\n"
            f"COLUMNS:\n{cols[['column_name', 'column_type']].to_string(index=False)}\n"
            f"SAMPLE:\n{sample.to_string(index=False)}"
        )

    elif name == "run_sql":
        sql = arguments.get("sql")
        try:
            df     = conn.execute(sql).fetchdf()
            result = df.to_string(index=False)
        except Exception as e:
            result = f"SQL_ERROR: {str(e)}"

    else:
        result = f"UNKNOWN_TOOL: {name}"

    logger.info(f"MCP tool called: {name}")
    return [types.TextContent(type="text", text=result)]


# ── Run server ────────────────────────────────────────────────────
async def main():
    global conn
    try:
        # open connection on startup
        conn = duckdb.connect(DB_PATH)
        logger.info(f"MCP server connected to: {DB_PATH}")

        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        # always close connection on shutdown
        if conn:
            conn.close()
            logger.info("MCP server DB connection closed")


if __name__ == "__main__":
    asyncio.run(main())