from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graphs.state import AgentState
from graphs.nodes.planner import planner_node
from graphs.nodes.sql_agent import sql_agent_node
from graphs.nodes.chart_agent import chart_agent_node
from graphs.nodes.answer import answer_node
from graphs.nodes.critique import critique_node
from observability.logger import logger


def should_retry(state: AgentState) -> str:
    if state["is_approved"]:
        logger.info("[Graph] approved → END")
        return "end"

    failed = state.get("failed_component", "sql")
    logger.info(f"[Graph] rejected — failed: {failed} | retry: {state['retry_count']}")

    if failed == "chart":
        return "chart_agent"
    elif failed == "answer":
        return "answer"
    else:
        return "sql_agent"


def build_single_query_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner",     planner_node)
    graph.add_node("sql_agent",   sql_agent_node)
    graph.add_node("chart_agent", chart_agent_node)
    graph.add_node("answer",      answer_node)
    graph.add_node("critique",    critique_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner",     "sql_agent")
    graph.add_edge("sql_agent",   "chart_agent")
    graph.add_edge("chart_agent", "answer")
    graph.add_edge("answer",      "critique")

    graph.add_conditional_edges(
        "critique",
        should_retry,
        {
            "end":         END,
            "sql_agent":   "sql_agent",
            "chart_agent": "chart_agent",
            "answer":      "answer"
        }
    )

    return graph.compile(checkpointer=MemorySaver())


single_query_graph = build_single_query_graph()