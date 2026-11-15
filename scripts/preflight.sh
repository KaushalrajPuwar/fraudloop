#!/usr/bin/env bash
# Preflight check for FraudLoop.
#
# Verifies this machine can run the full stack before you spend time on the
# playbook. Run from the repository root:
#
#   ./scripts/preflight.sh
#
# Exit code 0 means every hard requirement is met. Warnings do not fail.

set -uo pipefail

pass=0
fail=0
warn=0

ok()   { printf '  \033[32m ok \033[0m  %s\n' "$1"; pass=$((pass + 1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fail=$((fail + 1)); }
note() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; warn=$((warn + 1)); }
section() { printf '\n%s\n' "$1"; }

have() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------- tooling ---
section 'Tooling'

for tool in docker k3d kubectl ansible ansible-playbook python3 git; do
  if have "$tool"; then
    ok "$tool"
  else
    case "$tool" in
      k3d)     bad "k3d missing        -> brew install k3d   |  curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash" ;;
      ansible) bad "ansible missing    -> brew install ansible  |  pipx install --include-deps ansible" ;;
      kubectl) bad "kubectl missing    -> brew install kubectl |  https://kubernetes.io/docs/tasks/tools/" ;;
      docker)  bad "docker missing     -> install Docker Desktop" ;;
      *)       bad "$tool missing" ;;
    esac
  fi
done

# ------------------------------------------------------------------ docker ---
section 'Docker'

if have docker && docker info >/dev/null 2>&1; then
  ok 'daemon is running'

  mem_bytes=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  mem_gib=$(awk -v b="$mem_bytes" 'BEGIN { printf "%.1f", b / 1073741824 }')
  if awk -v m="$mem_gib" 'BEGIN { exit !(m >= 4.0) }'; then
    ok "VM memory ${mem_gib} GiB (need >= 4.0)"
  else
    bad "VM memory ${mem_gib} GiB - raise Docker Desktop memory to 4.5 GB"
  fi

  cpus=$(docker info --format '{{.NCPU}}' 2>/dev/null || echo 0)
  if [ "${cpus:-0}" -ge 4 ]; then
    ok "VM cpus $cpus (need >= 4)"
  else
    note "VM cpus $cpus - 4 or more is recommended"
  fi
else
  bad 'docker daemon is not running - start Docker Desktop'
fi

# ------------------------------------------------------------------ python ---
section 'Python'

if have python3; then
  version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    ok "python ${version} (need >= 3.11)"
  else
    bad "python ${version} - need 3.11 or newer"
  fi
else
  bad 'python3 missing'
fi

if [ -x .venv/bin/python ]; then
  ok '.venv exists'
  if .venv/bin/python -c 'import fastapi, sklearn, pandas' >/dev/null 2>&1; then
    ok 'runtime dependencies installed'
  else
    bad 'dependencies missing - run: pip install -r requirements-dev.txt'
  fi
else
  bad '.venv missing - run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt'
fi

# ------------------------------------------------------------------ memory ---
section 'Host resources'

if [ "$(uname -s)" = 'Darwin' ]; then
  host_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
else
  host_bytes=$(awk '/MemTotal/ { print $2 * 1024 }' /proc/meminfo 2>/dev/null || echo 0)
fi
host_gib=$(awk -v b="$host_bytes" 'BEGIN { printf "%.1f", b / 1073741824 }')

if awk -v m="$host_gib" 'BEGIN { exit !(m >= 15.0) }'; then
  ok "host memory ${host_gib} GiB"
elif awk -v m="$host_gib" 'BEGIN { exit !(m >= 7.5) }'; then
  note "host memory ${host_gib} GiB - workable but tight; close other applications during the demo"
else
  bad "host memory ${host_gib} GiB - 8 GiB is the practical minimum"
fi

avail_kb=$(df -Pk . 2>/dev/null | awk 'NR==2 { print $4 }')
avail_gib=$(awk -v k="${avail_kb:-0}" 'BEGIN { printf "%.1f", k / 1048576 }')
if awk -v g="$avail_gib" 'BEGIN { exit !(g >= 20) }'; then
  ok "free disk ${avail_gib} GiB (need >= 20)"
else
  bad "free disk ${avail_gib} GiB - need at least 20 GiB for images"
fi

# ------------------------------------------------------------------- ports ---
section 'Ports'

port_busy() {
  if have lsof; then
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1 && exec 3<&- && return 0 || return 1
  fi
}

for entry in "8080:application ingress" "8090:Jenkins" "5601:Kibana" "9200:Elasticsearch" "8200:Vault"; do
  port="${entry%%:*}"
  label="${entry#*:}"
  if port_busy "$port"; then
    note "port $port in use ($label) - fine if it is already us"
  else
    ok "port $port free ($label)"
  fi
done

# ------------------------------------------------------------------ cluster ---
section 'Cluster'

if have k3d && k3d cluster list --no-headers 2>/dev/null | grep -q '^fraudloop'; then
  ok 'k3d cluster "fraudloop" exists'
  if kubectl get nodes --no-headers 2>/dev/null | grep -q Ready; then
    ready=$(kubectl get nodes --no-headers 2>/dev/null | grep -c Ready)
    ok "kubectl can reach the cluster ($ready node(s) ready)"
  else
    bad 'cluster exists but kubectl cannot reach it - check KUBECONFIG'
  fi
else
  note 'no "fraudloop" cluster yet - ansible-playbook ansible/site.yml will create it'
fi

# ------------------------------------------------------------------ summary ---
printf '\n%s\n' '----------------------------------------'
printf 'passed %d   warnings %d   failed %d\n' "$pass" "$warn" "$fail"

if [ "$fail" -gt 0 ]; then
  printf '\nResolve the FAIL lines above, then run this again.\n'
  exit 1
fi

printf '\nReady. Next: ansible-playbook ansible/site.yml\n'
