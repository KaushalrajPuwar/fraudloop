# CSE 816 Capstone — Requirements Analysis (Turn 1)

**Prepared:** 10-Nov-2026 · **Role:** orchestrator/scaffolding notes
**Sources:**
- `docs/SPE_Capstone_Project.md` — problem statement (Term I 2026-27), 285 lines
- `docs/FinalProjectGuidelinesAndEvaluationCriteria.pdf` — 2 pages, pure text, extracted with `pdftotext -layout` and visually verified against rendered PNGs

**Resolution rule (from the user):** on any conflict, **the PDF wins**.

---

## 1. Conflict register

| # | Topic | PDF (authoritative) | Markdown | Resolution |
|---|-------|--------------------|----------|------------|
| C1 | Total marks | **30** (20 + 3 + 2 + 5) | 25 (8-criterion table) | **30, PDF rubric** |
| C2 | Rubric shape | Working project 20 / Advanced 3 / Innovation 2 / Domain 5 | 8 stage-based criteria summing 25 | **PDF rubric** |
| C3 | Monitoring | **ELK Stack + Kibana** named twice, mandatory | Prometheus+Grafana default, alternatives allowed | **ELK mandatory**; Prometheus+Grafana added as bonus (non-conflicting) |
| C4 | CI/CD | **Jenkins** + "GitHub Hook Trigger for GITScm Polling" + Jenkins pipelines | Jenkins default, alternatives OK | **Jenkins** |
| C5 | Registry | **Push images to Docker Hub** (explicit, mandatory) | not specified | **Docker Hub** |
| C6 | Containerization | **Docker + Docker Compose** | Docker | **Docker + Compose** (Compose used for host-side stack) |
| C7 | Config mgmt | **Ansible Playbooks**, + "roles" for marks | Ansible default, Terraform/Helm/Crossplane OK | **Ansible with roles** |
| C8 | Domain | Domain-specific rewarded **+5**; generic web app does not earn it | Free choice, tracks are "inspiration" | **Domain-specific — both agree** |
| C9 | Infra | silent | Local cluster only (Minikube/kind/K3s), no paid cloud | **Local cluster** |
| C10 | Extension | "Innovation 2 marks" + "advanced features encouraged" | "cutting-edge extension required" | **Both — one capability, framed as innovation** |

**Non-conflicting additions from the markdown** (keep all of them): team of two, deliverables list, timeline/milestones, 60 idea catalogue, both-members Git history, live-demo-must-genuinely-run policy, individual viva.

---

## 2. Merged mandatory requirements (the actual checklist)

### A. Blocking / marks-bearing

| ID | Requirement | Source | Marks at risk |
|----|-------------|--------|---------------|
| R1 | Git + GitHub, **progressive commits from both members**, branches/PRs | PDF + MD | collaboration + viva |
| R2 | Jenkins pipeline triggered on push (GitHub hook trigger for GITScm polling) | PDF | 20 |
| R3 | Automated tests run in the pipeline | PDF | 20 |
| R4 | Docker image built and **pushed to Docker Hub** | PDF | 20 |
| R5 | Image **deployed to Kubernetes** automatically | PDF | 20 |
| R6 | Refresh the app → new change visible seamlessly | PDF | 20 |
| R7 | App logs → **ELK**; **Kibana dashboard** visualises them | PDF | 20 |
| R8 | **Ansible roles** (modular) | PDF | 3 |
| R9 | **HashiCorp Vault** for secrets | PDF | 3 |
| R10 | **Kubernetes HPA** | PDF | 3 |
| R11 | Domain-specific project (MLOps / AIOps / DevSecOps / Networking / Big Data / Healthcare / Finance) | PDF | 5 |
| R12 | Innovation / cutting-edge capability | PDF + MD | 2 |
| R13 | Live patching / zero-downtime update | PDF (encouraged) | 20 (R6) |
| R14 | Docker Compose used meaningfully | PDF | 20 (completeness) |
| R15 | Report 4–6 pp PDF, 1-page proposal, live demo, screen recording, signed contribution statement | MD | 2 + demo |

### B. Deliverables
1. Git repo with source, pipeline defs, IaC, K8s manifests
2. 1-page proposal (due **~11-Nov**) + 4–6 page final report PDF
3. Live end-to-end demo (push → build → deploy → observe)
4. Screen-recorded backup of a full pipeline run
5. Individual contribution statement, signed by both

---

## 3. Marks map — where the effort actually pays

