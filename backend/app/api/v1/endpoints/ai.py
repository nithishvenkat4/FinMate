"""FastAPI Router for FinMate AI Intelligence Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ai.services.ai_service import AIService
from app.schemas.ai import (
    TransactionClassificationRequest,
    TransactionClassificationResponse,
    ExpenseForecastRequest,
    ExpenseForecastResponse,
    AnomalyCheckRequest,
    AnomalyCheckResponse,
    RAGRetrieveRequest,
    RAGRetrieveResponse,
    AIAskRequest,
    AIAskResponse,
    ModelRegistryResponse
)

router = APIRouter(prefix="/ai", tags=["AI Models & Intelligence"])


@router.post(
    "/classify-transaction",
    response_model=TransactionClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict transaction category using NLP and supervised ML"
)
def classify_transaction(
    payload: TransactionClassificationRequest,
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return service.classify_transaction(
        description=payload.description,
        amount=payload.amount,
        transaction_type=payload.transaction_type or "expense"
    )


@router.post(
    "/forecast-expenses",
    response_model=ExpenseForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate time-series monthly expense forecast with statistical uncertainty bounds"
)
def forecast_expenses(
    payload: ExpenseForecastRequest,
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return service.forecast_monthly_expenses(
        user_id=payload.user_id,
        recent_lags=payload.recent_lags,
        forecast_month=payload.forecast_month
    )


@router.post(
    "/anomaly-check",
    response_model=AnomalyCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check transaction for unusual spending patterns using Isolation Forest"
)
def anomaly_check(
    payload: AnomalyCheckRequest,
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return service.check_transaction_anomaly(
        amount=payload.amount,
        category=payload.category,
        is_weekend=payload.is_weekend or False
    )


@router.post(
    "/retrieve",
    response_model=RAGRetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve verified financial guidelines from RAG knowledge base"
)
def retrieve_knowledge(
    payload: RAGRetrieveRequest,
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return service.retrieve_guidance(
        query=payload.query,
        top_k=payload.top_k or 3
    )


@router.post(
    "/ask",
    response_model=AIAskResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-end AI Decision Support synthesizing deterministic facts, ML, RAG, and LLM"
)
async def ask_finmate(
    payload: AIAskRequest,
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return await service.ask_finmate(
        question=payload.question,
        user_id=payload.user_id,
        include_financial_context=payload.include_financial_context if payload.include_financial_context is not None else True
    )


@router.get(
    "/models",
    response_model=ModelRegistryResponse,
    status_code=status.HTTP_200_OK,
    summary="List all registered models, evaluated metrics, and benchmark comparisons"
)
def list_registered_models(
    db: Session = Depends(get_db)
):
    service = AIService(db=db)
    return service.get_registered_models()
