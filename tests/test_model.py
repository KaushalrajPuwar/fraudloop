"""Model loading and prediction tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.model import FEATURES, ModelNotFound, load_model


def test_model_loads_with_metadata(model_dir: Path) -> None:
    bundle = load_model(model_dir)
    assert bundle.version == "m-test"
    assert bundle.rows > 0
    assert 0.0 <= bundle.pr_auc <= 1.0


def test_predictions_are_probabilities(model_dir: Path) -> None:
    bundle = load_model(model_dir)
    score = bundle.predict_proba({name: 1.0 for name in FEATURES})
    assert 0.0 <= score <= 1.0


def test_missing_artifacts_raise(tmp_path: Path) -> None:
    with pytest.raises(ModelNotFound, match="model artifacts missing"):
        load_model(tmp_path)


def test_high_risk_transaction_scores_above_low_risk(model_dir: Path) -> None:
    bundle = load_model(model_dir)

    low_risk = {
        "amount": 12.0, "hour_of_day": 12, "txn_count_24h": 1, "avg_amount_30d": 15.0,
        "distance_from_home_km": 1.0, "is_foreign": 0, "merchant_risk": 0.05,
        "card_age_days": 2500,
    }
    high_risk = {
        "amount": 2400.0, "hour_of_day": 3, "txn_count_24h": 18, "avg_amount_30d": 40.0,
        "distance_from_home_km": 420.0, "is_foreign": 1, "merchant_risk": 0.92,
        "card_age_days": 45,
    }

    assert bundle.predict_proba(high_risk) > bundle.predict_proba(low_risk)
