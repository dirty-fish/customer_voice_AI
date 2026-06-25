from sqlalchemy.orm import Session

from customer_voice_ai.db.models import Topic
from customer_voice_ai.ml.embedding_service import get_embedding_service


class TopicRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(
        self,
        name: str,
        description: str | None = None,
        source: str = "manual",
    ) -> Topic:
        normalized_name = name.strip()
        
        embedding_text = (
            f"{normalized_name}. {description}"
            if description
            else normalized_name
            )
        embedding = get_embedding_service().embed_text(embedding_text)

        topic = (
            self.session.query(Topic)
            .filter(Topic.name == normalized_name)
            .one_or_none()
        )

        if topic is not None:
            return topic

        topic = Topic(
            name=normalized_name,
            description=description,
            source=source,
            embedding=embedding,
        )

        self.session.add(topic)
        self.session.commit()
        self.session.refresh(topic)

        return topic

    def list_active(self, limit: int = 100) -> list[Topic]:
        return (
            self.session.query(Topic)
            .filter(Topic.status == "active")
            .order_by(Topic.created_at.desc())
            .limit(limit)
            .all()
        )