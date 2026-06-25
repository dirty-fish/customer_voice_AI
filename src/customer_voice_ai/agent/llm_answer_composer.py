from typing import Any

from langchain_openai import ChatOpenAI

from customer_voice_ai.core.config import get_settings

SYSTEM_PROMPT = """You are an analytics assistant for a Customer Voice team.
You answer using only the provided classification, aggregate metrics, and similar complaints.
Be concise, business-oriented, and explicit when confidence is low.
Do not invent counts, companies, issues, or complaint details.
"""


def compose_llm_answer(
    query: str,
    classification: dict[str, Any],
    related_issues: list[dict[str, Any]],
    search_results: list[dict[str, Any]],
) -> str | None:
    settings = get_settings()

    if not settings.llm_api_key:
        return None

    complaint_snippets = []
    for index, item in enumerate(search_results[:3], start=1):
        narrative = item.get("consumer_complaint_narrative", "")
        snippet = narrative[:500].replace("\n", " ")
        complaint_snippets.append(
            {
                "rank": index,
                "product": item.get("product"),
                "issue": item.get("issue"),
                "company": item.get("company"),
                "similarity": item.get("score"),
                "snippet": snippet,
            }
        )

    evidence = {
        "query": query,
        "classification": classification,
        "related_issues": related_issues[:5],
        "similar_complaints": complaint_snippets,
    }

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                "Prepare a short analytical answer from this evidence:\n"
                f"{evidence}",
            ),
        ]
    )

    return str(response.content)