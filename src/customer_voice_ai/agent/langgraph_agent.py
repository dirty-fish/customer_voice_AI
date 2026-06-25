from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from customer_voice_ai.agent.llm_answer_composer import compose_llm_answer
from customer_voice_ai.analytics import get_complaint_analytics
from customer_voice_ai.ml.product_classifier import get_product_classifier
from customer_voice_ai.rag.local_search import get_complaint_search


class ComplaintAgentState(TypedDict, total=False):
    query: str
    top_k: int
    classification: dict[str, Any]
    search_results: list[dict[str, Any]]
    product_summary: dict[str, Any]
    related_issues: list[dict[str, Any]]
    answer: str
    answer_source: str


def classify_query(state: ComplaintAgentState) -> ComplaintAgentState:
    classifier = get_product_classifier()
    state["classification"] = classifier.predict(
        text=state["query"],
        top_k=3,
        confidence_threshold=0.55,
    )
    return state


def search_similar_complaints(state: ComplaintAgentState) -> ComplaintAgentState:
    search = get_complaint_search()
    state["search_results"] = search.search(
        query=state["query"],
        top_k=state.get("top_k", 3),
    )
    return state


def load_product_analytics(state: ComplaintAgentState) -> ComplaintAgentState:
    analytics = get_complaint_analytics()
    summary = analytics.product_summary(top_n=5)

    classification = state["classification"]
    product = classification["label"]
    related_issues = summary["top_issues_by_product"].get(product, [])

    state["product_summary"] = summary
    state["related_issues"] = related_issues
    return state


def compose_answer(state: ComplaintAgentState) -> ComplaintAgentState:
    classification = state["classification"]
    search_results = state["search_results"]
    product_summary = state["product_summary"]
    related_issues = state["related_issues"]

    label = classification["label"]
    score = classification["score"]
    status = classification["classification_status"]

    product_count = next(
        (
            item["count"]
            for item in product_summary["top_products"]
            if item["product"] == label
        ),
        None,
    )

    if status == "known":
        opening = f"The query is most likely related to '{label}' with confidence {score:.2f}."
    else:
        opening = (
            f"The query was mapped to '{label}' with low confidence {score:.2f}; "
            "it should be reviewed as a possible emerging or out-of-taxonomy topic."
        )

    count_sentence = (
        f"This product appears {product_count} times in the current analytical dataset."
        if product_count is not None
        else "This product is outside the current top product summary."
    )

    if related_issues:
        issues = "; ".join(
            f"{item['issue']} ({item['count']})"
            for item in related_issues[:3]
        )
        issues_sentence = f"Top related issues are: {issues}."
    else:
        issues_sentence = "No related issue summary is available."

    if search_results:
        source = search_results[0]
        source_sentence = (
            "Closest historical complaint: "
            f"product='{source.get('product')}', issue='{source.get('issue')}', "
            f"similarity={source.get('score'):.2f}."
        )
    else:
        source_sentence = "No similar complaints were found."
    
    llm_answer = compose_llm_answer(
        query=state["query"],
        classification=classification,
        related_issues=related_issues,
        search_results=search_results,
    )

    if llm_answer:
        state["answer"] = llm_answer
        state["answer_source"] = "llm"
        return state
    
    state["answer"] = " ".join(
        [opening, count_sentence, issues_sentence, source_sentence]
    )
    state["answer_source"] = "deterministic"
    return state


def build_complaint_graph():
    graph = StateGraph(ComplaintAgentState)

    graph.add_node("classify", classify_query)
    graph.add_node("search", search_similar_complaints)
    graph.add_node("analytics", load_product_analytics)
    graph.add_node("compose_answer", compose_answer)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "search")
    graph.add_edge("search", "analytics")
    graph.add_edge("analytics", "compose_answer")
    graph.add_edge("compose_answer", END)

    return graph.compile()


def run_complaint_graph(query: str, top_k: int = 3) -> dict[str, Any]:
    graph = build_complaint_graph()
    return graph.invoke({"query": query, "top_k": top_k})