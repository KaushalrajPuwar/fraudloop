# fraudloop — Project Plan (lean, locked)

**Supersedes** `01-PROJECT-PLAN.md` v1 and §5–§10 of [00-REQUIREMENTS-ANALYSIS.md](00-REQUIREMENTS-ANALYSIS.md).
**Locked:** 15-Nov-2026 · **Demo window:** 07–12 Dec 2026

---

## 0. Mandatory vs. invented — the audit

### What the PDF actually requires

> **Project Expectations:** Version Control: Git and GitHub · CI/CD Automation: Jenkins, GitHub Hook Trigger for GITScm Polling, and Jenkins pipelines · Containerization: Docker and Docker Compose · Configuration Management: Ansible Playbooks · Orchestration and Scaling: Kubernetes (K8s) · Monitoring and Logging: ELK Stack (Elasticsearch, Logstash, and Kibana)

> **Mandatory:** (1) incremental git updates trigger Jenkins fetch+build, automated tests, push Docker images to Docker Hub, deploy to target system (2) refresh → changes visible seamlessly (3) app logs feed into ELK Stack, Kibana dashboard visualises them

> **Marks:** Working Project 20 · Advanced Features 3 — *"Usage of Vault, Roles in Ansible, and Kubernetes HPA"* · Innovation 2 · Domain-Specific 5

**That is the complete mandatory list. Six toolchain items, three advanced items, two scoring categories.**

### Full audit

| Item | Source | Status |
|---|---|---|
| Git + GitHub | PDF, explicit | **Required** |
| Jenkins + Jenkinsfile | PDF, explicit | **Required** |
| GitHub hook trigger for GITScm polling | PDF, explicit | **Required** |
| Docker | PDF, explicit | **Required** |
| Docker Compose | PDF, explicit | **Required** |
| Ansible **roles** | PDF marks, 3 pts | **Required** |
| Kubernetes (local) | PDF + MD | **Required** |
| Elasticsearch + Logstash + Kibana | PDF, named twice | **Required** |
| Docker Hub push | PDF, explicit | **Required** |
| Automated tests | PDF, explicit | **Required** |
| Vault | PDF marks, 3 pts | **Required** |
| HPA | PDF marks, 3 pts | **Required** |
| Domain-specific app | PDF marks, 5 pts | **Required** |
| One innovation | PDF marks, 2 pts | **Required** |
| | | |
| **k3d** | my choice (MD allows Minikube/kind/K3s) | **Keep** — it *is* the cluster, and the leanest option |
| **metrics-server** | k3s built-in, needed for HPA | **Keep** — free, already there |
| **Argo CD** | **my invention** | **CUT** |
| **Filebeat** | **my invention** | **CUT** |
| **Prometheus + Grafana** | **my invention** (MD rubric only; PDF never asks) | **CUT** |
| **Helm** | **my invention** | **CUT** |
| **Trivy** | **my invention** | **CUT** |
| **ServiceAccount / Vault injector** | **my invention** | **CUT** |

**Nothing cut loses a mark.** GitOps was one option in the MD's extension list — we take the MLOps closed-loop option instead, which is cheaper and fits the domain better.

---

## 1. Name

| | |
|---|---|
| **Project** | **FraudLoop** |
| **Repo** | `fraudloop` |
| **Tagline** | *Real-time transaction fraud scoring, with a closed-loop retraining pipeline* |
| **Namespace** | `fraudloop` |
| **Image** | `docker.io/<you>/fraudloop-scorer` |
| **Domain claim** | **MLOps × Finance** — two of the PDF's named domains |

---

## 2. Scope contract

### In scope — the entire application
- **One** Python container (FastAPI + scikit-learn)
- **One** HTML page, no framework, no build step
- **Two** JSON endpoints (`/score`, `/stats`) + health
- **One** sklearn model, trained in CI, **baked into the image**
- Synthetic data generated in-repo with a fixed seed

### OUT of scope
Database · MLflow · model registry · React/Node · message queue · auth system · drift microservice · microservices · GPU/DL · Helm · GitOps · service mesh

**Result: 1 container, 6 Kubernetes manifests, ~450 lines of application code.**

---

## 3. The application

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | HTML dashboard — the "refresh shows new changes" proof |
| POST | `/score` | `{transaction}` → `{score, decision, model_version}` |
| GET | `/stats` | Rolling-window feature means — consumed by the drift check |
| GET | `/healthz` / `/readyz` | Probes |

**Dashboard shows:** `fraudloop v0.1.0 · build #42 · a1b2c3d` (injected at build — this is how R6 is proven on camera) · counters · model version + PR-AUC · `Vault secret: sha256:ab12cd…` · last 20 transactions · "Score a random transaction" button.

