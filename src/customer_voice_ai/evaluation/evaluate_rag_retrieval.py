import json
from pathlib import Path

from customer_voice_ai.rag.pgvector_search import get_pgvector_complaint_search

OUTPUT_PATH = Path("artifacts/reports/rag_retrieval_evaluation.json")

EVAL_QUERIES = [
    {
        "query": "debt collector calling about a debt I do not owe",
        "expected_product": "Debt collection",
        "expected_issue_keywords": ["debt not owed", "collect debt not owed"],
    },
    {
        "query": "unauthorized credit card charges and dispute rejected",
        "expected_product": "Credit card or prepaid card",
        "expected_issue_keywords": ["purchase shown", "transaction", "unauthorized"],
    },
    {
        "query": "incorrect information on my credit report",
        "expected_product":
        "Credit reporting, credit repair services, or other personal consumer reports",
        "expected_issue_keywords": ["incorrect information"],
    },
    {
        "query": "mortgage forbearance and struggling to pay",
        "expected_product": "Mortgage",
        "expected_issue_keywords": ["struggling to pay", "forbearance"],
    },
    {
        "query": "bank account closed without explanation",
        "expected_product": "Checking or savings account",
        "expected_issue_keywords": ["closing an account", "managing an account"],
    },
]


def issue_matches(issue: str | None, keywords: list[str]) -> bool:
    if not issue:
        return False

    lowered_issue = issue.lower()
    return any(keyword.lower() in lowered_issue for keyword in keywords)


def evaluate_query(query_config: dict, top_k: int = 5) -> dict:
    search = get_pgvector_complaint_search()
    results = search.search(query=query_config["query"], top_k=top_k)

    expected_product = query_config["expected_product"]
    expected_issue_keywords = query_config["expected_issue_keywords"]

    product_hit_rank = None
    issue_hit_rank = None

    for index, result in enumerate(results, start=1):
        if product_hit_rank is None and result["product"] == expected_product:
            product_hit_rank = index

        if issue_hit_rank is None and issue_matches(
            result.get("issue"),
            expected_issue_keywords,
        ):
            issue_hit_rank = index

    return {
        "query": query_config["query"],
        "expected_product": expected_product,
        "expected_issue_keywords": expected_issue_keywords,
        "product_hit_rank": product_hit_rank,
        "issue_hit_rank": issue_hit_rank,
        "product_hit_at_k": product_hit_rank is not None,
        "issue_hit_at_k": issue_hit_rank is not None,
        "top_results": [
            {
                "rank": index,
                "complaint_id": result["complaint_id"],
                "product": result["product"],
                "issue": result["issue"],
                "score": result["score"],
            }
            for index, result in enumerate(results, start=1)
        ],
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    top_k = 5
    query_results = [
        evaluate_query(query_config, top_k=top_k)
        for query_config in EVAL_QUERIES
    ]

    product_hit_rate = sum(item["product_hit_at_k"] for item in query_results) / len(query_results)
    issue_hit_rate = sum(item["issue_hit_at_k"] for item in query_results) / len(query_results)

    report = {
        "metric": "retrieval_hit_at_k",
        "top_k": top_k,
        "num_queries": len(query_results),
        "product_hit_rate": product_hit_rate,
        "issue_hit_rate": issue_hit_rate,
        "queries": query_results,
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2),
                            encoding="utf-8")

    print(f"Saved RAG retrieval evaluation to: {OUTPUT_PATH}")
    print(f"Product hit@{top_k}: {product_hit_rate:.3f}")
    print(f"Issue hit@{top_k}: {issue_hit_rate:.3f}")


if __name__ == "__main__":
    main()
