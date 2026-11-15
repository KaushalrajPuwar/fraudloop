# FraudLoop — Setup Guide

Everything needed to go from a bare machine to a running, verified FraudLoop
platform. Written so that either a person or an AI agent can follow it end to end.

**Repository:** https://github.com/KaushalrajPuwar/fraudloop (public)
**Verified on:** macOS 26.7, Apple Silicon, 8 GB RAM, Docker Desktop 27.5.1
**Not yet verified on:** Windows / WSL2 — that path is documented from first
principles below, so expect to iterate on it rather than assume it is exact.

---

## 0. For an agent: the short version

If you are an AI agent setting this up, run these in order and stop at the first
failure. Each step lists what success looks like.

```bash
# 0.1  confirm the machine can host the stack
git clone https://github.com/KaushalrajPuwar/fraudloop.git
cd fraudloop
./scripts/preflight.sh          # expect: "failed 0"

# 0.2  python environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt

# 0.3  dataset + model (both are gitignored, must be generated)
python ml/generate_data.py      # expect: wrote data/transactions.csv rows=50,000
python ml/train.py              # expect: "quality gate passed"

# 0.4  tests
pytest -q                       # expect: 14 passed
ruff check app ml tests scripts # expect: All checks passed!

# 0.5  one-command platform bring-up
ansible-playbook ansible/site.yml   # expect: failed=0

# 0.6  build and load the application image
docker build -f docker/Dockerfile \
  --build-arg APP_VERSION=0.1.0 \
  --build-arg BUILD_NUMBER=1 \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  -t kaushalrajpuwar/fraudloop-scorer:latest .
k3d image import kaushalrajpuwar/fraudloop-scorer:latest -c fraudloop

# 0.7  deploy
kubectl apply -f k8s/
kubectl -n fraudloop rollout status deployment/scorer --timeout=180s

# 0.8  verify
./scripts/smoke.sh http://fraudloop.localhost:8080   # expect: all checks passed
```

Everything after step 0.8 — Docker Hub credentials, Jenkins jobs, Kibana — is
manual UI work described in sections 8–11. An agent cannot do those without
browser automation.

---

## 1. What you are setting up

```
GitHub ──webhook or poll──▶ Jenkins (host, Docker Compose)
                               │ lint → test → train + quality gate
                               │ → build → push → deploy
                               ▼
                        Docker Hub ──┐
                                     ▼
   k3d cluster "fraudloop" (K3s in Docker)
     ├── fraudloop namespace   scorer Deployment x2, HPA 2→6, Ingress
     ├── vault namespace       HashiCorp Vault (dev mode)
     └── logging namespace     Elasticsearch · Logstash · Kibana
```

Three things run **outside** the cluster, all as Docker containers on the host:
Jenkins, and the k3d node containers themselves.

| Component | Where | Port |
|---|---|---|
| Application | in cluster, via k3d load balancer | 8080 |
| Jenkins | host Docker Compose | 8090 |
| Kibana | in cluster, port-forward | 5601 |
| Elasticsearch | in cluster, port-forward | 9200 |
| Vault | in cluster, port-forward | 8200 |

---

## 2. Requirements

| | Minimum | Comfortable |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Free disk | 20 GB | 40 GB |
| CPUs | 4 | 6+ |
| OS | macOS, Linux, or Windows 11 + WSL2 | — |

**8 GB is the practical floor.** The stack requests about 2.7 GB inside Docker
plus whatever the host OS needs. On 8 GB you will need to close browsers and
chat apps during the demo. This is not a preference — Elasticsearch gets
OOM-killed without the headroom.

---

## 3. Windows: install WSL2 first

Docker, k3d, and Ansible all run far more reliably inside WSL2 than in native
Windows shells. Do everything below **inside Ubuntu**, not PowerShell.

### 3.1 Install WSL2 and Ubuntu

Open PowerShell **as Administrator**:

```powershell
wsl --install -d Ubuntu
```

Reboot when prompted. Ubuntu will ask for a UNIX username and password on first
launch — this is separate from your Windows account.

Verify from PowerShell:

```powershell
wsl -l -v
```

Expect `Ubuntu` with `STATE=Running` and `VERSION=2`. If it says version 1:

```powershell
wsl --set-version Ubuntu 2
```

### 3.2 Install Docker Desktop with WSL integration

