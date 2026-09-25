"""Pydantic Request and Response Schemas for FinMate AI Endpoints."""

from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


# 1. Transaction Classification
class TransactionClassificationRequest(BaseModel):
    description: str = Field(..., min_length=1, description="Transaction memo or merchant name")
    amount: Optional[Decimal] = Field(default=None, ge=0, description="Optional transaction amount")
    transaction_type: Optional[str] = Field(default="expense", description="income or expense")


class TransactionClassificationResponse(BaseModel):
    predicted_category: str
    confidence: float
    requires_user_confirmation: bool
    contributing_tokens: List[str]
    model_version: str
    confidence_threshold: float


# 2. Expense Forecasting
class ExpenseForecastRequest(BaseModel):
    user_id: Optional[uuid.UUID] = None
    recent_lags: Optional[List[float]] = None
    forecast_month: Optional[int] = Field(default=None, ge=1, le=12)


class ExpenseForecastResponse(BaseModel):
    predicted_expense: Optional[float]
    uncertainty_range: Optional[Dict[str, Any]] = None
    features_used: Optional[Dict[str, Any]] = None
    model_version: str
    limitation_notice: str


# 3. Anomaly Detection
class AnomalyCheckRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    category: str
    is_weekend: Optional[bool] = False


class AnomalyCheckResponse(BaseModel):
    is_unusual: bool
    anomaly_score: float
    category: str
    amount: float
    ratio_to_benchmark: float
    explanation: str
    classification_notice: str


# 4. RAG Retrieval
class RAGRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)


class RAGRetrieveResponse(BaseModel):
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    has_sufficient_evidence: bool
    notice: Optional[str] = None


# 5. AI Question Answering ("Ask FinMate")
class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    user_id: Optional[uuid.UUID] = None
    include_financial_context: Optional[bool] = True


class AIAskResponse(BaseModel):
    question: str
    deterministic_facts: Dict[str, Any]
    ml_forecast: Optional[Dict[str, Any]] = None
    rag_sources: List[Dict[str, Any]] = []
    ai_decision_support: Dict[str, Any]
    safety_notice: str


# 6. Model Metadata
class ModelEntry(BaseModel):
    task: str
    model_name: str
    version: str
    algorithm: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    is_selected: bool
    is_baseline: bool
    notes: Optional[str] = None
    registered_at: str


class ModelRegistryResponse(BaseModel):
    models: List[ModelEntry]
    last_updated: Optional[str] = None
