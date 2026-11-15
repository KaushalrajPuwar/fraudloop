"""Compare live feature distributions against the training baseline.

Run on a schedule by Jenkins. Exit code 2 means drift was detected and the
main pipeline should be triggered to retrain and redeploy.

    exit 0  no drift
    exit 2  drift detected
    exit 3  could not reach the scorer (not a drift signal)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

DEFAULT_URL = os.environ.get("SCORER_URL", "http://localhost:8000")
DEFAULT_META = Path("artifacts/model_meta.json")
DEFAULT_THRESHOLD = 0.50  # mean absolute z-score across features


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect feature drift in production.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the scorer")
    parser.add_argument("--meta", type=Path, default=DEFAULT_META)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    if not args.meta.exists():
        print(f"no baseline at {args.meta}", file=sys.stderr)
        return 3

    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    features = meta["features"]
    baseline_means = meta["baseline_means"]
    baseline_stds = meta["baseline_stds"]

    try:
        response = httpx.get(f"{args.url.rstrip('/')}/stats", timeout=10.0)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"could not reach scorer at {args.url}: {exc}", file=sys.stderr)
        return 3

    live_means = response.json().get("feature_means") or {}
    if not live_means:
        print("no live traffic yet - nothing to compare")
        return 0

    print(f"{'feature':<24}{'baseline':>12}{'live':>12}{'z':>9}")
    z_scores: list[float] = []
    for name in features:
        if name not in live_means:
            continue
        baseline = float(baseline_means[name])
        std = float(baseline_stds[name]) or 1.0
        live = float(live_means[name])
        z = abs(live - baseline) / std
        z_scores.append(z)
        print(f"{name:<24}{baseline:>12.4f}{live:>12.4f}{z:>9.3f}")

    if not z_scores:
        print("no overlapping features - nothing to compare")
        return 0

    drift = sum(z_scores) / len(z_scores)
    print(f"\nmean |z| = {drift:.4f}   threshold = {args.threshold:.2f}")

    if drift > args.threshold:
        print("DRIFT DETECTED - retraining recommended")
        return 2

    print("OK - distribution within tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
