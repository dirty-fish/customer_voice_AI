from datetime import UTC, datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from customer_voice_ai.db.session import Base


class AgentFeedback(Base):
    __tablename__ = "agent_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feedback_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    classification_status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class UncertainClassification(Base):
    __tablename__ = "uncertain_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    text: Mapped[str] = mapped_column(Text)
    predicted_label: Mapped[str] = mapped_column(Text, index=True)
    score: Mapped[float] = mapped_column()
    confidence_threshold: Mapped[float] = mapped_column()
    top_predictions: Mapped[list[dict]] = mapped_column(JSONB)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    assigned_label: Mapped[str | None] = mapped_column(Text, nullable=True)

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    date_received: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped[str] = mapped_column(Text, index=True)
    issue: Mapped[str] = mapped_column(Text, index=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_via: Mapped[str | None] = mapped_column(String(64), nullable=True)

    narrative: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        index=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    name: Mapped[str] = mapped_column(Text, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="manual", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)

class ClassificationEvent(Base):
    __tablename__ = "classification_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    text: Mapped[str] = mapped_column(Text)
    predicted_label: Mapped[str] = mapped_column(Text, index=True)
    score: Mapped[float] = mapped_column()
    classification_status: Mapped[str] = mapped_column(String(32), index=True)
    confidence_threshold: Mapped[float] = mapped_column()
    top_predictions: Mapped[list[dict]] = mapped_column(JSONB)

    topic_match_status: Mapped[str] = mapped_column(String(32), index=True)
    topic_matches: Mapped[list[dict]] = mapped_column(JSONB)
    recommended_action: Mapped[str] = mapped_column(String(64), index=True)