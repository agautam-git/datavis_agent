from typing import TypedDict
import json
import pandas as pd


class AgentState(TypedDict):

    # ── Identity ──────────────────────────────────────────────────
    thread_id:         str

    # ── Input ─────────────────────────────────────────────────────
    question:          str

    # ── SQL Agent output ──────────────────────────────────────────
    messages:          list
    sql_result:        str
    df_columns:        list[str]
    sql_used:          str

    # ── Final output ──────────────────────────────────────────────
    answer:            str
    chart_type:        str
    plotly_code:       str

    # ── Control flow ──────────────────────────────────────────────
    critique:          str
    failed_component:  str
    retry_count:       int
    is_approved:       bool

    # ── Report accumulation ───────────────────────────────────────
    report_sections:   list[dict]


def make_initial_state(question: str, thread_id: str = "default") -> AgentState:
    return AgentState(
        thread_id        = thread_id,
        question         = question,
        messages         = [],
        sql_result       = "",
        df_columns       = [],
        sql_used         = "",
        answer           = "",
        chart_type       = "none",
        plotly_code      = "",
        critique         = "",
        failed_component = "none",
        retry_count      = 0,
        is_approved      = False,
        report_sections  = []
    )


# ── DataFrame local cache — never sent to LLM ────────────────────
_df_cache: dict = {}


def store_df(thread_id: str, df: pd.DataFrame):
    _df_cache[thread_id] = df


def get_df(thread_id: str) -> pd.DataFrame | None:
    return _df_cache.get(thread_id)