| Bucket | Marks | Nature | Strategy |
|--------|-------|--------|----------|
| Working project | **20** (or 15 if "partially functional") | Binary cliff | **Reliability > ambition.** This is 67% of the grade and it is a 5-mark cliff. |
| Advanced features | 3 | Deterministic, enumerated | Vault + Ansible roles + HPA. Cheap. No excuses to miss. |
| Innovation | 2 | Judgement | One well-chosen capability, demoed live. |
| Domain-specific | 5 | Judgement | Pick from the PDF's named list. Highest-leverage single decision. |

**Key strategic read:** 23 of 30 marks are "do the baseline competently and reliably". Only 7 depend on taste. Therefore the engineering priority is a **reproducible, one-command, from-scratch bring-up** — not feature breadth. The PDF's own philosophy line and the markdown's "we assess DevOps engineering, not application complexity" both say the same thing.

---

## 4. Track filter — which tracks can earn the +5

The PDF names the qualifying domains explicitly. Mapping the markdown's 8 tracks:

| MD track | Qualifies for +5? | Verdict |
|----------|-------------------|---------|
| Full-stack web app | ✗ generic — explicitly excluded | **Avoid** |
| ML / MLOps | ✓ MLOps | **Strong** |
| AI / LLMOps | ~ AIOps only; LLMOps not named | Partial |
| Security / DevSecOps | ✓ DevSecOps | **Strong** |
| Networking / Service Mesh | ✓ Networking (NFV) | Strong but heavy |
| Deep Learning | ✓ MLOps-ish, but GPU on 8 GB laptop | **Avoid** |
| IoT / Edge | ✗ not named | Risky |
| Platform Engineering | ✗ not named | Risky (loses 5) |

**Double-credit combinations** (two named domains in one project): MLOps×Finance, MLOps×Healthcare, DevSecOps×Finance, AIOps×Big Data.

---

## 5. Recommended project

### Primary: **MLOps × Finance — Real-Time Transaction Fraud Scoring Platform**

Why this one:
- Hits **two** PDF-named domains (MLOps **and** Finance) → strongest possible claim on the 5 marks.
- The ML is deliberately trivial (sklearn logistic regression / gradient boosting on synthetic transactions) → the app is a vehicle, not the work.
- Synthetic data generated in-repo → **offline-safe, deterministic demo**, no Kaggle download on demo day.
- Naturally produces the telemetry the rubric wants: request latency, RPS, fraud rate, model version, drift.
- Natural HPA story (HTTP scoring service under load), natural Vault story (Docker Hub token, DB creds), natural zero-downtime story (2 replicas + rolling update).
- Natural innovation: **drift-triggered automated retraining** — closes the loop from production telemetry back into the CI/CD pipeline.

### Alternatives, ranked
2. **DevSecOps — Hardened CI/CD reference pipeline + supply chain** (MD ideas 27/28/29/31). The pipeline *is* the product; app intentionally trivial. Very on-brief for "DevOps showcase". Risk: a grader may read it as "not a domain project"; SonarQube is RAM-heavy.
3. **AIOps — self-healing platform** (anomaly detection on metrics → auto-remediation). AIOps is named; good innovation story; overlaps MLOps skills.
4. **Networking / NFV** — most infra-native, but Istio/Cilium + ELK + Jenkins on 8 GB is a resource fight. Deprioritise.
5. **Platform Engineering / Backstage** — best "wow", worst fit: not a named domain (loses 5) and Backstage is heavy. Deprioritise.

---

## 6. Target architecture (primary pick)

```
                     GitHub (2 devs, PRs, protected main)
                              │  webhook (gh webhook forward) / SCM poll
                              ▼
                    ┌──────────────────┐
   Ansible roles ──▶│     Jenkins      │  host Docker + Compose
   (provision +     │  Jenkinsfile     │
    configure)      └────────┬─────────┘
                              │ 1 lint+test  2 train+eval gate  3 docker build
                              │ 4 Trivy scan  5 push Docker Hub  6 bump GitOps tag
                              ▼
   ┌───────────────────────────────────────────────────────────┐
   │  K8s cluster (kind / k3d / K3s)   — local, arm64           │
   │                                                           │
   │  Argo CD ──syncs──▶ scorer (FastAPI, 2+ replicas, HPA)     │
   │                     │  rolling update, probes, PDB        │
   │                     ├── Postgres (transactions)           │
   │                     ├── retrain CronJob (drift check)     │
   │                     ├── metrics-server (HPA)              │
   │                     └── Vault (Docker Hub token, DB creds) │
   └───────────────────────────┬───────────────────────────────┘
                               │ structured JSON logs
                               ▼
   ┌───────────────────────────────────────────────────────────┐
   │  Observability — host Docker Compose                       │
   │  Filebeat/Fluent Bit → Logstash → Elasticsearch → Kibana   │
   │  Prometheus + Grafana (bonus: SLOs, HPA, model metrics)    │
   └───────────────────────────────────────────────────────────┘
```

