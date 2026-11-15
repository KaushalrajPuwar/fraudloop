"""Generate the synthetic transaction dataset used to train the fraud model.

Deterministic: the same seed always produces the same file, so the pipeline
never needs to download anything and the demo works offline.

Usage:
    python ml/generate_data.py                 # 50,000 rows -> data/transactions.csv
    python ml/generate_data.py --rows 1000     # smaller file
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DEFAULT_ROWS = 50_000
DEFAULT_OUT = Path("data/transactions.csv")

# How strongly each signal pushes a transaction toward "fraud".
WEIGHTS = {
    "amount": 0.9,
    "txn_count_24h": 0.7,
    "distance": 0.8,
    "is_foreign": 0.6,
    "merchant_risk": 1.2,
    "card_age": -0.5,
}

FRAUD_RATE = 0.02          # ~2% of transactions are fraudulent
NOISE_POS_TO_NEG = 0.01    # 1% of real frauds look clean
NOISE_NEG_TO_POS = 0.0005  # 0.05% of clean transactions look odd


def _zscore(values: np.ndarray) -> np.ndarray:
    return (values - values.mean()) / (values.std() + 1e-9)


def generate(rows: int = DEFAULT_ROWS, seed: int = SEED) -> pd.DataFrame:
    """Build a transactions table with a learnable (but imperfect) fraud label."""
    rng = np.random.default_rng(seed)

    # --- raw signals -------------------------------------------------------
    amount = np.round(rng.lognormal(mean=4.2, sigma=0.9, size=rows), 2).clip(1, 5000)
    hour_of_day = rng.integers(0, 24, size=rows)
    txn_count_24h = rng.poisson(3.0, size=rows).clip(0, 30)
    avg_amount_30d = np.round(amount * rng.uniform(0.4, 1.6, size=rows), 2)
    distance_km = np.round(
        np.clip(rng.exponential(scale=25.0, size=rows), 0, 500), 1
    )
    is_foreign = (rng.random(rows) < 0.08).astype(int)
    merchant_risk = np.round(rng.beta(2, 5, size=rows), 3)
    card_age_days = rng.integers(30, 3000, size=rows)

    # --- risk score -> label ----------------------------------------------
    risk = (
        WEIGHTS["amount"] * _zscore(np.log1p(amount))
        + WEIGHTS["txn_count_24h"] * _zscore(txn_count_24h)
        + WEIGHTS["distance"] * _zscore(np.log1p(distance_km))
        + WEIGHTS["is_foreign"] * is_foreign
        + WEIGHTS["merchant_risk"] * _zscore(merchant_risk)
        + WEIGHTS["card_age"] * _zscore(np.log1p(card_age_days))
    )
    probability = 1.0 / (1.0 + np.exp(-risk))
    cutoff = np.quantile(probability, 1.0 - FRAUD_RATE)
    is_fraud = probability >= cutoff

    # Label noise so the problem is realistic rather than perfectly separable.
    flip_pos = is_fraud & (rng.random(rows) < NOISE_POS_TO_NEG)
    flip_neg = ~is_fraud & (rng.random(rows) < NOISE_NEG_TO_POS)
    is_fraud = is_fraud ^ flip_pos ^ flip_neg

    # --- assemble ----------------------------------------------------------
    start = np.datetime64("2026-10-01T00:00:00")
    offsets = rng.integers(0, 30 * 24 * 3600, size=rows)
    timestamps = start + offsets.astype("timedelta64[s]")

    frame = pd.DataFrame(
        {
            "txn_id": [f"txn_{i:07d}" for i in range(rows)],
            "timestamp": timestamps,
            "amount": amount,
            "hour_of_day": hour_of_day,
            "txn_count_24h": txn_count_24h,
            "avg_amount_30d": avg_amount_30d,
            "distance_from_home_km": distance_km,
            "is_foreign": is_foreign,
            "merchant_risk": merchant_risk,
            "card_age_days": card_age_days,
            "is_fraud": is_fraud.astype(int),
        }
    )
    return frame.sort_values("timestamp").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fraud data.")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    frame = generate(rows=args.rows, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)

    fraud = int(frame["is_fraud"].sum())
    print(f"wrote {args.out}  rows={len(frame):,}  fraud={fraud:,} "
          f"({fraud / len(frame):.2%})")


if __name__ == "__main__":
    main()
