import json
import time
import random
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)

from config import AGENT_MODEL, FINAL_MODEL, MAX_RETRIES
from models.schemas import AgentAnswer
from agent.tools import TOOLS
from agent.prompts import SYSTEM_PROMPT
from agent.executor import execute_tool
from memory.memory import MemoryManager
from db.database import Database
from observability.logger import logger
from observability.evaluation import evaluate_run
from observability.langfuse_setup import langfuse

import plotly.express as px
import plotly.graph_objects as go


# ── OpenAI client ─────────────────────────────────────────────────
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def call_openai(fn, *args, **kwargs):
    """Retry wrapper with exponential backoff."""
    base_wait = 1

    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)

        except RateLimitError:
            wait = base_wait * (2**attempt) + random.uniform(0, 1)
            logger.warning(
                f"rate limit — waiting {wait:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(wait)

        except APITimeoutError:
            wait = base_wait * (2**attempt)
            logger.warning(
                f"timeout — waiting {wait:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(wait)

        except APIConnectionError:
            wait = base_wait * (2**attempt)
            logger.warning(
                f"connection error — waiting {wait:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(wait)

        except APIStatusError as e:
            if e.status_code >= 500:
                wait = base_wait * (2**attempt)
                logger.warning(f"server error {e.status_code} — waiting {wait:.1f}s")
                time.sleep(wait)
            else:
                logger.error(f"client error {e.status_code}: {e.message}")
                raise

        except Exception as e:
            logger.error(f"unexpected error: {type(e).__name__}: {e}")
            raise

    logger.error(f"all {MAX_RETRIES} attempts failed")
    return None


def run_agent(question: str, db: Database, memory: MemoryManager) -> AgentAnswer | None:

    # ── Trace ─────────────────────────────────────────────────────
    trace = langfuse.trace(
        name="agent-run", input=question, metadata={"model": AGENT_MODEL}
    )

    # ── Memory ────────────────────────────────────────────────────
    memory.add_question(question)
    messages = memory.get_messages(SYSTEM_PROMPT)

    logger.info(f"question: {question}")
    memory.stats(SYSTEM_PROMPT)

    step = 0
    retries = 0
    last_df = None
    run_start = time.time()

    while True:
        gen = trace.generation(
            name=f"agent-loop-{step}", model=AGENT_MODEL, input=messages
        )

        response = call_openai(
            client.chat.completions.create,
            model=AGENT_MODEL,
            messages=messages,
            tools=TOOLS,
        )

        if response is None:
            logger.error("agent loop: all retries failed")
            gen.end(output="failed")
            trace.update(output="openai call failed")
            return None

        msg = response.choices[0].message
        messages.append(msg)

        gen.end(
            output=msg.content or "",
            usage={
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            },
        )

        if not msg.tool_calls:
            break

        for tc in msg.tool_calls:
            step += 1
            args = json.loads(tc.function.arguments)
            span = trace.span(name=tc.function.name, input=args)

            try:
                if tc.function.name == "list_tables":
                    logger.info(f"step {step}: list_tables()")
                    result, _ = execute_tool("list_tables", {}, db, memory)

                elif tc.function.name == "get_schema":
                    logger.info(f"step {step}: get_schema({args.get('table_name')})")
                    result, _ = execute_tool("get_schema", args, db, memory)

                elif tc.function.name == "run_sql":
                    logger.info(f"step {step}: run_sql()")

                    try:
                        validated = __import__(
                            "models.schemas", fromlist=["RunSqlInput"]
                        ).RunSqlInput(**args)
                    except Exception as e:
                        logger.warning(f"  validation failed: {e}")
                        result = f"VALIDATION_ERROR: {str(e)}"
                        retries += 1
                        if retries >= MAX_RETRIES:
                            logger.error("max retries reached. stopping.")
                            trace.update(output="max retries reached")
                            return None
                        messages.append(
                            {"role": "tool", "tool_call_id": tc.id, "content": result}
                        )
                        continue

                    logger.info(f"  sql: {validated.sql}")
                    result, last_df = execute_tool(
                        "run_sql", {"sql": validated.sql}, db, memory
                    )

                    if last_df is not None:
                        logger.info(f"  rows returned: {len(last_df)}")
                        retries = 0
                    else:
                        logger.error(f"  sql failed: {result}")
                        retries += 1
                        if retries >= MAX_RETRIES:
                            logger.error("max retries reached. stopping.")
                            trace.update(output="max retries reached")
                            return None
                        logger.warning(f"  retry {retries}/{MAX_RETRIES}")

            finally:
                span.end(output=str(result)[:500])

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    # ── Final answer ──────────────────────────────────────────────
    try:
        df_columns = (
            [str(col) for col in last_df.columns] if last_df is not None else []
        )
        df_context = (
            f"DataFrame columns: {df_columns}. Use only these in plotly_code."
            if df_columns
            else "No SQL was run. Answer from context only. Set chart_type to none."
        )

        gen_final = trace.generation(
            name="final-answer", model=FINAL_MODEL, input=messages
        )

        final = call_openai(
            client.beta.chat.completions.parse,
            model=FINAL_MODEL,
            messages=messages
            + [
                {
                    "role": "user",
                    "content": f"{df_context} Now give your final structured answer.",
                }
            ],
            response_format=AgentAnswer,
        )

        if final is None:
            logger.error("final answer: all retries failed")
            gen_final.end(output="failed")
            trace.update(output="final answer call failed")
            return None

        result = final.choices[0].message.parsed

        gen_final.end(
            output=result.answer,
            usage={
                "input": final.usage.prompt_tokens,
                "output": final.usage.completion_tokens,
            },
        )

    except Exception as e:
        logger.error(f"final answer error: {e}")
        try:
            fallback = call_openai(
                client.beta.chat.completions.parse,
                model=FINAL_MODEL,
                messages=messages
                + [
                    {
                        "role": "user",
                        "content": f"{df_context} Give final answer. Set plotly_code to empty string and chart_type to none.",
                    }
                ],
                response_format=AgentAnswer,
            )
            if fallback is None:
                return None
            result = fallback.choices[0].message.parsed
            logger.warning("fallback answer used — no chart")
        except Exception as e2:
            logger.error(f"fallback failed: {e2}")
            trace.update(output=f"final answer error: {e2}")
            return None

    # ── Memory ────────────────────────────────────────────────────
    memory.add_answer(result.answer)

    duration = round(time.time() - run_start, 2)
    logger.info(f"answer: {result.answer[:100]}...")
    logger.info(f"chart:  {result.chart_type}")
    logger.info(f"duration: {duration}s")

    trace.update(
        output=result.answer,
        metadata={
            "chart_type": result.chart_type,
            "duration_seconds": duration,
            "steps": step,
            "sql_used": result.sql_used,
        },
    )
    langfuse.flush()

    # ── Evaluation ────────────────────────────────────────────────
    try:
        eval_result = evaluate_run(
            client=client,
            question=question,
            answer=result.answer,
            sql_used=result.sql_used,
            chart_type=result.chart_type,
            steps=step,
        )

        if eval_result:
            trace.score(name="answer_relevance", value=eval_result.answer_relevance)
            trace.score(name="sql_correctness", value=eval_result.sql_correctness)
            trace.score(
                name="chart_appropriateness", value=eval_result.chart_appropriateness
            )
            trace.score(name="tool_efficiency", value=eval_result.tool_efficiency)
            langfuse.flush()
            logger.info(
                f"eval — relevance: {eval_result.answer_relevance} | sql: {eval_result.sql_correctness} | chart: {eval_result.chart_appropriateness} | efficiency: {eval_result.tool_efficiency}"
            )

    except Exception as e:
        logger.warning(f"evaluation failed: {e}")

    # ── Chart ─────────────────────────────────────────────────────
    if result.plotly_code and result.chart_type != "none" and last_df is not None:
        try:
            local_vars = {"df": last_df, "px": px, "go": go}
            exec(result.plotly_code, local_vars)
            local_vars["fig"].show()
        except Exception as e:
            logger.warning(f"chart error: {e}")

    return result
