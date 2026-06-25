from customer_voice_ai.db.models import Topic
from customer_voice_ai.db.session import SessionLocal
from customer_voice_ai.ml.embedding_service import get_embedding_service


def main() -> None:
    embedding_service = get_embedding_service()

    with SessionLocal() as session:
        topics = session.query(Topic).filter(Topic.embedding.is_(None)).all()

        for topic in topics:
            text = f"{topic.name}. {topic.description}" if topic.description else topic.name
            topic.embedding = embedding_service.embed_text(text)

        session.commit()

    print(f"Updated topic embeddings: {len(topics)}")


if __name__ == "__main__":
    main()