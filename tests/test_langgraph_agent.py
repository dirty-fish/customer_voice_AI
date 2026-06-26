import pytest

from customer_voice_ai.agent.langgraph_agent import run_complaint_graph
from customer_voice_ai.core.config import get_settings

pytestmark = pytest.mark.integration

def test_run_complaint_graph(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", None)

    result = run_complaint_graph(
        query="A debt collector keeps calling me about a debt I do not owe.",
        top_k=2,
    )

    assert result["answer"]
    assert result["classification"]["label"]
    assert len(result["search_results"]) == 2
    assert "related_issues" in result
    assert result["answer_source"] == "deterministic"