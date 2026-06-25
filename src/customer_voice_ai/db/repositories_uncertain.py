from sqlalchemy import desc
from sqlalchemy.orm import Session

from customer_voice_ai.db.models import UncertainClassification
from customer_voice_ai.db.repositories_topics import TopicRepository


class UncertainClassificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        text: str,
        predicted_label: str,
        score: float,
        confidence_threshold: float,
        top_predictions: list[dict],
    ) -> UncertainClassification:
        event = UncertainClassification(
            text=text,
            predicted_label=predicted_label,
            score=score,
            confidence_threshold=confidence_threshold,
            top_predictions=top_predictions,
        )

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event
    
    def list_pending(self, limit: int = 50) -> list[UncertainClassification]:
        return (
            self.session.query(UncertainClassification)
            .filter(UncertainClassification.review_status == "pending")
            .order_by(desc(UncertainClassification.created_at))
            .limit(limit)
            .all()
        )

    def mark_reviewed(
        self,
        event_id: str,
        assigned_label: str,
    ) -> UncertainClassification | None:
        event = (
            self.session.query(UncertainClassification)
            .filter(UncertainClassification.event_id == event_id)
            .one_or_none()
        )

        if event is None:
            return None

        event.assigned_label = assigned_label
        event.review_status = "reviewed"

        TopicRepository(self.session).get_or_create(
            name=assigned_label,
            description=f"Created from uncertain classification event {event.event_id}",
            source="human_review",
        )

        self.session.commit()
        self.session.refresh(event)

        return event