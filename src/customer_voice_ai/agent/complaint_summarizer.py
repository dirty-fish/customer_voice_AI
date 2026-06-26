from typing import Any

from langchain_openai import ChatOpenAI

from customer_voice_ai.core.config import get_settings

SYSTEM_PROMPT = """You summarize customer complaint evidence for product specialists.
Use only the provided complaint snippets.
Be concise, specific, and avoid inventing facts.
Return a business-oriented summary with key themes and risks.
"""


def deterministic_summary(query: str, complaints: list[dict[str, Any]]) -> str:
    if not complaints:
        return f"No similar complaints were found for query: {query}"

    products = {}
    issues = {}

    for complaint in complaints:
        product = complaint.get("product") or "Unknown product"
        issue = complaint.get("issue") or "Unknown issue"

        products[product] = products.get(product, 0) + 1
        issues[issue] = issues.get(issue, 0) + 1

    top_product = max(products.items(), key=lambda item: item[1])
    top_issue = max(issues.items(), key=lambda item: item[1])

    return (
        f"Found {len(complaints)} similar complaints for the query. "
        f"The dominant product is '{top_product[0]}' ({top_product[1]} matches). "
        f"The most frequent issue is '{top_issue[0]}' ({top_issue[1]} matches). "
        "Review the retrieved complaint snippets for concrete examples."
    )


def summarize_complaints(
    query: str,
    complaints: list[dict[str, Any]],
) -> tuple[str, str]:
    settings = get_settings()

    if not settings.llm_api_key:
        return deterministic_summary(query, complaints), "deterministic"

    snippets = []
    for index, complaint in enumerate(complaints, start=1):
        narrative = complaint.get("consumer_complaint_narrative", "")
        snippets.append(
            {
                "rank": index,
                "product": complaint.get("product"),
                "issue": complaint.get("issue"),
                "company": complaint.get("company"),
                "score": complaint.get("score"),
                "snippet": narrative[:700].replace("\n", " "),
            }
        )

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
                "Summarize these retrieved complaints for the analyst.\n"
                f"Query: {query}\n"
                f"Complaints: {snippets}",
            ),
        ]
    )

    return str(response.content), "llm"