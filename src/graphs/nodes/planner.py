from openai import OpenAI
from graphs.state import AgentState
from config import AGENT_MODEL, OPENAI_API_KEY
from observability.logger import logger

client = OpenAI(api_key=OPENAI_API_KEY)


async def planner_node(state: AgentState) -> AgentState:
    logger.info(f"[Planner] question: {state['question']}")

    response = client.chat.completions.create(
        model    = AGENT_MODEL,
        messages = [
            {
                "role": "system",
                "content": """You are a data analyst planner.
Given a question create a brief plan for what SQL queries are needed.
2-3 sentences max. Do NOT write SQL — just describe what data is needed."""
            },
            {
                "role": "user",
                "content": f"Question: {state['question']}"
            }
        ]
    )

    plan = response.choices[0].message.content
    logger.info(f"[Planner] plan: {plan[:100]}...")

    return {
        **state,
        "messages": [
            {"role": "user", "content": f"Question: {state['question']}\nPlan: {plan}"}
        ]
    }