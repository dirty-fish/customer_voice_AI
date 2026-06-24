from fastapi.testclient import TestClient

from customer_voice_ai.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_classify_comment() -> None:
    response = client.post(
        "/comments/classify",
        json={
            "text": "A debt collector keeps calling me about a debt I do not recognize.",
            "top_k": 3,
            "confidence_threshold": 0.55,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["label"]
    assert 0 <= payload["score"] <= 1
    assert payload["classification_status"] in {"known", "uncertain"}
    assert len(payload["top_predictions"]) == 3


def test_search_complaints() -> None:
    response = client.post(
        "/search/complaints",
        json={
            "query": "unauthorized credit card charges and dispute rejected",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["results"]) == 2
    assert payload["results"][0]["consumer_complaint_narrative"]
    assert payload["results"][0]["score"] > 0


def test_agent_analyze() -> None:
    response = client.post(
        "/agent/analyze",
        json={
            "query": "A debt collector keeps calling me about a debt I do not owe.",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["answer"]
    assert payload["classification"]["label"]
    assert len(payload["similar_complaints"]) == 2