from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from customer_voice_ai.agent.complaint_summarizer import summarize_complaints

#from customer_voice_ai.agent.complaint_analysis_agent import get_complaint_analysis_agent
from customer_voice_ai.agent.langgraph_agent import run_complaint_graph
from customer_voice_ai.analytics import get_complaint_analytics
from customer_voice_ai.api.schemas import (
    AgentFeedbackRequest,
    AgentFeedbackResponse,
    AnalyzeComplaintRequest,
    AnalyzeComplaintResponse,
    ClassificationRuntimeMetricsResponse,
    ClassifyCommentRequest,
    ClassifyCommentResponse,
    CreateTopicRequest,
    CsiDriversResponse,
    CsiSummaryResponse,
    MatchTopicsRequest,
    MatchTopicsResponse,
    ProductSummaryResponse,
    ReviewUncertainClassificationRequest,
    SearchComplaintsRequest,
    SearchComplaintsResponse,
    SummarizeComplaintsRequest,
    SummarizeComplaintsResponse,
    TopicResponse,
    UncertainClassificationResponse,
)
from customer_voice_ai.db.repositories import AgentFeedbackRepository
from customer_voice_ai.db.repositories_classification_events import ClassificationEventRepository
from customer_voice_ai.db.repositories_topics import TopicRepository
from customer_voice_ai.db.repositories_uncertain import UncertainClassificationRepository
from customer_voice_ai.db.session import get_db_session
from customer_voice_ai.ml.product_classifier import get_product_classifier
from customer_voice_ai.ml.topic_matcher import get_topic_matcher

#from customer_voice_ai.rag.local_search import get_complaint_search
from customer_voice_ai.rag.pgvector_search import get_pgvector_complaint_search

DbSession = Annotated[Session, Depends(get_db_session)]
router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db_session)]

def determine_topic_match_status(
    classification_status: str,
    topic_matches: list[dict],
    topic_match_threshold: float = 0.35,
) -> str:
    if classification_status == "known":
        return "not_applicable"

    if not topic_matches:
        return "no_topics"

    if topic_matches[0]["score"] >= topic_match_threshold:
        return "strong_match"

    return "weak_match"

def determine_recommended_action(
    classification_status: str,
    topic_matches: list[dict],
    topic_match_threshold: float = 0.35,
    ) -> str:
    if classification_status == "known":
        return "accept_product_class"

    if topic_matches and topic_matches[0]["score"] >= topic_match_threshold:
        return "route_to_dynamic_topic"

    return "send_to_human_review"

def build_uncertain_classification_response(event) -> UncertainClassificationResponse:
    return UncertainClassificationResponse(
        event_id=event.event_id,
        created_at=event.created_at.isoformat(),
        text=event.text,
        predicted_label=event.predicted_label,
        score=event.score,
        confidence_threshold=event.confidence_threshold,
        top_predictions=event.top_predictions,
        review_status=event.review_status,
        assigned_label=event.assigned_label,
    )

def build_topic_response(topic) -> TopicResponse:
    return TopicResponse(
        topic_id=topic.topic_id,
        created_at=topic.created_at.isoformat(),
        updated_at=topic.updated_at.isoformat(),
        name=topic.name,
        description=topic.description,
        source=topic.source,
        status=topic.status,
    )

@router.post("/comments/classify", response_model=ClassifyCommentResponse)
def classify_comment(
    request: ClassifyCommentRequest,
    db: DbSession,
    ) -> ClassifyCommentResponse:
    classifier = get_product_classifier()
    topic_matches = []
    try:
        result = classifier.predict(
            text=request.text,
            top_k=request.top_k,
            confidence_threshold=request.confidence_threshold,
            )
        if result["classification_status"] == "uncertain":
            repository = UncertainClassificationRepository(db)
            repository.create(
                text=request.text,
                predicted_label=result["label"],
                score=result["score"],
                confidence_threshold=result["confidence_threshold"],
                top_predictions=result["top_predictions"],
            )
        
        if request.include_topic_matches:
            topic_matches = get_topic_matcher().match(
                text=request.text,
                top_k=3,
            )        
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    topic_match_status = determine_topic_match_status(
        classification_status=result["classification_status"],
        topic_matches=topic_matches,
    )
    recommended_action = determine_recommended_action(
        classification_status=result["classification_status"],
        topic_matches=topic_matches,
        )
    ClassificationEventRepository(db).create(
        text=request.text,
        predicted_label=result["label"],
        score=result["score"],
        classification_status=result["classification_status"],
        confidence_threshold=result["confidence_threshold"],
        top_predictions=result["top_predictions"],
        topic_match_status=topic_match_status,
        topic_matches=topic_matches,
        recommended_action=recommended_action,
    )
    return ClassifyCommentResponse(
        **result,
        topic_matches=topic_matches,
        topic_match_status=topic_match_status,
        recommended_action=recommended_action,
        )

@router.post("/search/complaints", response_model=SearchComplaintsResponse)
def search_complaints(request: SearchComplaintsRequest) -> SearchComplaintsResponse:
    #search = get_complaint_search()
    search = get_pgvector_complaint_search()

    try:
        results = search.search(query=request.query, top_k=request.top_k)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return SearchComplaintsResponse(results=results)

