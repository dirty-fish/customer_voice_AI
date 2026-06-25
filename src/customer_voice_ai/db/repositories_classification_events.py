from sqlalchemy import func
from sqlalchemy.orm import Session

from customer_voice_ai.db.models import ClassificationEvent


class ClassificationEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        text: str,
        predicted_label: str,
        score: float,
        classification_status: str,
        confidence_threshold: float,
        top_predictions: list[dict],
        topic_match_status: str,
        topic_matches: list[dict],
        recommended_action: str,
    ) -> ClassificationEvent:
        event = ClassificationEvent(
            text=text,
            predicted_label=predicted_label,
            score=score,
            classification_status=classification_status,
            confidence_threshold=confidence_threshold,
            top_predictions=top_predictions,
            topic_match_status=topic_match_status,
            topic_matches=topic_matches,
            recommended_action=recommended_action,
        )

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event
    
    def summary(self) -> dict:
        total_events = self.session.query(func.count(ClassificationEvent.id)).scalar() or 0

        status_rows = (
            self.session.query(
                ClassificationEvent.classification_status,
                func.count(ClassificationEvent.id),
            )
            .group_by(ClassificationEvent.classification_status)
            .all()
        )

        action_rows = (
            self.session.query(
                ClassificationEvent.recommended_action,
                func.count(ClassificationEvent.id),
            )
            .group_by(ClassificationEvent.recommended_action)
            .all()
        )

        topic_status_rows = (
            self.session.query(
                ClassificationEvent.topic_match_status,
                func.count(ClassificationEvent.id),
            )
            .group_by(ClassificationEvent.topic_match_status)
            .all()
        )

        return {
            "total_events": int(total_events),
            "classification_status_counts": {
                status: int(count) for status, count in status_rows
            },
            "recommended_action_counts": {
                action: int(count) for action, count in action_rows
            },
            "topic_match_status_counts": {
                status: int(count) for status, count in topic_status_rows
            },
        }