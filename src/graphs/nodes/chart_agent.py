import json
from openai import OpenAI
from graphs.state import AgentState
from config import FINAL_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def chart_agent_node(state: AgentState) -> AgentState:
    """
    Reads df_columns and sql_result from state.
    Generates appropriate plotly code.
    """
    logger.info("[Chart Agent] generating chart...")

    df_columns = state["df_columns"]
    sql_result = state["sql_result"]
    question   = state["question"]

    if not df_columns or not sql_result:
        logger.info("[Chart Agent] no data — skipping")
        return {**state, "chart_type": "none", "plotly_code": ""}

    response = client.chat.completions.create(
        model    = FINAL_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a data visualisation expert.
Given data and a question decide the best chart and write plotly code.

Rules:
- df is already loaded as pandas DataFrame
- create figure called fig
- do NOT call fig.show()
- use double quotes only — never single quotes
- never use escaped quotes
- no template parameter
- use only the exact columns provided
- choose: bar, line, pie, scatter, histogram, table, none

Return JSON only — no markdown:
{
  "chart_type": "bar",
  "plotly_code": "import plotly.express as px\nfig = px.bar(...)"
}"""
            },
            {
                "role": "user",
                "content": f"""Question: {question}
DataFrame columns: {df_columns}
Data sample:
{sql_result[:500]}"""
            }
        ]
    )

    try:
        raw     = response.choices[0].message.content
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed  = json.loads(cleaned)
        chart_type  = parsed.get("chart_type", "none")
        plotly_code = parsed.get("plotly_code", "")
        logger.info(f"[Chart Agent] chart_type: {chart_type}")
    except Exception as e:
        logger.warning(f"[Chart Agent] parse error: {e}")
        chart_type  = "none"
        plotly_code = ""

    return {
        **state,
        "chart_type":  chart_type,
        "plotly_code": plotly_code
    }