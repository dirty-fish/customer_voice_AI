from sqlalchemy.orm import Session

from customer_voice_ai.db.models import AgentFeedback


class AgentFeedbackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        query: str,
        answer: str,
        rating: int,
        comment: str | None = None,
        answer_source: str | None = None,
        classification_status: str | None = None,
    ) -> AgentFeedback:
        feedback = AgentFeedback(
            query=query,
            answer=answer,
            rating=rating,
            comment=comment,
            answer_source=answer_source,
            classification_status=classification_status,
        )

        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)

        return feedback