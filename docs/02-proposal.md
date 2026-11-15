# Capstone Proposal — FraudLoop

**CSE 816 Software Production Engineering · Team of Two**
**Kaushalraj Puwar · Harsh Gupta**

---

## Application

FraudLoop is a real-time transaction fraud scoring service. A FastAPI endpoint accepts a
card transaction and returns a fraud probability and a BLOCK/ALLOW decision, using a
logistic regression model trained on synthetic transaction data.

The application is deliberately small: one container, six endpoints, roughly 450 lines of
code. It exists to produce the traffic, logs, and model artifacts that the pipeline needs
to demonstrate. **The pipeline is the subject of the project, not the application.**

## Architecture

```
GitHub ──webhook──▶ Jenkins (host, Docker Compose)
                       │ lint → test → train + quality gate → build → push → deploy
                       ▼
              Docker Hub  ─────────────────────────────┐
                                                       ▼
   k3d cluster (K3s, local)                    Deployment: scorer x2
     ├── HPA 2→6 on CPU                              │
     ├── Ingress  fraudloop.localhost                │
     ├── Vault  (policy-scoped token) ───────────────┘
     └── logging namespace
           Filebeat-free: app ships JSON over TCP
           Logstash → Elasticsearch → Kibana
```

## Tool choices and rationale

| Stage | Tool | Rationale |
|---|---|---|
| Source control | Git + GitHub | Course default; protected main, PR-based review |
| CI/CD | Jenkins (declarative pipeline) | Course default; runs on the host so the cluster stays small |
| Trigger | GitHub hook trigger for GITScm polling | The mechanism named in the guidelines |
| Build | Docker, multi-stage, non-root | Course default; builder/runtime split keeps dev dependencies out of the image |
| Registry | Docker Hub | Named explicitly in the guidelines |
| Configuration management | Ansible, four roles | Course default; roles provide the modularity the rubric rewards |
| Orchestration | Kubernetes on k3d (K3s) | Local-only requirement; k3d is the lightest option on an 8 GB laptop |
| Secrets | HashiCorp Vault | Scored advanced feature; policy-scoped token, never the root token |
| Autoscaling | Horizontal Pod Autoscaler | Scored advanced feature |
| Logging | Elasticsearch + Logstash + Kibana | Named explicitly in the guidelines |

## Cutting-edge extension

**Closed-loop retraining driven by production drift.** A scheduled Jenkins job compares the
live feature distribution against the training baseline using a mean absolute z-score.
When drift crosses the threshold it triggers the main pipeline, which retrains, re-runs the
quality gate, and redeploys — no human in the loop.

This is paired with a **model quality gate inside CI**: if the retrained model's PR-AUC
falls below 0.60, the build fails and nothing is deployed. Together they mean a bad model
cannot ship and a stale model cannot persist.

## Domain

MLOps × Finance — two of the domains the guidelines name as earning additional marks.

## Deliverables

Repository with source, pipeline definitions, IaC, and manifests; this proposal; a 4–6 page
final report; a live end-to-end demonstration; a screen-recorded backup; and a signed
individual contribution statement.
