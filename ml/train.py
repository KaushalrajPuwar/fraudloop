"""Train the fraud model and enforce the quality gate.

This is the stage that makes the pipeline an MLOps pipeline rather than just a
CI pipeline: if the freshly trained model is worse than the quality bar, the
build fails and nothing gets deployed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Allow "python ml/train.py" from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from app.model import FEATURES  # noqa: E402
from ml.generate_data import generate  # noqa: E402

DEFAULT_DATA = Path("data/transactions.csv")
DEFAULT_OUT = Path("artifacts")
DEFAULT_MIN_PR_AUC = 0.60


def _load_frame(data_path: Path, rows: int) -> pd.DataFrame:
    if data_path.exists():
        return pd.read_csv(data_path)
    print(f"{data_path} not found, generating {rows:,} rows")
    frame = generate(rows=rows)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(data_path, index=False)
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the fraud model.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument(
        "--min-pr-auc",
        type=float,
        default=float(os.environ.get("MIN_PR_AUC", DEFAULT_MIN_PR_AUC)),
        help="Quality gate. The build fails below this PR-AUC.",
    )
    args = parser.parse_args()

    frame = _load_frame(args.data, args.rows)
    missing = [name for name in FEATURES if name not in frame.columns]
    if missing:
        print(f"dataset is missing required columns: {missing}", file=sys.stderr)
        return 2

    features = frame[FEATURES]
    labels = frame["is_fraud"]

    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=args.test_size, random_state=42, stratify=labels
    )

    pipeline = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    )
    pipeline.fit(x_train, y_train)

    probabilities = pipeline.predict_proba(x_test)[:, 1]
    pr_auc = float(average_precision_score(y_test, probabilities))
    roc_auc = float(roc_auc_score(y_test, probabilities))

    build = os.environ.get("BUILD_NUMBER", "")
    version = f"m-{build}" if build else f"m-{datetime.now(UTC):%Y%m%d%H%M%S}"

    args.out.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.out / "model.pkl")

    meta = {
        "version": version,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "rows": int(len(frame)),
        "features": FEATURES,
        "fraud_rate": round(float(frame["is_fraud"].mean()), 4),
        "baseline_means": {name: round(float(features[name].mean()), 4) for name in FEATURES},
        "baseline_stds": {name: round(float(features[name].std()), 4) for name in FEATURES},
    }
    (args.out / "model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (args.out / "metrics.json").write_text(
        json.dumps({"version": version, "pr_auc": pr_auc, "roc_auc": roc_auc}, indent=2),
        encoding="utf-8",
    )

    print(f"model      {version}")
    print(f"rows       {len(frame):,}")
    print(f"PR-AUC     {pr_auc:.4f}")
    print(f"ROC-AUC    {roc_auc:.4f}")
    print(f"gate       >= {args.min_pr_auc:.2f}")

    if pr_auc < args.min_pr_auc:
        print(
            f"\nQUALITY GATE FAILED: PR-AUC {pr_auc:.4f} is below the "
            f"{args.min_pr_auc:.2f} threshold.",
            file=sys.stderr,
        )
        return 1

    print("\nquality gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
