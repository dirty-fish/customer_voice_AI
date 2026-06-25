from customer_voice_ai.agent.langgraph_agent import run_complaint_graph


def main() -> None:
    result = run_complaint_graph(
        query="A debt collector keeps calling me about a debt I do not owe.",
        top_k=2,
    )

    print(result["answer"])
    print("\nClassification:")
    print(result["classification"])
    print("\nSimilar complaints:")
    for item in result["search_results"]:
        print(f"- {item['product']} | {item['issue']} | score={item['score']:.3f}")


if __name__ == "__main__":
    main()