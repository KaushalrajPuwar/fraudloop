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

    def predict_proba(self, values: dict[str, float]) -> float:
        """Score a single transaction. Returns the fraud probability."""
        row = pd.DataFrame([[float(values[name]) for name in FEATURES]], columns=FEATURES)
        return float(self.pipeline.predict_proba(row)[0][1])


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
