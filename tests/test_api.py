"""API contract tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_model(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["model_version"] == "m-test"


def test_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "FraudLoop" in response.text


def test_score_returns_a_decision(client: TestClient, transaction: dict) -> None:
    response = client.post("/score", json=transaction)
    assert response.status_code == 200

    body = response.json()
    assert 0.0 <= body["score"] <= 1.0
    assert body["decision"] in {"BLOCK", "ALLOW"}
    assert body["model_version"] == "m-test"
    assert body["txn_id"].startswith("txn_")


def test_score_signs_the_response(client: TestClient, transaction: dict) -> None:
    response = client.post("/score", json=transaction)
    signature = response.headers.get("X-Signature")
    assert signature is not None
    assert len(signature) == 16


def test_score_echoes_a_supplied_id(client: TestClient, transaction: dict) -> None:
    response = client.post("/score", json={**transaction, "txn_id": "txn_custom"})
    assert response.json()["txn_id"] == "txn_custom"


def test_score_rejects_out_of_range_input(client: TestClient, transaction: dict) -> None:
    response = client.post("/score", json={**transaction, "hour_of_day": 99})
    assert response.status_code == 422


def test_score_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/score", json={"amount": 10.0})
    assert response.status_code == 422


def test_stats_tracks_scored_transactions(client: TestClient, transaction: dict) -> None:
    before = client.get("/stats").json()["counters"]["scored"]
    client.post("/score", json=transaction)
    client.post("/score", json=transaction)

    stats = client.get("/stats").json()
    assert stats["counters"]["scored"] == before + 2
    assert stats["model"]["version"] == "m-test"
    assert stats["secret"]["source"] == "env"
    assert len(stats["secret"]["fingerprint"]) == 12
    assert set(stats["feature_means"]) == {
        "amount", "hour_of_day", "txn_count_24h", "avg_amount_30d",
        "distance_from_home_km", "is_foreign", "merchant_risk", "card_age_days",
    }


def test_stats_lists_recent_transactions(client: TestClient, transaction: dict) -> None:
    client.post("/score", json={**transaction, "txn_id": "txn_recent"})
    recent = client.get("/stats").json()["recent"]
    assert any(row["txn_id"] == "txn_recent" for row in recent)
