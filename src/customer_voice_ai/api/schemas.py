from pydantic import BaseModel, Field


class ClassifyCommentRequest(BaseModel):
    text: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)

class ClassPrediction(BaseModel):
    label: str
    score: float


class ClassifyCommentResponse(BaseModel):
    label: str
    score: float
    top_predictions: list[ClassPrediction]
    classification_status: str
    confidence_threshold: float

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
    classification: dict
    related_issues: list[IssueCount]
    similar_complaints: list[ComplaintSearchResult]