import pytest
from fastapi.testclient import TestClient

from customer_voice_ai.api.main import app

pytestmark = pytest.mark.integration
client = TestClient(app)

def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"


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
    assert "topic_matches" in payload
    assert payload["recommended_action"] in {
        "accept_product_class",
        "route_to_dynamic_topic",
        "send_to_human_review",
        }
    assert payload["topic_match_status"] in {
        "not_applicable",
        "no_topics",
        "weak_match",
        "strong_match",
    }


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
    assert payload["answer_source"] in {"deterministic", "llm"}

def test_save_agent_feedback() -> None:
    response = client.post(
        "/agent/feedback",
        json={
            "query": "Why are customers complaining about debt collection?",
            "answer": (
                "Debt collection complaints are mainly related to attempts "
                "to collect debt not owed."
            ),
            "rating": 4,
            "comment": "Useful answer.",
            "answer_source": "llm",
            "classification_status": "known",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["feedback_id"]
    assert payload["rating"] == 4
    assert payload["answer_source"] == "llm"
    assert payload["classification_status"] == "known"

def test_list_uncertain_classifications() -> None:
    client.post(
        "/comments/classify",
        json={
            "text":
            "The mobile banking app keeps crashing after login and support has not answered.",
            "top_k": 3,
            "confidence_threshold": 0.95,
        },
    )

    response = client.get("/classifications/uncertain?limit=5")

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert payload[0]["event_id"]
    assert payload[0]["review_status"] == "pending"
    assert payload[0]["top_predictions"]

def test_review_uncertain_classification() -> None:
    create_response = client.post(
        "/comments/classify",
        json={
            "text": "The mobile app crashes on login and support is not responding.",
            "top_k": 3,
            "confidence_threshold": 0.95,
        },
    )
    assert create_response.status_code == 200

    list_response = client.get("/classifications/uncertain?limit=1")
    assert list_response.status_code == 200

    event_id = list_response.json()[0]["event_id"]

    review_response = client.patch(
        f"/classifications/uncertain/{event_id}/review",
        json={"assigned_label": "Mobile app stability issue"},
    )

    assert review_response.status_code == 200
    payload = review_response.json()

    assert payload["event_id"] == event_id
    assert payload["review_status"] == "reviewed"
    assert payload["assigned_label"] == "Mobile app stability issue"

def test_review_uncertain_classification_creates_topic() -> None:
    client.post(
        "/comments/classify",
        json={
            "text": "Face ID login fails in the banking app and customers cannot see balances.",
            "top_k": 3,
            "confidence_threshold": 0.95,
        },
    )

    list_response = client.get("/classifications/uncertain?limit=1")
    assert list_response.status_code == 200

    event_id = list_response.json()[0]["event_id"]
    assigned_label = "Mobile biometric login issue"

    review_response = client.patch(
        f"/classifications/uncertain/{event_id}/review",
        json={"assigned_label": assigned_label},
    )

    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "reviewed"

    topics_response = client.get("/topics?limit=20")
    assert topics_response.status_code == 200

    topic_names = {topic["name"] for topic in topics_response.json()}
    assert assigned_label in topic_names

def test_create_topic() -> None:
    response = client.post(
        "/topics",
        json={
            "name": "Card dispute handling",
            "description": "Complaints about rejected or delayed card transaction disputes.",
            "source": "business_taxonomy",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["name"] == "Card dispute handling"
    assert payload["source"] == "business_taxonomy"
    assert payload["status"] == "active"

    def test_match_topics() -> None:
        client.post(
        "/topics",
        json={
            "name": "Mobile authentication failure",
            "description": "Customers cannot authenticate in the mobile app.",
            "source": "test",
        },
    )

    response = client.post(
        "/topics/match",
        json={
            "text": "Face ID login fails in the banking app.",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["matches"]) >= 1
    assert payload["matches"][0]["score"] > 0

def test_classify_comment_includes_topic_matches() -> None:
    client.post(
        "/topics",
        json={
            "name": "Mobile authentication failure",
            "description": "Customers cannot authenticate in the mobile app.",
            "source": "test",
        },
    )

    response = client.post(
        "/comments/classify",
        json={
            "text": "Face ID login fails in the banking app.",
            "top_k": 3,
            "confidence_threshold": 0.95,
            "include_topic_matches": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["classification_status"] == "uncertain"
    assert len(payload["topic_matches"]) >= 1
    assert payload["recommended_action"] in {
        "route_to_dynamic_topic",
        "send_to_human_review",
        }
    assert payload["topic_match_status"] in {"weak_match", "strong_match"}

def test_classification_runtime_metrics() -> None:
    client.post(
        "/comments/classify",
        json={
            "text": "A debt collector keeps calling me about a debt I do not owe.",
            "top_k": 3,
            "confidence_threshold": 0.55,
        },
    )

    response = client.get("/metrics/classification-runtime")

    assert response.status_code == 200
    payload = response.json()

    assert payload["total_events"] >= 1
    assert isinstance(payload["classification_status_counts"], dict)
    assert isinstance(payload["recommended_action_counts"], dict)
    assert isinstance(payload["topic_match_status_counts"], dict)

def test_csi_summary() -> None:
    response = client.get("/analytics/csi-summary")

    assert response.status_code == 200
    payload = response.json()

    assert payload["total_rows"] >= 1
    assert payload["avg_csi_score"] is None or 1 <= payload["avg_csi_score"] <= 5
    assert isinstance(payload["sentiment_counts"], dict)
    assert isinstance(payload["severity_counts"], dict)
    assert isinstance(payload["lowest_csi_products"], list)
    assert isinstance(payload["monthly_csi"], list)

def test_csi_drivers() -> None:
    response = client.get("/analytics/csi-drivers?min_count=20&limit=5")

    assert response.status_code == 200
    payload = response.json()

    assert payload["min_count"] == 20
    assert isinstance(payload["drivers"], list)

def test_summarize_complaints() -> None:
    response = client.post(
        "/complaints/summarize",
        json={
            "query": "debt collector calling about a debt I do not owe",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["query"]
    assert payload["summary"]
    assert payload["summary_source"] in {"deterministic", "llm"}
    assert len(payload["complaints"]) == 3