**Every request emits one JSON log line** with `txn_id`, `amount`, `score`, `decision`, `latency_ms`, `model_version` — that is what makes the Kibana dashboards non-trivial.

---

## 4. Data & model

`ml/generate_data.py` writes 50,000 synthetic transactions, fixed seed. **No downloads, offline-safe on demo day.**

8 explainable features: `amount`, `hour_of_day`, `txn_count_24h`, `avg_amount_30d`, `distance_from_home_km`, `is_foreign`, `merchant_risk`, `card_age_days`.

Label = known weighted rule + 3% noise → PR-AUC ≈ 0.85, which gives the CI eval gate a meaningful threshold.

**Model version = image version.** No registry, no artifact store, no PVC.

---

## 5. Tech stack (final, lean)

| Stage | Tool | Where |
|---|---|---|
| SCM | GitHub, protected `main`, PRs | cloud |
| CI/CD | **Jenkins LTS** (Docker Compose) | **host** |
| Trigger | GitHub webhook (`gh webhook forward`), SCM poll fallback | — |
| Build | Docker BuildKit, multi-stage, non-root | host (socket) |
| Registry | **Docker Hub** | cloud |
| Compose | runs Jenkins on the host | host |
| IaC | **Ansible, 4 roles** | host |
| Cluster | **k3d** (K3s in Docker), 1 server + 1 agent | host |
| Deploy | **Jenkins → `kubectl set image` → rolling update** | host → cluster |
| Secrets | **Vault** (dev server, scoped read-only token) | cluster |
| Autoscale | **HPA** + k3s metrics-server | cluster |
| Logs | **Elasticsearch + Logstash + Kibana** | cluster |
| Log shipping | **app → Logstash over TCP JSON** (no Filebeat) | in-app |

**Third-party components: Jenkins, k3d, Ansible, Vault, ES, Logstash, Kibana. Seven. Six are named in the PDF.**

---

## 6. Architecture

```
  GitHub ──webhook──▶ Jenkins (host, Docker Compose)
  fraudloop            │
                       ├─ 1 checkout
                       ├─ 2 ruff + pytest
                       ├─ 3 generate data → train → EVAL GATE (PR-AUC ≥ 0.80)
                       ├─ 4 docker build (GIT_SHA / BUILD_NUM baked in)
                       ├─ 5 push → Docker Hub
                       └─ 6 kubectl set image → rollout status → smoke test
                                    │
                                    ▼
  ┌──────────── k3d cluster: fraudloop ────────────────────────┐
  │  Deployment scorer ×2  ──  HPA 2→6  ──  Ingress            │
  │        │                                                   │
  │        ├─ /score  /stats  /  /healthz                      │
  │        ├─ reads API key from Vault at startup              │
  │        └─ ships JSON logs over TCP ──▶ Logstash            │
  │                                            │               │
  │  Vault (1 pod)                             ▼               │
  │                              Elasticsearch ──▶ Kibana      │
  └────────────────────────────────────────────────────────────┘
                                    ▲
  scripts/loadgen.py ───────────────┘   (HPA + zero-downtime + drift demo)
```

**Three layers, no overlap:** Ansible provisions · Jenkins builds, publishes and deploys · the app is a vehicle.

---

## 7. Repository layout

```
fraudloop/
├── app/            main.py · model.py · schemas.py · logging_conf.py
│                   static/index.html · requirements.txt
├── ml/             generate_data.py · train.py · drift_check.py
├── tests/          test_api.py · test_model.py
├── docker/         Dockerfile · .dockerignore
├── k8s/            00-namespace · 10-configmap · 20-deployment
│                   30-service · 40-ingress · 50-hpa
├── ansible/        site.yml · inventory.ini · ansible.cfg
│                   roles/{cluster,jenkins,elk,vault}/
├── jenkins/        Jenkinsfile · Jenkinsfile.drift
├── compose/        docker-compose.yml   (Jenkins)
├── scripts/        loadgen.py · smoke.sh
├── docs/           00-REQUIREMENTS-ANALYSIS · 01-PROJECT-PLAN
│                   02-proposal · 03-runbook
└── README.md
```

~28 files, most under 60 lines.

---

## 8. Kubernetes footprint

**Six manifests, and that is the entire app.**

| Object | Notes |
|---|---|
| Namespace | `fraudloop` |
| ConfigMap | log level, thresholds, model version |
| Deployment | 2 replicas, `maxUnavailable: 0`, probes, resource limits |
| Service | ClusterIP :80 → :8000 |
| Ingress | `fraudloop.localhost` via k3d's built-in Traefik |
| HPA | 2 → 6, 60% CPU |

Vault's API-key secret is created by the Ansible `vault` role, not by a manifest.

---

## 9. Pipeline

