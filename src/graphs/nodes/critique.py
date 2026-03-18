import json
from openai import OpenAI
from graphs.state import AgentState, get_df
from config import CRITIQUE_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


async def critique_node(state: AgentState) -> AgentState:
    logger.info("[Critique] evaluating...")

    if state["retry_count"] >= 2:
        logger.warning("[Critique] max retries — forcing approval")
        return {**state, "is_approved": True, "failed_component": "none"}

    df        = get_df(state["thread_id"])
    row_count = len(df) if df is not None else 0

    response = client.chat.completions.create(
        model    = CRITIQUE_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a strict BI analyst critic.
Evaluate the complete output — SQL, chart and answer together.
Return JSON only:
{
  "approved": true/false,
  "reason": "specific actionable feedback",
  "failed_component": "sql|chart|answer|none"
}
failed_component rules:
- "sql"    → SQL wrong, missing, or no data returned
- "chart"  → chart type inappropriate for the data
- "answer" → answer vague, incomplete, or wrong
- "none"   → everything correct

Approve if ALL true:
- SQL correctly answers question
- rows > 0 returned
- answer is meaningful
- chart type appropriate (none is correct for single values)"""
            },
            {
                "role": "user",
                "content": f"""Question: {state['question']}
SQL used: {state['sql_used']}
Rows returned: {row_count}
Data sample: {state['sql_result'][:400]}
Answer: {state['answer']}
Chart type: {state['chart_type']}"""
            }
        ]
    )

    try:
        raw              = response.choices[0].message.content
        cleaned          = raw.replace("```json", "").replace("```", "").strip()
        parsed           = json.loads(cleaned)
        approved         = parsed.get("approved", False)
        reason           = parsed.get("reason", "")
        failed_component = parsed.get("failed_component", "sql")
        logger.info(f"[Critique] approved: {approved} | failed: {failed_component} | reason: {reason[:80]}")
    except Exception as e:
        logger.warning(f"[Critique] parse error: {e} — approving")
        approved, reason, failed_component = True, "", "none"

    return {
        **state,
        "is_approved":      approved,
        "critique":         reason,
        "failed_component": failed_component,
        "retry_count":      state["retry_count"] + (0 if approved else 1)
    }