1. Download Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/
2. Install and start it.
3. **Settings → General** → ensure *Use the WSL 2 based engine* is checked.
4. **Settings → Resources → WSL Integration** → enable the toggle for **Ubuntu**.
5. **Settings → Resources → Advanced** → set **Memory 4.5 GB**, **CPUs 6**.
   Click **Apply & restart**.

Verify inside Ubuntu:

```bash
docker version          # expect Client and Server both reporting a version
docker info --format '{{.MemTotal}} {{.NCPU}}'
```

The second command should print roughly `4600000000 6`. If `MemTotal` is under
4 GB, the memory setting did not apply — restart Docker Desktop and check again.

### 3.3 Keep the repository inside the Linux filesystem

Clone into `~/fraudloop`, **not** into `/mnt/c/...`. Cross-filesystem I/O from
WSL2 to Windows is roughly 10x slower and will make `docker build` and the
Ansible playbook crawl.

```bash
cd ~
git clone https://github.com/KaushalrajPuwar/fraudloop.git
cd fraudloop
```

### 3.4 Make `fraudloop.localhost` resolve on Windows

The ingress routes by hostname. Windows does not resolve arbitrary
`*.localhost` names the way macOS does, so add an entry.

Open Notepad **as Administrator**, then open
`C:\Windows\System32\drivers\etc\hosts` and add:

```
127.0.0.1 fraudloop.localhost
```

If you cannot edit that file, the fallback is to always send the header
explicitly:

```bash
curl -H "Host: fraudloop.localhost" http://localhost:8080/healthz
```

### 3.5 WSL2 memory, if you have 16 GB or more

Create `C:\Users\<YourName>\.wslconfig`:

```ini
[wsl2]
memory=6GB
processors=6
swap=2GB
```

Then from PowerShell: `wsl --shutdown` and reopen Ubuntu.

If you have 8 GB, **skip this** — let WSL2 use its defaults and just close other
applications. Capping it further will starve the cluster.

---

## 4. Linux or macOS instead

Skip section 3 entirely. You need Docker running, then:

```bash
git clone https://github.com/KaushalrajPuwar/fraudloop.git
cd fraudloop
```

On macOS, `fraudloop.localhost` already resolves to 127.0.0.1 — no hosts file
edit needed.

---

## 5. Install the tooling

Inside Ubuntu (or your Linux/macOS shell):

### 5.1 Base packages

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
```

### 5.2 kubectl

```bash
curl -fsSL -o /tmp/kubectl "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
kubectl version --client
```

On Apple Silicon use `linux/arm64` in the URL instead of `linux/amd64`; on
Linux ARM use `linux/arm64` as well.

### 5.3 k3d

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
k3d version
```

### 5.4 Ansible

```bash
pipx install --include-deps ansible
```

If `pipx` is missing:

```bash
sudo apt-get install -y pipx
pipx ensurepath
# open a new shell, then re-run the pipx install command
```

Verify:

```bash
ansible --version | head -1
```

### 5.5 Ansible needs the Kubernetes Python library

The `kubernetes.core` collection shells out to the `kubernetes` Python package.
Without it every cluster task fails with *"Failed to import the required Python
library (kubernetes)"*.

```bash
python3 -m pip install --break-system-packages kubernetes
python3 -c "import kubernetes; print(kubernetes.__version__)"
```

If `--break-system-packages` is rejected, your Python is externally managed and
you have two options:

```bash
# option A: use a dedicated venv and point Ansible at it
python3 -m venv ~/.ansible-k8s
~/.ansible-k8s/bin/pip install kubernetes
# then add to ansible/inventory.ini:
#   localhost ansible_connection=local ansible_python_interpreter=~/.ansible-k8s/bin/python

# option B: pipx inject
pipx inject ansible kubernetes
```

---

## 6. Python environment and artifacts

```bash
cd ~/fraudloop
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

Generate the dataset and train the model. **Both are gitignored** — the
repository ships the generator, not the output, so a fresh clone has neither.

```bash
python ml/generate_data.py
# expect: wrote data/transactions.csv  rows=50,000  fraud=1,004 (2.01%)

