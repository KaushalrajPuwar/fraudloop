#!/usr/bin/env bash
# End-to-end smoke test against a running scorer.
#
#   ./scripts/smoke.sh                        # against localhost:8000
#   ./scripts/smoke.sh http://fraudloop.localhost:8080
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
failures=0

check() {
  local name="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "$url" || echo "000")
  if [[ "$code" == "$expected" ]]; then
    printf '  ok    %-14s %s\n' "$name" "$code"
  else
    printf '  FAIL  %-14s got %s want %s\n' "$name" "$code" "$expected"
    failures=$((failures + 1))
  fi
}

echo "smoke testing $BASE_URL"

check "healthz" "${BASE_URL}/healthz"
check "readyz"  "${BASE_URL}/readyz"
check "stats"   "${BASE_URL}/stats"
check "dashboard" "${BASE_URL}/"

code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE_URL}/score" \
  -H 'Content-Type: application/json' \
  -d '{"amount":250.0,"hour_of_day":9,"txn_count_24h":3,"avg_amount_30d":120.0,
       "distance_from_home_km":12.0,"is_foreign":0,"merchant_risk":0.2,"card_age_days":800}')
if [[ "$code" == "200" ]]; then
  printf '  ok    %-14s %s\n' "score" "$code"
else
  printf '  FAIL  %-14s got %s want 200\n' "score" "$code"
  failures=$((failures + 1))
fi

if (( failures > 0 )); then
  echo "$failures check(s) failed"
  exit 1
fi

echo "all checks passed"
