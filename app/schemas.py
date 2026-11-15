"""Request and response models for the scoring API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """One card transaction to be scored."""

    txn_id: str | None = Field(default=None, description="Client-supplied id; generated if absent")
    amount: float = Field(ge=0, le=100_000, description="Transaction amount")
    hour_of_day: int = Field(ge=0, le=23, description="Hour the transaction occurred")
    txn_count_24h: int = Field(ge=0, le=1000, description="Transactions on this card in 24h")
    avg_amount_30d: float = Field(ge=0, le=1_000_000, description="30-day average amount")
    distance_from_home_km: float = Field(ge=0, le=50_000, description="Distance from home")
    is_foreign: int = Field(ge=0, le=1, description="1 if the merchant is foreign")
    merchant_risk: float = Field(ge=0, le=1, description="Merchant risk score 0-1")
    card_age_days: int = Field(ge=0, le=50_000, description="Age of the card in days")


class Reason(BaseModel):
    """One feature's contribution to a prediction."""

    feature: str
    value: float
    contribution: float = Field(description="Positive pushes toward fraud")


class ScoreResponse(BaseModel):
    """The model's verdict on one transaction."""

    txn_id: str
    score: float = Field(description="Fraud probability, 0-1")
    decision: str = Field(description="BLOCK or ALLOW")
    model_version: str
    latency_ms: float
    reasons: list[Reason] = Field(default_factory=list)


class ModelInfo(BaseModel):
    version: str
    trained_at: str
    pr_auc: float
    roc_auc: float
    rows: int


class SecretInfo(BaseModel):
    source: str = Field(description="vault, env, or generated")
    fingerprint: str = Field(description="First 12 chars of the secret's SHA-256")


class Counters(BaseModel):
    scored: int
    fraud: int
    fraud_rate: float
    p95_latency_ms: float


class StatsResponse(BaseModel):
    version: str
    build: str
    git_sha: str
    pod: str = Field(description="Replica that served this response")
    model: ModelInfo | None
    secret: SecretInfo
    counters: Counters
    feature_means: dict[str, float]
    recent: list[dict]