| # | Stage | Catches |
|---|---|---|
| 1 | Checkout | — |
| 2 | ruff + pytest | broken code |
| 3 | generate data → train → **eval gate (PR-AUC ≥ 0.80)** | **model regression** |
| 4 | docker build | — |
| 5 | push → Docker Hub | — |
| 6 | `kubectl set image` → `rollout status` → smoke test | bad deploy |

**Second pipeline — `Jenkinsfile.drift`**, cron every 30 min: `GET /stats` → compare live feature means to the training baseline → if drift crosses threshold, trigger the main pipeline.

**That is the innovation (2 marks), and it needs zero extra infrastructure.** Production telemetry feeds back into CI; the model retrains and redeploys itself with no human in the loop. It is also what makes the MLOps domain claim real rather than cosmetic.

**Demo:** `loadgen.py --drift` shifts the `amount` distribution → drift trips → retrain fires → new build badge appears on refresh.

---

## 10. Phases & timeline

| Phase | Dates | Deliverable | Gate |
|---|---|---|---|
| **0** Setup | 15–16 Nov | Tools installed, Docker tuned | `k3d cluster list` |
| **1** App | 16–17 Nov | Runs locally via Compose | dashboard loads |
| **2** Cluster | 18–20 Nov | k3d + Ansible `cluster` role + 6 manifests | `curl fraudloop.localhost:8080` |
| **3** CI/CD | 21–23 Nov | Jenkins green end-to-end | **Milestone ~25-Nov** |
| **4** Observability | 24–26 Nov | Logstash pipeline + Kibana dashboards | logs visible in Kibana |
| **5** Advanced | 27–29 Nov | Vault + HPA + 4 Ansible roles | **Milestone ~02-Dec** |
| **6** Innovation | 30 Nov–2 Dec | Eval gate + drift-triggered retrain | drift fires a build |
| **7** Report | 3–4 Dec | Report draft, runbook | **Briefing 04-Dec** |
| **8** Rehearsal | 5–6 Dec | Dry run ×2, screen recording | clean |
| **9** Demo | 7–12 Dec | Live demo + viva | — |

**Rule:** if a phase slips, cut from the bottom. Never cut phases 1–3 — those are the 20 marks.

---

## 11. Install commands (yours to run)

```bash
# 1. Start Docker Desktop (installed, daemon stopped)
open -a Docker

# 2. Two packages. That is the whole list.
brew install k3d ansible

# 3. Python env
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" scikit-learn pandas numpy pytest httpx ruff
```

**Docker Desktop:** Settings → Resources → **Memory 4 GB**, CPUs 4, Disk 40 GB. (Down from 6 GB — the lean stack fits.)

```bash
# 4. Verify
docker info | head -3
k3d version && ansible --version | head -1

# 5. Cluster (Phase 2)
k3d cluster create fraudloop --servers 1 --agents 1 \
  --port "8080:80@loadbalancer" --port "8443:443@loadbalancer"
kubectl get nodes
```

*Optional, only if you want them:* `brew install vault ansible-lint` (Vault CLI for manual poking; Ansible handles init/seed either way).

---

## 12. Resource budget (8 GB host)

| Component | Where | Request | Limit |
|---|---|---|---|
| k3s system (Traefik, CoreDNS, metrics-server) | cluster | 300 Mi | 600 Mi |
| scorer ×2 | cluster | 100 Mi ea | 256 Mi ea |
| Vault | cluster | 100 Mi | 256 Mi |
| Elasticsearch | cluster | 512 Mi | 1 Gi |
| Logstash | cluster | 256 Mi | 512 Mi |
| Kibana | cluster | 256 Mi | 512 Mi |
| **cluster total** | | **~1.6 Gi** | **~3.4 Gi** |
| Jenkins | host Docker | 512 Mi | 1 Gi |

**Docker Desktop at 4 GB covers it.** Down from 6 GB in v1. Pod count drops from ~16 to **10**.

---

## 13. Risks

| # | Risk | Mitigation |
|---|---|---|
| X1 | 8 GB RAM | 4 GB Docker Desktop; pinned heaps; Jenkins on host; nothing else in-cluster |
| X2 | Logstash slow start (~90 s) | `-w 1`, `-Xmx256m`, single pipeline; start it before the demo |
| X3 | GitHub can't reach Jenkins on localhost | `gh webhook forward`; SCM polling (1 min) fallback |
| X4 | Vault dev mode is in-memory | Ansible re-seeds on every `site.yml` run; noted as a deliberate local simplification |
| X5 | "Live patching" ambiguity | Interpreted as zero-downtime rolling update; proven with loadgen showing 0 failed requests |
| X6 | App→Logstash TCP drops if Logstash is down | Non-blocking queue handler, drops silently; `kubectl logs` still works |

---

## 14. What I need from you

1. **Docker Hub username**
2. **GitHub owner** (personal account or org?)
3. Confirmation you'll run §11
