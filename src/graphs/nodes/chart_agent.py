import json
from openai import OpenAI
from graphs.state import AgentState
from config import CHART_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


async def chart_agent_node(state: AgentState) -> AgentState:
    logger.info("[Chart Agent] generating chart...")

    if not state["df_columns"] or not state["sql_result"]:
        logger.info("[Chart Agent] no data — skipping")
        return {**state, "chart_type": "none", "plotly_code": ""}

    response = client.chat.completions.create(
        model    = CHART_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a data visualisation expert.
Return JSON only — no markdown:
{
  "chart_type": "bar|line|pie|scatter|histogram|table|none",
  "plotly_code": "import plotly.express as px\nfig = px.bar(...)"
}
Rules:
- df is already loaded as pandas DataFrame
- create figure called fig
- do NOT call fig.show()
- use double quotes only — never single quotes
- no escaped quotes, no template parameter
- use ONLY the exact column names provided
- for single value results use chart_type none"""
            },
            {
                "role": "user",
                "content": f"""Question: {state['question']}
DataFrame columns: {state['df_columns']}
Data sample:
{state['sql_result'][:500]}"""
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
        chart_type, plotly_code = "none", ""

    return {**state, "chart_type": chart_type, "plotly_code": plotly_code}