python ml/train.py
# expect: PR-AUC 0.7284 / ROC-AUC 0.9899 / quality gate passed
```

Confirm the code itself is sound:

```bash
pytest -q                        # expect: 14 passed
ruff check app ml tests scripts  # expect: All checks passed!
```

---

## 7. Bring up the platform

One command creates the cluster, deploys ELK, deploys Vault, and starts Jenkins.

```bash
ansible-playbook ansible/site.yml
```

Expect roughly **28 tasks, `failed=0`**, taking 8–15 minutes on a first run
because Docker has to pull the Elasticsearch, Logstash, and Kibana images.

What it does, in order:

| Role | Effect |
|---|---|
| `cluster` | Creates k3d cluster `fraudloop` (1 server, 1 agent), waits for both nodes, applies the three namespaces |
| `elk` | Deploys Elasticsearch, Logstash, Kibana into `logging`; waits for all three to be ready |
| `vault` | Deploys Vault into `vault`, installs a read-only policy, stores the API key, issues a 24h scoped token, writes it as a Kubernetes secret |
| `jenkins` | Rewrites your kubeconfig so containers can reach the API, builds the Jenkins image, starts it via Compose |

Run a single role with `--tags`:

```bash
ansible-playbook ansible/site.yml --tags cluster
ansible-playbook ansible/site.yml --tags elk
ansible-playbook ansible/site.yml --tags vault
ansible-playbook ansible/site.yml --tags jenkins
```

The playbook is idempotent — re-running it is safe and is the first thing to try
when something looks wrong.

Verify:

```bash
kubectl get nodes                       # expect 2 Ready
kubectl get pods -n logging             # expect elasticsearch, kibana, logstash Running
kubectl get pods -n vault               # expect vault Running
kubectl -n fraudloop get secret vault-token   # expect the secret to exist
docker ps --filter name=fraudloop-jenkins     # expect "healthy"
```

---

## 8. Docker Hub

The pipeline pushes images to Docker Hub, and the Kubernetes deployment pulls
from there. **The repository is hardcoded to the account `kaushalrajpuwar`.**
If you are setting this up under a different account, change all three places:

| File | Line to change |
|---|---|
| `k8s/20-deployment.yaml` | `image: docker.io/<you>/fraudloop-scorer:latest` |
| `jenkins/Jenkinsfile` | `IMAGE_NAME = 'docker.io/<you>/fraudloop-scorer'` |
| `README.md` | the `docker build` and `docker push` lines |

### 8.1 Create an access token

1. Sign in at https://hub.docker.com
2. **Account Settings → Security → New Access Token**
3. Description: `fraudloop-jenkins`, permissions: **Read & Write**
4. Copy the token — it is shown once.

Do **not** use your account password for this.

### 8.2 Log in from the shell

```bash
docker login -u <your-dockerhub-username>
# paste the token when prompted for the password
```

### 8.3 Push a first image manually

This proves the account works before Jenkins gets involved.

```bash
docker build -f docker/Dockerfile \
  --build-arg APP_VERSION=0.1.0 \
  --build-arg BUILD_NUMBER=0 \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  -t <you>/fraudloop-scorer:latest .

docker push <you>/fraudloop-scorer:latest
```

If that succeeds, Jenkins will too.

---

## 9. Configure Jenkins

### 9.1 Unlock

```bash
docker exec fraudloop-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open http://localhost:8090, paste the password.

### 9.2 Install plugins

Choose **Install suggested plugins** and wait. Then create the admin user when
prompted (any username and password — this is a local instance).

### 9.3 Add the Docker Hub credential

**Manage Jenkins → Credentials → System → Global credentials (unrestricted) →
Add Credentials**

| Field | Value |
|---|---|
| Kind | Username with password |
| Scope | Global |
| Username | your Docker Hub username |
| Password | the access token from 8.1 |
| **ID** | **`dockerhub`** |
| Description | Docker Hub push token |

The ID must be exactly `dockerhub` — that is what the Jenkinsfile references.

### 9.4 Create the delivery job

**New Item → Pipeline → name it `fraudloop` → OK**

| Field | Value |
|---|---|
| Description | FraudLoop delivery pipeline |
| Pipeline → Definition | Pipeline script from SCM |
| SCM | Git |
| Repository URL | `https://github.com/KaushalrajPuwar/fraudloop.git` |
| Branch Specifier | `*/main` |
| Script Path | `jenkins/Jenkinsfile` |

Save.

### 9.5 Create the drift job

**New Item → Pipeline → name it `fraudloop-drift` → OK**

Same fields, except:

| Field | Value |
|---|---|
| Script Path | `jenkins/Jenkinsfile.drift` |

The drift job carries its own `cron('H/30 * * * *')` trigger, so it will start
running on its own once saved.

> The drift job calls `build job: 'fraudloop'` when it detects drift. That
> name must match the delivery job exactly.

