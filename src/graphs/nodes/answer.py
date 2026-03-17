from openai import OpenAI
from graphs.state import AgentState
from models.schemas import AgentAnswer
from config import FINAL_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def answer_node(state: AgentState) -> AgentState:
    """
    Generates final structured answer from approved SQL results.
    Stores result in report_sections for report accumulation.
    """
    logger.info("[Answer] generating final answer...")

    df_columns = state["df_columns"]
    df_context = (
        f"DataFrame columns: {df_columns}. Use only these in plotly_code."
        if df_columns
        else "No data available. Set chart_type to none."
    )

    final = client.beta.chat.completions.parse(
        model    = FINAL_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a data analyst.
Give a clear concise answer based on the data.
For plotly_code:
- df is already loaded as pandas DataFrame
- create figure called fig
- do NOT call fig.show()
- use double quotes only
- never use escaped quotes
- no template parameter"""
            },
            *state["messages"],
            {
                "role": "user",
                "content": f"{df_context} Give your final structured answer."
            }
        ],
        response_format = AgentAnswer
    )

    result = final.choices[0].message.parsed

    logger.info(f"[Answer] answer: {result.answer[:100]}...")
    logger.info(f"[Answer] chart:  {result.chart_type}")

    # ── Accumulate for report ─────────────────────────────────────
    section = {
        "question":   state["question"],
        "answer":     result.answer,
        "sql_used":   result.sql_used,
        "chart_type": result.chart_type,
        "plotly_code":result.plotly_code,
        "dataframe":  state["dataframe"]
    }

    existing_sections = state.get("report_sections", [])

    return {
        **state,
        "answer":           result.answer,
        "sql_used":         result.sql_used,
        "chart_type":       result.chart_type,
        "plotly_code":      result.plotly_code,
        "report_sections":  existing_sections + [section]
    }