from pydantic import BaseModel, Field


class ClassifyCommentRequest(BaseModel):
    text: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    include_topic_matches: bool = True

class ClassPrediction(BaseModel):
    label: str
    score: float

class TopicMatch(BaseModel):
    topic_id: str
    name: str
    description: str | None = None
    source: str
    status: str
    score: float

class ClassifyCommentResponse(BaseModel):
    label: str
    score: float
    top_predictions: list[ClassPrediction]
    classification_status: str
    confidence_threshold: float
    topic_matches: list[TopicMatch] = []
    recommended_action: str
    topic_match_status: str

class SearchComplaintsRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ComplaintSearchResult(BaseModel):
    complaint_id: int | str
    date_received: str | None = None
    product: str | None = None
    issue: str | None = None
    company: str | None = None
    state: str | None = None
    consumer_complaint_narrative: str
    score: float


class SearchComplaintsResponse(BaseModel):
    results: list[ComplaintSearchResult]

class ProductCount(BaseModel):
    product: str
    count: int


class IssueCount(BaseModel):
    issue: str
    count: int


class MonthlyProductCount(BaseModel):
    month: str
    product: str
    count: int


class ProductSummaryResponse(BaseModel):
    total_rows: int
    top_products: list[ProductCount]
    top_issues_by_product: dict[str, list[IssueCount]]
    monthly_counts: list[MonthlyProductCount]

class AnalyzeComplaintRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class AnalyzeComplaintResponse(BaseModel):
    query: str
    answer: str
    answer_source: str
    classification: dict
    related_issues: list[IssueCount]
    similar_complaints: list[ComplaintSearchResult]

class AgentFeedbackRequest(BaseModel):
    query: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    answer_source: str | None = None
    classification_status: str | None = None


class AgentFeedbackResponse(BaseModel):
    feedback_id: str
    created_at: str
    query: str
    answer: str
    rating: int
    comment: str | None = None
    answer_source: str | None = None
    classification_status: str | None = None

class UncertainClassificationResponse(BaseModel):
    event_id: str
    created_at: str
    text: str
    predicted_label: str
    score: float
    confidence_threshold: float
    top_predictions: list[ClassPrediction]
    review_status: str
    assigned_label: str | None = None

class ReviewUncertainClassificationRequest(BaseModel):
    assigned_label: str = Field(min_length=1)

class TopicResponse(BaseModel):
    topic_id: str
    created_at: str
    updated_at: str
    name: str
    description: str | None = None
    source: str
    status: str

class CreateTopicRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    source: str = "manual"




class MatchTopicsRequest(BaseModel):
    text: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class MatchTopicsResponse(BaseModel):
    matches: list[TopicMatch]

class ClassificationRuntimeMetricsResponse(BaseModel):
    total_events: int
    classification_status_counts: dict[str, int]
    recommended_action_counts: dict[str, int]
    topic_match_status_counts: dict[str, int]