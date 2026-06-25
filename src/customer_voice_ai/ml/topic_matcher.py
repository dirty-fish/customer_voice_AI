from functools import lru_cache

from sqlalchemy import select

from customer_voice_ai.db.models import Topic
from customer_voice_ai.db.session import SessionLocal
from customer_voice_ai.ml.embedding_service import get_embedding_service


class TopicMatcher:
    def __init__(self) -> None:
        self.embedding_service = get_embedding_service()

    def match(self, text: str, top_k: int = 3) -> list[dict]:
        if not text.strip():
            raise ValueError("Text must not be empty")

        query_embedding = self.embedding_service.embed_text(text)
        distance = Topic.embedding.cosine_distance(query_embedding)

        statement = (
            select(
                Topic.topic_id,
                Topic.name,
                Topic.description,
                Topic.source,
                Topic.status,
                distance.label("distance"),
            )
            .where(Topic.embedding.is_not(None))
            .where(Topic.status == "active")
            .order_by(distance)
            .limit(top_k)
        )

        with SessionLocal() as session:
            rows = session.execute(statement).all()

        return [
            {
                "topic_id": row.topic_id,
                "name": row.name,
                "description": row.description,
                "source": row.source,
                "status": row.status,
                "score": 1.0 - float(row.distance),
            }
            for row in rows
        ]


@lru_cache
def get_topic_matcher() -> TopicMatcher:
    return TopicMatcher()