from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

#from customer_voice_ai.agent.complaint_analysis_agent import get_complaint_analysis_agent
from customer_voice_ai.agent.langgraph_agent import run_complaint_graph
from customer_voice_ai.analytics import get_complaint_analytics
from customer_voice_ai.api.schemas import (
    AgentFeedbackRequest,
    AgentFeedbackResponse,
    AnalyzeComplaintRequest,
    AnalyzeComplaintResponse,
    ClassifyCommentRequest,
    ClassifyCommentResponse,
    ProductSummaryResponse,
    SearchComplaintsRequest,
    SearchComplaintsResponse,
)
from customer_voice_ai.db.repositories import AgentFeedbackRepository
from customer_voice_ai.db.session import get_db_session
from customer_voice_ai.ml.product_classifier import get_product_classifier
from customer_voice_ai.rag.local_search import get_complaint_search

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db_session)]

@router.post("/comments/classify", response_model=ClassifyCommentResponse)
def classify_comment(request: ClassifyCommentRequest) -> ClassifyCommentResponse:
    classifier = get_product_classifier()

    try:
        result = classifier.predict(
            text=request.text,
            top_k=request.top_k,
            confidence_threshold=request.confidence_threshold,
            )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ClassifyCommentResponse(**result)

@router.post("/search/complaints", response_model=SearchComplaintsResponse)
def search_complaints(request: SearchComplaintsRequest) -> SearchComplaintsResponse:
    search = get_complaint_search()

    try:
        results = search.search(query=request.query, top_k=request.top_k)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return SearchComplaintsResponse(results=results)

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