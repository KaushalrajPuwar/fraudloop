# Runbook

Everything needed to bring FraudLoop up from a cold machine, run the demo, and recover
when something misbehaves.

---

## 1. Prerequisites

```bash
open -a Docker                  # Docker Desktop, 4.5 GB memory, 6 CPUs
brew install k3d ansible
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

Docker Desktop → Settings → Resources: **Memory 4.5 GB**, **CPUs 6**, **Disk 40 GB**.
The stack fits in ~2.7 GB; the ceiling needs headroom for image builds.

## 2. Bring everything up

```bash
ansible-playbook ansible/site.yml
```

That single command creates the k3d cluster, applies the namespaces, deploys ELK into
`logging`, deploys Vault into `vault`, and starts Jenkins on the host.

Roles can be run individually:

```bash
ansible-playbook ansible/site.yml --tags cluster
ansible-playbook ansible/site.yml --tags elk
ansible-playbook ansible/site.yml --tags vault
ansible-playbook ansible/site.yml --tags jenkins
```

## 3. Deploy the application

```bash
python ml/train.py
docker build -f docker/Dockerfile -t kaushalrajpuwar/fraudloop-scorer:latest .
docker push kaushalrajpuwar/fraudloop-scorer:latest
kubectl apply -f k8s/
kubectl -n fraudloop rollout status deployment/scorer
```

## 4. Reach the services

| Service | URL |
|---|---|
| Application | http://fraudloop.localhost:8080 |
| Kibana | `kubectl -n logging port-forward svc/kibana 5601:5601` → http://localhost:5601 |
| Elasticsearch | `kubectl -n logging port-forward svc/elasticsearch 9200:9200` |
| Jenkins | http://127.0.0.1:8090 |
| Vault | `kubectl -n vault port-forward svc/vault 8200:8200` |

Jenkins initial admin password:

```bash
docker exec fraudloop-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

## 5. The demo, in order

**a. Trigger the pipeline.** Push a commit. Jenkins builds, tests, trains, gates, pushes,
and deploys. Refresh the dashboard — the build number and commit hash in the header change.
That is the "new changes visible seamlessly" requirement, on screen.

**b. Prove zero downtime.** In one terminal:

```bash
python scripts/loadgen.py --rate 20 --duration 60
```

In another, while it runs:

```bash
kubectl -n fraudloop set image deployment/scorer \
  scorer=kaushalrajpuwar/fraudloop-scorer:<new-sha>
kubectl -n fraudloop rollout status deployment/scorer
```

The load generator reports zero failures. `maxUnavailable: 0` plus the readiness probe is
what makes that true.

**c. Show the logs.** Kibana → FraudLoop dashboard. Every scored transaction is a document
with amount, score, decision, latency, and model version.

**d. Scale.** With load running:

```bash
kubectl -n fraudloop get hpa scorer -w
```

Replicas climb from 2 toward 6 as CPU crosses 60%.

**e. Close the loop.** Generate drifted traffic, then let the scheduled job fire:

```bash
python scripts/loadgen.py --rate 30 --duration 30 --drift
python ml/drift_check.py --url http://localhost:8000   # exits 2
```

The drift job triggers the main pipeline, which retrains, gates, and redeploys.

**f. Show Vault.** The dashboard's secret card reads `source: vault` with a fingerprint.
Scale Vault to zero and restart the app; the card flips to `env` or `generated` and the
log records a warning. The secret is load-bearing, not decorative.

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `readyz` returns 503 | model artifacts missing from the image | run `python ml/train.py` before `docker build` |
| Pods `ImagePullBackOff` | image not pushed, or wrong tag | `docker push`, then `kubectl set image` |
| Elasticsearch `OOMKilled` | heap too large for the node | keep `-Xmx384m`; check `kubectl top pods -n logging` |
| Logstash never becomes ready | Elasticsearch not ready first | `kubectl -n logging logs deploy/logstash`; it retries |
| Kibana blank | index pattern not created | run `scripts/kibana_setup.sh` |
| HPA shows `<unknown>` | metrics-server still starting | wait 60 s, `kubectl top pods -n fraudloop` |
| Jenkins can't reach the cluster | kubeconfig not mounted | `docker exec fraudloop-jenkins kubectl get nodes` |

## 7. Teardown

```bash
k3d cluster delete fraudloop
cd compose && docker compose down -v
docker system prune -af
```

## 8. Known local simplifications

- **Vault runs in dev mode.** Storage is in-memory and the root token is fixed. A
  production deployment would use Raft storage with auto-unseal; the application-facing
  contract (policy-scoped token, KV v2 path) is unchanged.
- **Elasticsearch runs with security disabled.** It is a single-node local cluster with no
  ingress exposure. Enabling TLS and basic auth is a one-line change per manifest.
- **Logs ship directly from the app to Logstash over TCP** rather than via Filebeat. The
  requirement is that logs reach the ELK stack; this keeps a DaemonSet out of an 8 GB
  laptop. `kubectl logs` still works normally.
