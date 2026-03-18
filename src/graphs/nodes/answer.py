from openai import OpenAI
from graphs.state import AgentState
from models.schemas import AgentAnswer
from config import FINAL_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


async def answer_node(state: AgentState) -> AgentState:
    logger.info("[Answer] generating final answer...")

    df_context = (
        f"DataFrame columns: {state['df_columns']}. Use only these in plotly_code."
        if state["df_columns"]
        else "No data available. Set plotly_code to empty string."
    )

    chart_instruction = (
        f"Chart type already decided: {state['chart_type']}. "
        f"Write plotly_code for this chart type only."
        if state["chart_type"] != "none"
        else "No chart needed. Set plotly_code to empty string."
    )

    messages = [
        {
            "role": "system",
            "content": """You are a data analyst.
Give a clear concise answer based on the data provided.
For plotly_code:
- df is already loaded as pandas DataFrame
- create figure called fig
- do NOT call fig.show()
- use double quotes only
- no escaped quotes
- no template parameter"""
        },
        {
            "role": "user",
            "content": f"""Question: {state['question']}
SQL used: {state['sql_used']}
Data: {state['sql_result'][:1000]}
{df_context}
{chart_instruction}
Give your final structured answer."""
        }
    ]

    final = client.beta.chat.completions.parse(
        model           = FINAL_MODEL,
        messages        = messages,
        response_format = AgentAnswer
    )

    result = final.choices[0].message.parsed
    logger.info(f"[Answer] answer: {result.answer[:100]}...")
    logger.info(f"[Answer] chart:  {state['chart_type']}")

    section = {
        "question":    state["question"],
        "answer":      result.answer,
        "sql_used":    result.sql_used,
        "chart_type":  state["chart_type"],
        "plotly_code": result.plotly_code,
        "df_columns":  state["df_columns"],
        "thread_id":   state["thread_id"]
    }

    return {
        **state,
        "answer":          result.answer,
        "sql_used":        result.sql_used,
        "chart_type":      state["chart_type"],
        "plotly_code":     result.plotly_code,
        "report_sections": state.get("report_sections", []) + [section]
    }