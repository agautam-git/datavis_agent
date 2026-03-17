from typing import TypedDict, Optional


class AgentState(TypedDict):

    # ── Conversation identity ─────────────────────────────────────
    thread_id:         str

    # ── Input ─────────────────────────────────────────────────────
    question:          str

    # ── Messages ─────────────────────────────────────────────────
    messages:          list

    # ── SQL results ───────────────────────────────────────────────
    sql_result:        str
    dataframe:         Optional[object]
    df_columns:        list[str]
    sql_used:          str

    # ── Output ────────────────────────────────────────────────────
    answer:            str
    chart_type:        str
    plotly_code:       str

    # ── Control flow ──────────────────────────────────────────────
    critique:          str
    failed_component:  str      # "sql", "chart", "answer", "none"
    retry_count:       int
    is_approved:       bool

    # ── Report accumulation ───────────────────────────────────────
    report_sections:   list[dict]