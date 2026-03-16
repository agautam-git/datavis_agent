import pandas as pd
from io import StringIO
from mcp_server.client import MCPClient
from memory.memory import MemoryManager
from models.schemas import RunSqlInput
from observability.logger import logger


async def execute_tool(
    tool_name: str,
    tool_args: dict,
    memory:    MemoryManager,
    mcp:       MCPClient
) -> tuple[str, pd.DataFrame | None]:
    """
    Executes tool via MCP client.
    Returns (result_string, dataframe_or_none)
    """

    if tool_name == "list_tables":
        cached = memory.get_cached_tables()
        if cached:
            logger.info("  list_tables: from cache")
            return cached, None
        result = await mcp.call_tool("list_tables")
        memory.cache_tables(result)
        return result, None

    elif tool_name == "get_schema":
        table  = tool_args.get("table_name")
        cached = memory.get_cached_schema(table)
        if cached:
            logger.info(f"  get_schema({table}): from cache")
            return cached, None
        result = await mcp.call_tool("get_schema", {"table_name": table})
        memory.cache_schema(table, result)
        return result, None

    elif tool_name == "run_sql":
        try:
            validated = RunSqlInput(**tool_args)
            result    = await mcp.call_tool("run_sql", {"sql": validated.sql})
            if result.startswith("SQL_ERROR"):
                return result, None
            try:
                df = pd.read_csv(StringIO(result), sep=r"\s{2,}", engine="python")
                return result, df
            except Exception:
                return result, None
        except Exception as e:
            return f"SQL_ERROR: {str(e)}", None

    return f"UNKNOWN_TOOL: {tool_name}", None