**Separation of concerns:** Ansible provisions and configures; Jenkins builds and publishes; Argo CD deploys (GitOps). No hand-deploys anywhere.

---

## 7. Tool decisions and the justification line for each

| Stage | Tool | Justification (report-ready) |
|-------|------|------------------------------|
| SCM | GitHub + protected main + PRs | PDF default |
| CI/CD | Jenkins (Jenkinsfile, declarative) | PDF default; named explicitly |
| Trigger | GitHub webhook → "GitHub hook trigger for GITScm polling", SCM poll as fallback | PDF names this exact mechanism |
| Build | Docker multi-stage, non-root, pinned digests | PDF default |
| Local dev / host stack | Docker Compose | PDF names Compose |
| Registry | Docker Hub | PDF mandates it |
| IaC / config | Ansible with roles | PDF mandates Ansible; roles are a scored item |
| Orchestration | kind or k3d (K3s) | MD allows; arm64-friendly |
| Deploy | Argo CD (GitOps) | MD cutting-edge option; keeps Jenkins out of the deploy path |
| Secrets | HashiCorp Vault | PDF scored item |
| Scaling | HPA + metrics-server | PDF scored item |
| Logging | Elasticsearch + Logstash + Kibana | PDF mandates ELK |
| Metrics | Prometheus + Grafana | MD observability; bonus |
| Innovation | Drift-triggered automated retraining (+ Argo Rollouts canary if time) | PDF 2 marks |

---

## 8. Constraints and risks

| # | Risk | Evidence | Mitigation |
|---|------|----------|------------|
| X1 | **8 GB RAM** on the dev laptop | `hw.memsize = 8589934592`, 8 cores, arm64 | Strict resource diet; ELK + Jenkins on host Compose, not in-cluster; ES heap 512 MB; Logstash single worker; K8s node capped ~4 GB. **This is the #1 technical risk.** |
| X2 | **~22 GB free disk** | `df -h /` → 22 Gi avail | Prune images aggressively; cap K8s node disk; avoid SonarQube/MLflow server if tight |
| X3 | **~4 weeks to demo** | today 10-Nov; demo 07–12 Dec | Cut everything not tied to a mark. See §9. |
| X4 | **Proposal due ~11-Nov (tomorrow)** | MD milestone table | Draft immediately — this is the nearest deadline |
| X5 | Jenkins on localhost is unreachable from GitHub | — | `gh webhook forward` for the live demo; SCM polling (1 min) as fallback |
| X6 | arm64 image availability | Apple Silicon | All chosen tools publish arm64; pin versions and verify early |
| X7 | Docker daemon not running | `docker info` failed | Start Docker Desktop before any bring-up |
| X8 | Live demo must genuinely run | MD policy | Rehearse the full push→deploy→observe loop; keep the screen recording as backup |

---

## 9. Timeline against the official milestones

| Milestone | Target | Days left | Plan |
|-----------|--------|-----------|------|
| Kickoff & registration | 04-Nov-2026 | passed | Confirm done |
| **Proposal approved** | ~11-Nov-2026 | **~1 day** | Draft 1-page proposal now |
| Pipeline working | ~25-Nov-2026 | ~15 days | Jenkins → Docker Hub → K8s green end-to-end |
| Deployed + observable | ~02-Dec-2026 | ~22 days | ELK + Kibana dashboards live, HPA proven |
| Final briefing | 04-Dec-2026 | ~24 days | Dry-run the demo |
| Final demo & viva | 07–12 Dec-2026 | ~27–32 days | Rehearse, record backup |

**Scope discipline:** build in this order, each stage independently demoable —
1. K8s cluster + app + Docker + Compose (foundation)
2. Jenkins pipeline → Docker Hub → deploy (R2–R6, the 20 marks)
3. ELK + Kibana dashboards (R7)
4. Ansible roles + Vault + HPA (the 3 marks)
5. Domain model + training/eval gate (the 5 marks)
6. Innovation: drift-triggered retrain (the 2 marks)
7. Report + recording + rehearsal

If time runs short, cut from the bottom — never from 1–3.

---

## 10. Open decisions for the user

1. Confirm the **primary pick** (MLOps × Finance — fraud scoring) vs an alternative.
2. Confirm **kind vs k3d vs K3s** for the local cluster (recommend k3d: fastest bring-up, lowest RAM, good arm64 support).
3. Confirm whether a **second, higher-RAM machine** is available — this materially de-risks X1.
4. Confirm **Docker Hub account** ownership and whether both members have push rights.
5. Confirm **GitHub org/repo** name and that both members will commit from day 1 (collaboration marks + viva).
