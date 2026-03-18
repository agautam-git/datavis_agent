import json
import pandas as pd
from openai import OpenAI
from graphs.state import AgentState, store_df
from mcp_server.client import MCPClient
from agent.tools import TOOLS
from agent.prompts import SYSTEM_PROMPT
from config import AGENT_MODEL, OPENAI_API_KEY, MCP_SERVER_PATH
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


async def sql_agent_node(state: AgentState) -> AgentState:
    logger.info("[SQL Agent] running...")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": state["question"]}
    ]

    if state.get("critique") and state.get("retry_count", 0) > 0:
        messages.append({
            "role":    "user",
            "content": f"Previous attempt failed. Feedback: {state['critique']}. Please fix."
        })
        logger.info(f"[SQL Agent] retry {state['retry_count']} — feedback: {state['critique'][:80]}")

    last_df  = None
    sql_used = ""
    result   = ""

    async with MCPClient(MCP_SERVER_PATH) as mcp:
        while True:
            response = client.chat.completions.create(
                model    = AGENT_MODEL,
                messages = messages,
                tools    = TOOLS
            )

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                break

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)

                if tc.function.name == "list_tables":
                    logger.info("[SQL Agent] list_tables()")
                    result = await mcp.call_tool("list_tables")

                elif tc.function.name == "get_schema":
                    logger.info(f"[SQL Agent] get_schema({args.get('table_name')})")
                    result = await mcp.call_tool("get_schema", args)

                elif tc.function.name == "run_sql":
                    sql    = args.get("sql")
                    logger.info(f"[SQL Agent] run_sql: {sql}")
                    result = await mcp.call_tool("run_sql", {"sql": sql})

                    if not result.startswith("SQL_ERROR"):
                        try:
                            last_df  = pd.read_csv(
                                pd.io.common.StringIO(result),
                                sep    = r"\s{2,}",
                                engine = "python"
                            )
                            sql_used = sql
                            logger.info(f"[SQL Agent] rows: {len(last_df)}")
                        except Exception as e:
                            logger.warning(f"[SQL Agent] df parse error: {e}")
                    else:
                        logger.error(f"[SQL Agent] failed: {result}")

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result
                })

    if last_df is not None:
        store_df(state["thread_id"], last_df)

    safe_messages = [m for m in messages if isinstance(m, dict)]

    return {
        **state,
        "messages":   safe_messages,
        "sql_result": result if last_df is not None else "",
        "df_columns": [str(c) for c in last_df.columns] if last_df is not None else [],
        "sql_used":   sql_used
    }