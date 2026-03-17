from openai import OpenAI
from graphs.state import AgentState
from config import AGENT_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def planner_node(state: AgentState) -> AgentState:
    """
    Reads question.
    Creates a brief data retrieval plan.
    Sets up messages for SQL agent.
    """
    question = state["question"]
    logger.info(f"[Planner] question: {question}")

    response = client.chat.completions.create(
        model    = AGENT_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a data analyst planner.
Given a question, create a brief plan for what SQL queries are needed.
Be concise — 2-3 sentences max.
Do not write SQL — just describe what data is needed."""
            },
            {
                "role": "user",
                "content": f"Question: {question}"
            }
        ]
    )

    plan = response.choices[0].message.content
    logger.info(f"[Planner] plan: {plan[:100]}...")

    return {
        **state,
        "messages": [{"role": "user", "content": f"Question: {question}\nPlan: {plan}"}]
    }