### 9.6 Triggering on push (optional)

The delivery pipeline already polls SCM every two minutes, so a push will start
a build without any extra setup.

To use a real GitHub webhook instead — which is what the course PDF names —
expose your local Jenkins to GitHub:

```bash
gh auth login
gh webhook forward --repo=KaushalrajPuwar/fraudloop \
  --events=push --url=http://localhost:8090/github-webhook/
```

Leave that running during the demo. Once the webhook works you can delete the
`pollSCM` block from `jenkins/Jenkinsfile` to avoid duplicate builds.

---

## 10. First pipeline run

Click **Build Now** on `fraudloop` and watch the stages.

| Stage | Expected |
|---|---|
| Checkout | commit hash printed |
| CI image | `fraudloop-ci:latest` built |
| Lint | `All checks passed!` |
| Test | `14 passed` |
| Train and quality gate | `PR-AUC 0.72...`, `quality gate passed` |
| Build image | two tags, one per commit SHA and `latest` |
| Push to Docker Hub | both tags pushed |
| Deploy to Kubernetes | `deployment "scorer" successfully rolled out` |
| Smoke test | `{"status":"ready",...}` |

If any stage fails, the build stops and **nothing is deployed** — that is the
point of the gate.

Verify the result:

```bash
kubectl -n fraudloop get pods
kubectl -n fraudloop get deployment scorer \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
```

The image tag should be the short commit SHA from the run.

---

## 11. Kibana

```bash
# terminal 1 - leave running
kubectl -n logging port-forward svc/kibana 5601:5601

# terminal 2
source .venv/bin/activate
python scripts/kibana_setup.py --url http://localhost:5601
```

Expect five `ok` lines: index pattern, three Lens panels, dashboard.

Open http://localhost:5601/app/dashboards#/view/fl-dashboard

Generate some traffic first, otherwise the panels are empty:

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 20 --duration 20
```

Set the dashboard time range to **Last 15 minutes**.

---

## 12. Verification checklist

Run these in order. Every one should pass before you consider the setup done.

| # | Command | Expected |
|---|---|---|
| 1 | `./scripts/preflight.sh` | `failed 0` |
| 2 | `pytest -q` | `14 passed` |
| 3 | `ruff check app ml tests scripts` | `All checks passed!` |
| 4 | `kubectl get nodes` | 2 nodes `Ready` |
| 5 | `kubectl get pods -A \| grep -v kube-system` | 6 pods `Running` |
| 6 | `./scripts/smoke.sh http://fraudloop.localhost:8080` | `all checks passed` |
| 7 | `curl -s http://fraudloop.localhost:8080/stats \| python -m json.tool` | `"source": "vault"` |
| 8 | `kubectl -n fraudloop get hpa` | `cpu: NN%/60%`, 2–6 replicas |
| 9 | `docker exec fraudloop-jenkins kubectl get nodes` | 2 nodes |
| 10 | Jenkins `fraudloop` job | all stages green |
| 11 | Kibana dashboard | panels render with data |

Check 7 is the one people skip. If it says `"source": "env"` or
`"generated"` instead of `"vault"`, the Vault role did not complete — re-run
`ansible-playbook ansible/site.yml --tags vault`.

---

## 13. Demo sequence

The order that shows every rubric item in about eight minutes.

**1. Push a change.** Edit the version string in `app/config.py`, commit, push.
Jenkins picks it up, runs the full pipeline, deploys. Refresh
http://fraudloop.localhost:8080 — the build number and commit hash in the header
change. *This is the "new changes visible seamlessly" requirement.*

**2. Prove zero downtime.** In one terminal:

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 80 --duration 70
```

While it runs, in another:

```bash
kubectl -n fraudloop rollout restart deployment/scorer
kubectl -n fraudloop rollout status deployment/scorer
```

The load generator must report **zero failures**. If it drops requests, the
`preStop` drain is missing from the deployment.

**3. Show the logs.** Kibana dashboard. Every scored transaction is a document
with amount, score, decision, latency, and model version.

**4. Scale.** With load running:

```bash
kubectl -n fraudloop get hpa scorer -w
```

Replicas climb from 2 toward 6.

**5. Close the loop.**

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 40 --duration 15 --drift
python ml/drift_check.py --url http://fraudloop.localhost:8080   # exits 2
```

Then trigger `fraudloop-drift` in Jenkins (or wait for the cron). It detects
drift and fires the delivery pipeline, which retrains, re-gates, and redeploys.

