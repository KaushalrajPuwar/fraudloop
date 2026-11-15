# FraudLoop

**Real-time transaction fraud scoring, wrapped in a complete delivery pipeline.**

FraudLoop is a deliberately small fraud-scoring service. The application is a vehicle; the
pipeline around it is the point of the project.

```
git push → Jenkins → lint → test → train + quality gate → Docker image
                                                       → Docker Hub
                                                       → Kubernetes
                                                       → Kibana
```

## What it does

A FastAPI service scores card transactions for fraud risk in real time. Every request emits
a structured JSON log line that ships to the ELK stack. A scheduled Jenkins job watches the
live feature distribution and, when it drifts far enough from the training baseline, triggers
the pipeline to retrain and redeploy — with no human in the loop.

The model is a logistic regression over eight transaction features, trained on synthetic
data generated in-repo with a fixed seed. No downloads, so the demo works offline.

## Stack

| Stage | Tool |
|---|---|
| Source control | GitHub (protected `main`, PRs) |
| CI/CD | Jenkins — declarative pipeline |
| Build | Docker, multi-stage, non-root |
| Registry | Docker Hub |
| Configuration management | Ansible — four roles |
| Orchestration | Kubernetes on k3d (K3s) |
| Secrets | HashiCorp Vault — policy-scoped token |
| Autoscaling | Horizontal Pod Autoscaler, 2 → 6 |
| Logging | Elasticsearch · Logstash · Kibana |
| Application | FastAPI · scikit-learn |

## Quick start

```bash
# Prerequisites: Docker Desktop (4.5 GB RAM), k3d, ansible
brew install k3d ansible
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Bring the whole platform up
ansible-playbook ansible/site.yml

# Train, build, deploy
python ml/train.py
docker build -f docker/Dockerfile -t kaushalrajpuwar/fraudloop-scorer:latest .
docker push kaushalrajpuwar/fraudloop-scorer:latest
kubectl apply -f k8s/
kubectl -n fraudloop rollout status deployment/scorer
```

Then:

| Service | Where |
|---|---|
| Application | http://fraudloop.localhost:8080 |
| Jenkins | http://127.0.0.1:8090 |
| Kibana | `kubectl -n logging port-forward svc/kibana 5601:5601` |

Full operating instructions, the demo script, and troubleshooting are in
[docs/03-runbook.md](docs/03-runbook.md).

## How the loop closes

```bash
python scripts/loadgen.py --rate 30 --duration 30 --drift   # shift the distribution
python ml/drift_check.py --url http://localhost:8000        # exits 2
```

The scheduled drift job picks that up, triggers the main pipeline, and the model is
retrained, re-gated, and redeployed. A model that regresses below PR-AUC 0.60 fails the
build and never ships.

## Repository layout

```
app/        FastAPI service, model loader, secret resolution, structured logging, dashboard
ml/         deterministic data generator, training with quality gate, drift check
tests/      14 tests covering the API contract and model behaviour
docker/     application image and CI image
k8s/        namespaces, config, deployment, service, ingress, HPA, PDB
ansible/    site.yml plus cluster, elk, vault, and jenkins roles
jenkins/    delivery pipeline and scheduled drift pipeline
compose/    host-side Jenkins
scripts/    load generator, smoke test, Kibana provisioning
docs/       requirements analysis, plan, proposal, runbook
```

## Dataset

50,000 synthetic transactions, 8 features, ~2% fraud rate, PR-AUC ≈ 0.73 with logistic
regression.

```bash
python ml/generate_data.py --rows 50000
```

## Team

- Kaushalraj Puwar
- Harsh Gupta

## License

MIT
