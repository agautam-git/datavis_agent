# tests/test_imports.py
def test_config():
    from config import AGENT_MODEL, FINAL_MODEL
    assert AGENT_MODEL is not None
    assert FINAL_MODEL is not None

def test_schemas():
    from models.schemas import RunSqlInput, AgentAnswer, EvaluationResult
    assert RunSqlInput is not None

def test_tools():
    from agent.tools import TOOLS
    assert len(TOOLS) == 3

def test_prompts():
    from agent.prompts import SYSTEM_PROMPT
    assert len(SYSTEM_PROMPT) > 0