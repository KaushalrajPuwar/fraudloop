# FraudLoop

**Real-time transaction fraud scoring, with a closed-loop MLOps pipeline.**

FraudLoop is a deliberately small fraud-scoring service wrapped in a complete, automated
DevOps pipeline. The application is a vehicle — the pipeline is the point.

```
git push  ->  Jenkins  ->  tests  ->  train + eval gate  ->  Docker image
                                                          ->  Docker Hub
                                                          ->  Kubernetes
                                                          ->  Kibana
```

## What it does

A FastAPI service scores transactions for fraud risk in real time. Every request emits a
structured JSON log line that flows into the ELK stack. A scheduled Jenkins job watches the
live feature distribution, and when it drifts far enough from the training baseline it
triggers the pipeline to retrain and redeploy — with no human in the loop.

## Stack

| Stage | Tool |
|---|---|
| Source control | GitHub (protected `main`, PRs) |
| CI/CD | Jenkins (declarative pipeline) |
| Build | Docker (multi-stage, non-root) |
| Registry | Docker Hub |
| Config management | Ansible (roles) |
| Orchestration | Kubernetes on k3d (K3s) |
| Secrets | HashiCorp Vault |
| Autoscaling | Horizontal Pod Autoscaler |
| Logging | Elasticsearch · Logstash · Kibana |
| App | FastAPI · scikit-learn |

## Quick start

```bash
# 1. Environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate the dataset (deterministic, no downloads)
python ml/generate_data.py

# 3. Run the tests
pytest

# 4. Cluster
k3d cluster create fraudloop --servers 1 --agents 1 \
  --port "8080:80@loadbalancer" --port "8443:443@loadbalancer"
```

## Repository layout

```
app/        FastAPI service, model loader, structured logging, dashboard
ml/         data generator, training, drift check
tests/      unit and API tests
docker/     Dockerfile
k8s/        Kubernetes manifests
ansible/    provisioning roles (cluster, jenkins, elk, vault)
jenkins/    Jenkinsfile and drift pipeline
compose/    Docker Compose for the host-side Jenkins
scripts/    load generator, smoke test
docs/       requirements analysis, project plan, runbook
```

## Dataset

Fully synthetic and generated in-repo with a fixed seed — no downloads, so the demo works
offline. 50,000 transactions, 8 features, ~2% fraud rate, PR-AUC ≈ 0.73 with logistic
regression.

```bash
python ml/generate_data.py --rows 50000
```

## Team

- Kaushalraj Puwar
- Harsh Gupta

## License

MIT
