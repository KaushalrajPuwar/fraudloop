"""FraudLoop scoring service.

A deliberately small application: one model, six endpoints, and structured
logs. The pipeline around it is the interesting part.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import Settings
from .logging_conf import configure_logging
from .model import FEATURES, ModelBundle, ModelNotFound, load_model
from .schemas import (
    Counters,
    ModelInfo,
    ScoreResponse,
    SecretInfo,
    StatsResponse,
    Transaction,
)
from .secret import Secret, load_secret

logger = logging.getLogger("fraudloop.scorer")

STATIC_DIR = Path(__file__).parent / "static"


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(round(0.95 * (len(ordered) - 1))), len(ordered) - 1)
    return round(ordered[index], 3)


def _feature_means(window: deque[dict[str, Any]]) -> dict[str, float]:
    if not window:
        return {}
    return {
        feature: round(sum(row[feature] for row in window) / len(window), 4)
        for feature in FEATURES
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application. Tests pass their own Settings."""
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        listener = configure_logging(
            level=config.log_level,
            logstash_host=config.logstash_host,
            logstash_port=config.logstash_port,
        )

        app.state.settings = config
        app.state.recent = deque(maxlen=config.stats_window)
        app.state.latencies = deque(maxlen=config.stats_window)
        app.state.scored = 0
        app.state.fraud = 0

        try:
            app.state.model = load_model(config.model_dir)
            logger.info(
                "model_loaded",
                extra={
                    "model_version": app.state.model.version,
                    "pr_auc": app.state.model.pr_auc,
                    "service_version": config.version,
                    "build": config.build_number,
                    "git_sha": config.git_sha,
                },
            )
        except ModelNotFound as exc:
            app.state.model = None
            logger.error("model_missing", extra={"error": str(exc), "model_dir": str(config.model_dir)})

        app.state.secret = load_secret(config)
        logger.info(
            "secret_loaded",
            extra={"source": app.state.secret.source, "fingerprint": app.state.secret.fingerprint},
        )
        logger.info(
            "service_started",
            extra={
                "service_version": config.version,
                "build": config.build_number,
                "git_sha": config.git_sha,
                "logstash": config.logstash_enabled,
            },
        )

        try:
            yield
        finally:
            if listener is not None:
                listener.stop()

    app = FastAPI(
        title="FraudLoop",
        description="Real-time transaction fraud scoring",
        version=config.version,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)

        if request.url.path not in ("/healthz", "/readyz", "/favicon.ico"):
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": elapsed_ms,
                    "client": request.client.host if request.client else "unknown",
                },
            )
        return response

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/healthz", summary="Liveness probe")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", summary="Readiness probe")
    async def readyz(request: Request):
        model = request.app.state.model
        if model is None:
            return JSONResponse(status_code=503, content={"status": "not ready", "reason": "model not loaded"})
        return {"status": "ready", "model_version": model.version}

    @app.post("/score", response_model=ScoreResponse, summary="Score one transaction")
    async def score(transaction: Transaction, request: Request) -> ScoreResponse:
        state = request.app.state
        model: ModelBundle | None = state.model
        if model is None:
            raise HTTPException(status_code=503, detail="model not loaded")

        started = time.perf_counter()
        txn_id = transaction.txn_id or f"txn_{uuid.uuid4().hex[:12]}"
        values = transaction.model_dump()

        probability = model.predict_proba(values)
        reasons = model.explain(values)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        threshold = model.threshold if model else config.fraud_threshold
        decision = "BLOCK" if probability >= threshold else "ALLOW"

        state.scored += 1
        if decision == "BLOCK":
            state.fraud += 1
        state.latencies.append(latency_ms)
        state.recent.append(
            {
                "txn_id": txn_id,
                "amount": values["amount"],
                "score": round(probability, 4),
                "decision": decision,
                "ts": time.time(),
                "reasons": reasons,
                **{feature: values[feature] for feature in FEATURES},
            }
        )

        secret: Secret = state.secret
        signature = hmac.new(
            secret.value.encode("utf-8"),
            f"{txn_id}:{probability:.6f}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        logger.info(
            "scored",
            extra={
                "txn_id": txn_id,
                "amount": values["amount"],
                "score": round(probability, 4),
                "decision": decision,
                "model_version": model.version,
                "latency_ms": latency_ms,
                "signature": signature,
            },
        )

        response = ScoreResponse(
            txn_id=txn_id,
            score=round(probability, 4),
            decision=decision,
            model_version=model.version,
            latency_ms=latency_ms,
            reasons=reasons,
        )
        return JSONResponse(
            content=response.model_dump(),
            headers={"X-Signature": signature},
        )

    @app.get("/stats", response_model=StatsResponse, summary="Live counters and feature means")
    async def stats(request: Request) -> StatsResponse:
        state = request.app.state
        model: ModelBundle | None = state.model
        secret: Secret = state.secret

        counters = Counters(
            scored=state.scored,
            fraud=state.fraud,
            fraud_rate=round(state.fraud / state.scored, 4) if state.scored else 0.0,
            p95_latency_ms=_p95(list(state.latencies)),
        )

        model_info = (
            ModelInfo(
                version=model.version,
                trained_at=model.trained_at,
                pr_auc=round(model.pr_auc, 4),
                roc_auc=round(model.roc_auc, 4),
                rows=model.rows,
                threshold=round(model.threshold, 4),
            )
            if model
            else None
        )

        # Newest first. `ts` must stay: the dashboard sorts and timestamps by it.
        recent = list(state.recent)[-config.recent_window:][::-1]

        return StatsResponse(
            version=config.version,
            build=config.build_number,
            git_sha=config.git_sha,
            pod=config.pod,
            model=model_info,
            secret=SecretInfo(source=secret.source, fingerprint=secret.fingerprint),
            counters=counters,
            feature_means=_feature_means(state.recent),
            recent=recent,
        )

    return app


app = create_app()
