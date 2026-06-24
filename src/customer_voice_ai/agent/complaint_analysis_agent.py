from customer_voice_ai.analytics import get_complaint_analytics
from customer_voice_ai.ml.product_classifier import get_product_classifier
from customer_voice_ai.rag.local_search import get_complaint_search


class ComplaintAnalysisAgent:
    def analyze(self, query: str, top_k: int = 3) -> dict:
        classifier = get_product_classifier()
        search = get_complaint_search()
        analytics = get_complaint_analytics()

        classification = classifier.predict(
            text=query,
            top_k=3,
            confidence_threshold=0.55,
        )
        search_results = search.search(query=query, top_k=top_k)
        summary = analytics.product_summary(top_n=5)

        top_product = classification["label"]
        top_product_count = next(
            (
                item["count"]
                for item in summary["top_products"]
                if item["product"] == top_product
            ),
            None,
        )

        related_issues = summary["top_issues_by_product"].get(top_product, [])

        answer = self._build_answer(
            query=query,
            classification=classification,
            top_product_count=top_product_count,
            related_issues=related_issues,
            search_results=search_results,
        )

        return {
            "query": query,
            "answer": answer,
            "classification": classification,
            "related_issues": related_issues,
            "similar_complaints": search_results,
        }

    def _build_answer(
        self,
        query: str,
        classification: dict,
        top_product_count: int | None,
        related_issues: list[dict],
        search_results: list[dict],
    ) -> str:
        status = classification["classification_status"]
        label = classification["label"]
        score = classification["score"]

        if status == "known":
            first_sentence = (
                f"The query is most likely related to '{label}' "
                f"with confidence {score:.2f}."
            )
        else:
            first_sentence = (
                f"The query was classified as '{label}', but confidence is only {score:.2f}, "
                "so it should be reviewed as a possible emerging or out-of-taxonomy topic."
            )

        count_sentence = (
            f"This product appears {top_product_count} times in the current analytical dataset."
            if top_product_count is not None
            else "This product is not in the current top product summary."
        )

        if related_issues:
            issue_text = "; ".join(
                f"{item['issue']} ({item['count']})"
                for item in related_issues[:3]
            )
            issue_sentence = f"Top related issues are: {issue_text}."
        else:
            issue_sentence = "No related issue summary is available for this product."

        if search_results:
            source = search_results[0]
            source_sentence = (
                "The closest historical complaint has "
                f"product='{source.get('product')}', issue='{source.get('issue')}', "
                f"similarity={source.get('score'):.2f}."
            )
        else:
            source_sentence = "No similar historical complaints were found."

        return " ".join([first_sentence, count_sentence, issue_sentence, source_sentence])


def get_complaint_analysis_agent() -> ComplaintAnalysisAgent:
    return ComplaintAnalysisAgent()