**6. Show Vault is load-bearing.**

```bash
kubectl -n vault scale deployment/vault --replicas=0
kubectl -n fraudloop rollout restart deployment/scorer
# dashboard secret card flips from "vault" to "generated"
kubectl -n vault scale deployment/vault --replicas=1
ansible-playbook ansible/site.yml --tags vault   # restore the secret
```

---

## 14. Troubleshooting

### WSL2 specific

**`docker: command not found` inside Ubuntu.** Docker Desktop WSL integration is
off. Settings → Resources → WSL Integration → enable Ubuntu, then restart the
Ubuntu shell.

**`docker info` reports under 4 GB.** The memory setting did not apply. Change
it, click *Apply & restart*, and confirm with
`docker info --format '{{.MemTotal}}'`.

**Browser cannot reach localhost:8080.** Confirm the port is published:
`docker ps | grep 8080`. If Docker Desktop is running but the port is not
published, the k3d cluster was created without the port mapping — delete and
recreate it with `ansible-playbook ansible/site.yml --tags cluster` after
`k3d cluster delete fraudloop`.

**`fraudloop.localhost` does not resolve.** Section 3.4 — add the hosts entry,
or pass `-H "Host: fraudloop.localhost"`.

**Everything is slow.** The repository is on `/mnt/c`. Move it into the Linux
filesystem (`~/fraudloop`).

### General

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to import the required Python library (kubernetes)` | missing Python package | section 5.5 |
| `readyz` returns 503 | no model in the image | `python ml/train.py` before `docker build` |
| Pods `ImagePullBackOff` | image not pushed, or wrong account | section 8 |
| Elasticsearch `OOMKilled` | heap too large for the node | keep `-Xmx384m`; check `kubectl top pods -n logging` |
| Kibana crash-loops with a V8 heap error | heap below ~512 MB | `NODE_OPTIONS` must stay at `--max-old-space-size=640` |
| Logstash never ready | Elasticsearch not up first | `kubectl -n logging logs deploy/logstash` — it retries |
| HPA shows `<unknown>` | metrics-server still starting | wait 60 s, then `kubectl top pods -n fraudloop` |
| Jenkins cannot reach the cluster | kubeconfig points at 0.0.0.0 | `ansible-playbook ansible/site.yml --tags jenkins` |
| Pipeline fails at Push | `dockerhub` credential missing or misnamed | section 9.3 |

**When in doubt, re-run the playbook.** It is idempotent:

```bash
ansible-playbook ansible/site.yml
```

---

## 15. Command reference

```bash
# bring everything up / repair
ansible-playbook ansible/site.yml

# rebuild and redeploy the app by hand
python ml/train.py
docker build -f docker/Dockerfile -t <you>/fraudloop-scorer:latest .
docker push <you>/fraudloop-scorer:latest
kubectl -n fraudloop set image deployment/scorer scorer=<you>/fraudloop-scorer:latest
kubectl -n fraudloop rollout status deployment/scorer

# inspect
kubectl -n fraudloop get pods,svc,ingress,hpa
kubectl -n fraudloop logs deploy/scorer --tail=50
kubectl -n logging logs deploy/logstash --tail=50
docker logs fraudloop-jenkins --tail=50

# traffic
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 20 --duration 30
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 40 --duration 15 --drift
python ml/drift_check.py --url http://fraudloop.localhost:8080

# smoke
./scripts/smoke.sh http://fraudloop.localhost:8080

# port-forwards
kubectl -n logging port-forward svc/kibana 5601:5601
kubectl -n logging port-forward svc/elasticsearch 9200:9200
kubectl -n vault port-forward svc/vault 8200:8200

# teardown
k3d cluster delete fraudloop
cd compose && docker compose down -v
docker system prune -af
```

---

## 16. Known limitations

These are deliberate, documented in the runbook, and worth knowing before a viva.

- **Vault runs in dev mode.** In-memory storage, fixed root token. The
  application-facing contract (policy-scoped token, KV v2 path) is the real
  thing, but a restart loses the secret until the playbook re-seeds it.
- **Elasticsearch has security disabled.** Single-node local cluster, not
  exposed beyond the port-forward.
- **Logs ship from the app directly to Logstash over TCP**, not through
  Filebeat. It keeps a DaemonSet off an 8 GB laptop. `kubectl logs` still works.
- **The k3d cluster is not highly available.** One server, one agent. The
  zero-downtime guarantee is about pods, not nodes.
