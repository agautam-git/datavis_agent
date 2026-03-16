import pandas as pd
from models.schemas import RunSqlInput
from db.database import Database
from memory.memory import MemoryManager
from observability.logger import logger


def execute_tool(
    tool_name: str, tool_args: dict, db: Database, memory: MemoryManager
) -> tuple[str, pd.DataFrame | None]:
    """
    Executes a tool call.
    Returns (result_string, dataframe_or_none)
    """

    if tool_name == "list_tables":
        cached = memory.get_cached_tables()
        if cached:
            logger.info("  list_tables: from cache")
            return cached, None
        tables = db.get_tables()
        result = str(tables)
        memory.cache_tables(result)
        return result, None

    elif tool_name == "get_schema":
        table = tool_args.get("table_name")
        cached = memory.get_cached_schema(table)
        if cached:
            logger.info(f"  get_schema({table}): from cache")
            return cached, None
        result = db.get_schema(table)
        memory.cache_schema(table, result)
        return result, None

    elif tool_name == "run_sql":
        try:
            validated = RunSqlInput(**tool_args)
            df = db.execute(validated.sql)
            return df.to_string(index=False), df
        except Exception as e:
            return f"SQL_ERROR: {str(e)}", None

    return f"UNKNOWN_TOOL: {tool_name}", None
