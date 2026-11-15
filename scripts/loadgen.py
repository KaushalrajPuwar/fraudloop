"""Generate realistic traffic against the scoring API.

Used for three demos: driving the HPA, proving a rolling update drops no
requests, and shifting the feature distribution so the drift check fires.

    python scripts/loadgen.py --rate 20 --duration 60
    python scripts/loadgen.py --rate 20 --duration 60 --drift
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DEFAULT_URL = "http://localhost:8000"


def random_transaction(drift: bool = False) -> dict:
    """One plausible transaction. With --drift, amounts and distances inflate."""
    amount = min(max(random.lognormvariate(4.2, 0.9), 1.0), 5000.0)
    distance = random.expovariate(1 / 25.0)
    txn_count = random.randint(0, 8)

    if drift:
        amount *= 4.0
        distance *= 3.0
        txn_count = min(txn_count + 6, 30)

    return {
        "amount": round(amount, 2),
        "hour_of_day": random.randint(0, 23),
        "txn_count_24h": txn_count,
        "avg_amount_30d": round(amount * random.uniform(0.4, 1.6), 2),
        "distance_from_home_km": round(distance, 1),
        "is_foreign": 1 if random.random() < 0.08 else 0,
        "merchant_risk": round(random.betavariate(2, 5), 3),
        "card_age_days": random.randint(30, 3000),
    }


def post(url: str, payload: dict) -> int:
    request = urllib.request.Request(
        f"{url.rstrip('/')}/score",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Load-test the scoring API.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--rate", type=int, default=10, help="Requests per second")
    parser.add_argument("--duration", type=int, default=30, help="Seconds to run")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--drift", action="store_true", help="Shift the feature distribution")
    args = parser.parse_args()

    total = args.rate * args.duration
    interval = 1.0 / args.rate
    sent = 0
    ok = 0
    started = time.perf_counter()

    print(f"sending {total} requests to {args.url} at ~{args.rate}/s"
          f"{' (drift mode)' if args.drift else ''}")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = []
        for _ in range(total):
            futures.append(pool.submit(post, args.url, random_transaction(args.drift)))
            sent += 1
            target = started + sent * interval
            sleep_for = target - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)

        for future in futures:
            if future.result() == 200:
                ok += 1

    elapsed = time.perf_counter() - started
    print(f"sent {sent}  ok {ok}  failed {sent - ok}  "
          f"in {elapsed:.1f}s ({sent / elapsed:.1f}/s)")
    return 0 if ok == sent else 1


if __name__ == "__main__":
    raise SystemExit(main())