@router.get(
    "/metrics/classification-runtime",
    response_model=ClassificationRuntimeMetricsResponse,
)
def classification_runtime_metrics(db: DbSession) -> ClassificationRuntimeMetricsResponse:
    repository = ClassificationEventRepository(db)
    summary = repository.summary()

    return ClassificationRuntimeMetricsResponse(**summary)

@router.get("/analytics/product-summary", response_model=ProductSummaryResponse)
def product_summary(top_n: int = 10) -> ProductSummaryResponse:
    analytics = get_complaint_analytics()
    result = analytics.product_summary(top_n=top_n)
    return ProductSummaryResponse(**result)

"""@router.post("/agent/analyze", response_model=AnalyzeComplaintResponse)
def analyze_complaint(request: AnalyzeComplaintRequest) -> AnalyzeComplaintResponse:
    agent = get_complaint_analysis_agent()
    result = agent.analyze(query=request.query, top_k=request.top_k)
    return AnalyzeComplaintResponse(**result)"""

@router.get("/analytics/csi-summary", response_model=CsiSummaryResponse)
def csi_summary() -> CsiSummaryResponse:
    analytics = get_complaint_analytics()
    result = analytics.csi_summary()
    return CsiSummaryResponse(**result)

@router.post("/agent/analyze", response_model=AnalyzeComplaintResponse)
def analyze_complaint(request: AnalyzeComplaintRequest) -> AnalyzeComplaintResponse:
    result = run_complaint_graph(query=request.query, top_k=request.top_k)

    return AnalyzeComplaintResponse(
        query=result["query"],
        answer=result["answer"],
        answer_source=result["answer_source"],
        classification=result["classification"],
        related_issues=result["related_issues"],
        similar_complaints=result["search_results"],
    )

@router.post("/agent/feedback", response_model=AgentFeedbackResponse)
def save_agent_feedback(
    request: AgentFeedbackRequest,
    db: DatabaseSession,
) -> AgentFeedbackResponse:
    repository = AgentFeedbackRepository(db)
    feedback = repository.create(
        query=request.query,
        answer=request.answer,
        rating=request.rating,
        comment=request.comment,
        answer_source=request.answer_source,
        classification_status=request.classification_status,
    )

    return AgentFeedbackResponse(
        feedback_id=feedback.feedback_id,
        created_at=feedback.created_at.isoformat(),
        query=feedback.query,
        answer=feedback.answer,
        rating=feedback.rating,
        comment=feedback.comment,
        answer_source=feedback.answer_source,
        classification_status=feedback.classification_status,
    )

@router.get(
    "/classifications/uncertain",
    response_model=list[UncertainClassificationResponse],
)
def list_uncertain_classifications(
    db: DbSession,
    limit: int = 50,
) -> list[UncertainClassificationResponse]:
    repository = UncertainClassificationRepository(db)
    events = repository.list_pending(limit=limit)

    return [build_uncertain_classification_response(event) for event in events]

@router.patch(
    "/classifications/uncertain/{event_id}/review",
    response_model=UncertainClassificationResponse,
)
def review_uncertain_classification(
    event_id: str,
    request: ReviewUncertainClassificationRequest,
    db: DbSession,
) -> UncertainClassificationResponse:
    repository = UncertainClassificationRepository(db)
    event = repository.mark_reviewed(
        event_id=event_id,
        assigned_label=request.assigned_label,
    )

    if event is None:
        raise HTTPException(status_code=404, detail="Uncertain classification event not found")

    return build_uncertain_classification_response(event)

@router.get("/topics", response_model=list[TopicResponse])
def list_topics(
    db: DbSession,
    limit: int = 100,
) -> list[TopicResponse]:
    repository = TopicRepository(db)
    topics = repository.list_active(limit=limit)

    return [build_topic_response(topic) for topic in topics]

@router.post("/topics", response_model=TopicResponse)
def create_topic(
    request: CreateTopicRequest,
    db: DbSession,
) -> TopicResponse:
    repository = TopicRepository(db)
    topic = repository.get_or_create(
        name=request.name,
        description=request.description,
        source=request.source,
    )

    return build_topic_response(topic)

@router.post("/topics/match", response_model=MatchTopicsResponse)
def match_topics(request: MatchTopicsRequest) -> MatchTopicsResponse:
    matcher = get_topic_matcher()
    matches = matcher.match(text=request.text, top_k=request.top_k)

    return MatchTopicsResponse(matches=matches)

@router.get("/analytics/csi-drivers", response_model=CsiDriversResponse)
def csi_drivers(
    min_count: int = 20,
    limit: int = 10,
) -> CsiDriversResponse:
    analytics = get_complaint_analytics()
    result = analytics.csi_drivers(min_count=min_count, limit=limit)
    return CsiDriversResponse(**result)

@router.post("/complaints/summarize", response_model=SummarizeComplaintsResponse)
def summarize_retrieved_complaints(
    request: SummarizeComplaintsRequest,
) -> SummarizeComplaintsResponse:
    search = get_pgvector_complaint_search()
    complaints = search.search(query=request.query, top_k=request.top_k)

    summary, summary_source = summarize_complaints(
        query=request.query,
        complaints=complaints,
    )

    return SummarizeComplaintsResponse(
        query=request.query,
        summary=summary,
        summary_source=summary_source,
        complaints=complaints,
    )