"""Shared fixtures: a small trained model and a test client."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.config import Settings
from app.main import create_app
from app.model import FEATURES
from ml.generate_data import generate


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A real, small model so tests exercise the same code path as production."""
    directory = tmp_path_factory.mktemp("artifacts")
    frame = generate(rows=3000, seed=7)

    pipeline = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    )
    pipeline.fit(frame[FEATURES], frame["is_fraud"])
    joblib.dump(pipeline, directory / "model.pkl")

    meta = {
        "version": "m-test",
        "trained_at": "2026-01-01T00:00:00+00:00",
        "pr_auc": 0.7,
        "roc_auc": 0.9,
        "rows": len(frame),
        "features": FEATURES,
        "baseline_means": {name: float(frame[name].mean()) for name in FEATURES},
        "baseline_stds": {name: float(frame[name].std()) for name in FEATURES},
    }
    (directory / "model_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return directory


@pytest.fixture
def client(model_dir: Path) -> TestClient:
    settings = Settings(model_dir=model_dir, log_level="WARNING", fallback_api_key="test-key")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def transaction() -> dict:
    return {
        "amount": 120.5,
        "hour_of_day": 14,
        "txn_count_24h": 2,
        "avg_amount_30d": 95.0,
        "distance_from_home_km": 3.2,
        "is_foreign": 0,
        "merchant_risk": 0.12,
        "card_age_days": 900,
    }
