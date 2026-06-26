from customer_voice_ai.api.routes import (
    determine_recommended_action,
    determine_topic_match_status,
)


def test_determine_recommended_action_accepts_known_class() -> None:
    action = determine_recommended_action(
        classification_status="known",
        topic_matches=[{"score": 0.9}],
    )

    assert action == "accept_product_class"


def test_determine_recommended_action_routes_to_dynamic_topic() -> None:
    action = determine_recommended_action(
        classification_status="uncertain",
        topic_matches=[{"score": 0.8}],
    )

    assert action == "route_to_dynamic_topic"


def test_determine_recommended_action_sends_to_review() -> None:
    action = determine_recommended_action(
        classification_status="uncertain",
        topic_matches=[{"score": 0.1}],
    )

    assert action == "send_to_human_review"


def test_determine_topic_match_status_known_not_applicable() -> None:
    status = determine_topic_match_status(
        classification_status="known",
        topic_matches=[{"score": 0.9}],
    )

    assert status == "not_applicable"