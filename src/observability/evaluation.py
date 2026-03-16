from openai import OpenAI
from models.schemas import EvaluationResult
from config import AGENT_MODEL
from observability.logger import logger
from agent.prompts import EVALUATION_PROMPT


def evaluate_run(
    client: OpenAI,
    question: str,
    answer: str,
    sql_used: str,
    chart_type: str,
    steps: int,
) -> EvaluationResult | None:
    """
    LLM-as-a-judge evaluation.
    Returns structured scores or None if evaluation fails.
    """

    prompt = EVALUATION_PROMPT.format(
        question=question,
        answer=answer,
        sql_used=sql_used,
        chart_type=chart_type,
        steps=steps,
    )

    try:
        response = client.beta.chat.completions.parse(
            model=AGENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=EvaluationResult,
        )
        return response.choices[0].message.parsed

    except Exception as e:
        logger.warning(f"evaluation failed: {e}")
        return None
