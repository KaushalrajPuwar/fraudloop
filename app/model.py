"""Loading and using the trained fraud model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

# Order matters: the pipeline was fitted on exactly this column order.
FEATURES = [
    "amount",
    "hour_of_day",
    "txn_count_24h",
    "avg_amount_30d",
    "distance_from_home_km",
    "is_foreign",
    "merchant_risk",
    "card_age_days",
]


class ModelNotFound(RuntimeError):
    """Raised when the artifacts directory has no usable model."""


@dataclass(frozen=True)
class ModelBundle:
    """A fitted pipeline plus the metadata written by the training job."""

    pipeline: Any
    meta: dict[str, Any]

    @property
    def version(self) -> str:
        return str(self.meta.get("version", "unknown"))

    @property
    def trained_at(self) -> str:
        return str(self.meta.get("trained_at", ""))

    @property
    def pr_auc(self) -> float:
        return float(self.meta.get("pr_auc", 0.0))

    @property
    def roc_auc(self) -> float:
        return float(self.meta.get("roc_auc", 0.0))

    @property
    def rows(self) -> int:
        return int(self.meta.get("rows", 0))

    @property
    def threshold(self) -> float:
        """Probability at or above which a transaction is blocked.

        Trained rather than fixed: class weighting inflates the probabilities,
        so the cut-off is chosen to reproduce the training base rate.
        """
        return float(self.meta.get("decision_threshold", 0.5))

    def predict_proba(self, values: dict[str, float]) -> float:
        """Score a single transaction. Returns the fraud probability."""
        row = self._row(values)
        return float(self.pipeline.predict_proba(row)[0][1])

    def explain(self, values: dict[str, float]) -> list[dict[str, object]]:
        """Every feature's contribution, largest absolute influence first.

        For a linear model the contribution of a feature is its coefficient
        times its scaled value, so this is exact rather than an approximation.
        All features are returned rather than a top-N slice: the caller decides
        which direction to show, because "why was this allowed" and "why was
        this blocked" need opposite ends of the list.
        """
        scaler = self.pipeline.named_steps["standardscaler"]
        classifier = self.pipeline.named_steps["logisticregression"]

        scaled = scaler.transform(self._row(values))[0]
        contributions = classifier.coef_[0] * scaled

        order = sorted(range(len(FEATURES)), key=lambda i: -abs(contributions[i]))
        return [
            {
                "feature": FEATURES[i],
                "value": round(float(values[FEATURES[i]]), 4),
                "contribution": round(float(contributions[i]), 3),
            }
            for i in order
        ]

    @staticmethod
    def _row(values: dict[str, float]) -> pd.DataFrame:
        return pd.DataFrame([[float(values[name]) for name in FEATURES]], columns=FEATURES)


def load_model(model_dir: Path) -> ModelBundle:
    """Load model.pkl and model_meta.json from *model_dir*.

    Raises ModelNotFound with an actionable message if either is missing, so a
    misconfigured deployment fails loudly instead of scoring nonsense.
    """
    model_path = model_dir / "model.pkl"
    meta_path = model_dir / "model_meta.json"

    missing = [str(p) for p in (model_path, meta_path) if not p.exists()]
    if missing:
        raise ModelNotFound(
            "model artifacts missing: "
            + ", ".join(missing)
            + " - run 'python ml/train.py' before starting the service"
        )

    pipeline = joblib.load(model_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return ModelBundle(pipeline=pipeline, meta=meta)
