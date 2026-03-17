import json
from openai import OpenAI
from graphs.state import AgentState
from config import CRITIQUE_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def critique_node(state: AgentState) -> AgentState:
    """
    Evaluates complete output.
    Returns failed_component to route retry precisely.
    """
    logger.info("[Critique] evaluating...")

    if state["retry_count"] >= 2:
        logger.warning("[Critique] max retries — forcing approval")
        return {**state, "is_approved": True, "failed_component": "none"}

    response = client.chat.completions.create(
        model    = CRITIQUE_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a strict BI analyst critic.
Evaluate the complete output.

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
- "none"   → approved, nothing failed

Approve if ALL true:
- SQL correctly answers question
- rows > 0 returned
- answer is meaningful
- chart type is appropriate"""
            },
            {
                "role": "user",
                "content": f"""Question: {state['question']}

SQL used:
{state['sql_used']}

Rows returned: {len(state['dataframe']) if state['dataframe'] is not None else 0}

Data sample:
{state['sql_result'][:400] if state['sql_result'] else 'no data'}

Answer:
{state['answer']}

Chart type: {state['chart_type']}"""
            }
        ]
    )

    try:
        raw      = response.choices[0].message.content
        cleaned  = raw.replace("```json", "").replace("```", "").strip()
        parsed   = json.loads(cleaned)
        approved         = parsed.get("approved", False)
        reason           = parsed.get("reason", "")
        failed_component = parsed.get("failed_component", "sql")
        logger.info(f"[Critique] approved: {approved} | failed: {failed_component} | reason: {reason[:100]}")
    except Exception as e:
        logger.warning(f"[Critique] parse error: {e} — approving by default")
        approved         = True
        reason           = ""
        failed_component = "none"

    return {
        **state,
        "is_approved":      approved,
        "critique":         reason,
        "failed_component": failed_component,
        "retry_count":      state["retry_count"] + (0 if approved else 1)
    }