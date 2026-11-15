# FraudLoop — Complete Setup Guide

A from-scratch guide for someone who has never seen this project. It assumes
you know nothing about it and takes you to a working, verified system.

Written for both people and AI agents. Every command is copy-pasteable, and
every step says what success looks like.

**Repository:** https://github.com/KaushalrajPuwar/fraudloop (public)

---

## Contents

- [Part 0 — Start here](#part-0--start-here)
- [Part 1 — Before you install](#part-1--before-you-install)
- [Part 2 — Install on Windows](#part-2--install-on-windows)
- [Part 3 — Install on Linux or macOS](#part-3--install-on-linux-or-macos)
- [Part 4 — Get the code running](#part-4--get-the-code-running)
- [Part 5 — Bring up the platform](#part-5--bring-up-the-platform)
- [Part 6 — Docker Hub](#part-6--docker-hub)
- [Part 7 — Configure Jenkins](#part-7--configure-jenkins)
- [Part 8 — Kibana](#part-8--kibana)
- [Part 9 — Understanding the dashboard](#part-9--understanding-the-dashboard)
- [Part 10 — Verification checklist](#part-10--verification-checklist)
- [Part 11 — The demo](#part-11--the-demo)
- [Part 12 — Everyday operations](#part-12--everyday-operations)
- [Part 13 — Troubleshooting](#part-13--troubleshooting)
- [Part 14 — Reference](#part-14--reference)

---

# Part 0 — Start here

## 0.1 What is this project?

FraudLoop is **two things at once**, and the difference matters:

1. **A small fraud-scoring web service.** You send it a card transaction, it
   replies with a fraud probability and a BLOCK or ALLOW decision. It is about
   450 lines of Python. It is deliberately boring.

2. **A complete automated delivery pipeline wrapped around it.** Push a commit
   and, with no human involvement, the code is tested, a model is retrained and
   quality-checked, a container image is built and published, the cluster is
   updated, and the logs show up in a dashboard.

**The second one is the project.** The course is *Software Production
Engineering*, and the marking scheme rewards DevOps engineering, not application
complexity. The fraud service exists only to give the pipeline something real to
build, test, deploy, and observe.

If you remember one sentence: **the app is the excuse, the pipeline is the work.**

## 0.2 What the marking actually rewards

The course PDF gives 30 marks:

| Marks | What it is | How this project earns it |
|---|---|---|
| **20** | A working, deployable project | The pipeline runs end to end and the app is live on Kubernetes |
| **3** | Vault, Ansible roles, Kubernetes HPA | All three are implemented |
| **2** | Innovation | Drift-triggered automatic retraining |
| **5** | A domain-specific project | MLOps × Finance |

Note the shape: **20 of 30 marks ride on "does it work"**. That is why this guide
is so long — a demo that fails costs more than any feature is worth.

## 0.3 The seven pieces

| Piece | What it is | Why it exists |
|---|---|---|
| **The app** | FastAPI service, one container | The thing being deployed |
| **Jenkins** | CI/CD server, runs on your machine in Docker | Builds, tests, and ships the app automatically |
| **k3d cluster** | A real Kubernetes cluster running inside Docker | Where the app runs |
| **Docker Hub** | Public image registry | Where the built image is stored |
| **Ansible** | Configuration management | Sets up the cluster and everything on it, from one command |
| **Vault** | Secrets manager | Holds the app's signing key |
| **ELK** | Elasticsearch + Logstash + Kibana | Collects and displays the app's logs |

Everything runs **on your laptop**. There is no cloud bill and no external
service except Docker Hub, which is free.

## 0.4 What happens when someone pushes code

This is the single most important thing to understand. Read it twice.

```
You run:  git push
   │
   ▼
GitHub notifies Jenkins (or Jenkins polls every 2 minutes)
   │
   ▼
Jenkins runs jenkins/Jenkinsfile, stage by stage:
   │
   ├─ 1. Checkout ............ pull the commit
   ├─ 2. CI image ............ build a Python image with test dependencies
   ├─ 3. Lint ................ ruff — style and obvious bugs
   ├─ 4. Test ................ pytest — 14 tests must pass
   ├─ 5. Train + gate ........ retrain the model; FAIL THE BUILD if PR-AUC < 0.60
   ├─ 6. Build image ......... docker build, with the commit SHA baked in
   ├─ 7. Push ................ docker push to Docker Hub
   ├─ 8. Deploy .............. kubectl set image -> Kubernetes rolls out new pods
   └─ 9. Smoke test .......... exec into a pod and hit /readyz
   │
   ▼
The new version is live. Refresh the dashboard: the build number changed.
```

If any stage fails, **nothing is deployed**. That is the point — a bad model or
broken code cannot reach production.

## 0.5 Glossary

Terms you will see in the commands and in conversation.

| Term | Plain meaning |
|---|---|
| **Cluster** | A group of machines (here: containers pretending to be machines) that run your app |
| **Pod** | The smallest unit Kubernetes runs — usually one container |
| **Deployment** | A Kubernetes object that keeps N copies of a pod running |
| **Replica** | One copy of your app. Two replicas = two pods |
| **Rollout** | Replacing old pods with new ones without downtime |
| **HPA** | Horizontal Pod Autoscaler — adds replicas when CPU is high |
| **Ingress** | The front door that routes outside traffic to a service |
| **Namespace** | A folder for Kubernetes objects. We use `fraudloop`, `logging`, `vault` |
| **Image** | A packaged, immutable snapshot of an application |
| **Registry** | Where images are stored. Ours is Docker Hub |
| **Pipeline** | The automated sequence Jenkins runs |
| **Quality gate** | A check that fails the build if a metric is too low |
| **Drift** | When live data stops looking like the data the model was trained on |
| **Playbook** | An Ansible script that configures machines |
| **Role** | A reusable, self-contained chunk of an Ansible playbook |
| **Port-forward** | Tunnelling a cluster service to your laptop so a browser can reach it |

---

# Part 1 — Before you install

## 1.1 Hardware

| | Minimum | Comfortable |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Free disk | 20 GB | 40 GB |
| CPUs | 4 | 6+ |

**8 GB is the practical floor.** The stack uses about 2.7 GB inside Docker plus
whatever your OS needs. On 8 GB you must close browsers and chat apps during the
demo — Elasticsearch gets killed without the headroom. This is not a
preference, it is a hard limit.

## 1.2 Accounts you need

| Account | Why | Cost |
|---|---|---|
| **GitHub** | The repository lives there | Free |
| **Docker Hub** | Images are pushed there | Free |

You also need to be **added as a collaborator** on
`github.com/KaushalrajPuwar/fraudloop`. Ask Kaushal to send the invite and
accept it, otherwise you cannot push.

## 1.3 Files you will be sent, and where they go

Some files arrive out of band — over a messaging app, email, or a shared drive.
Here is exactly where each one belongs.

| If you receive… | Put it here | Commit it? |
|---|---|---|
| Course PDFs (`FinalProjectGuidelinesAndEvaluationCriteria.pdf`, `SPE_Capstone_Project.md`) | `docs/` | Already committed — no action |
| Screenshots for the report | `docs/images/` | Yes |
| A report draft | `docs/` | Yes |
| **Docker Hub access token** | **Nowhere.** Paste it into Jenkins as a credential (Part 6) | **Never** |
| A `.env` file | Repository root | **Never** — already gitignored |
| SSH keys, `.pem`, `.key` | `~/.ssh/` on your machine | **Never** — already gitignored |
| Anything with a password in it | Nowhere near the repo | **Never** |

**Rule of thumb:** if it is a secret, it goes into Jenkins or Vault, never into a
file that gets committed. The `.gitignore` already blocks `.env`, `*.pem`,
`*.key`, and `kubeconfig*`.

If you are unsure where something goes, put it in `docs/` and ask.

---

# Part 2 — Install on Windows

Everything below runs **inside Ubuntu under WSL2**, not in PowerShell. Docker,
k3d, and Ansible are all far more reliable there.

## 2.1 Install WSL2 and Ubuntu

Open PowerShell **as Administrator**:

```powershell
wsl --install -d Ubuntu
```

Reboot when prompted. Ubuntu asks for a UNIX username and password on first
launch — this is separate from your Windows login and you will need it.

Verify from PowerShell:

```powershell
wsl -l -v
```

**Success looks like:** `Ubuntu`, `STATE=Running`, `VERSION=2`.

If it says version 1:

```powershell
wsl --set-version Ubuntu 2
```

## 2.2 Install Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop/ and install.
2. Start it and wait for the whale icon to stop animating.
3. **Settings → General** → tick *Use the WSL 2 based engine*.
4. **Settings → Resources → WSL Integration** → enable the toggle for **Ubuntu**.
5. **Settings → Resources → Advanced** → **Memory 4.5 GB**, **CPUs 6**.
6. Click **Apply & restart**.

Verify inside Ubuntu:

```bash
docker version
docker info --format '{{.MemTotal}} {{.NCPU}}'
```

**Success looks like:** both Client and Server print a version, and the second
command prints roughly `4630000000 6`.

If `MemTotal` is under 4 GB the memory setting did not apply — restart Docker
Desktop and check again.

## 2.3 Keep the repository in the Linux filesystem

Clone into `~/fraudloop`, **never** into `/mnt/c/...`. Cross-filesystem I/O
from WSL2 to Windows is roughly 10× slower and will make `docker build` and the
Ansible playbook crawl.

You will do this in Part 4.

## 2.4 Make `fraudloop.localhost` resolve

The ingress routes by hostname, and Windows does not resolve arbitrary
`*.localhost` names the way macOS does.

Open Notepad **as Administrator**, open
`C:\Windows\System32\drivers\etc\hosts`, and add:

```
127.0.0.1 fraudloop.localhost
```

Save. If you cannot edit that file, the fallback is to always send the header
explicitly:

```bash
curl -H "Host: fraudloop.localhost" http://localhost:8080/healthz
```

## 2.5 WSL2 memory, only if you have 16 GB or more

Create `C:\Users\<YourName>\.wslconfig`:

```ini
[wsl2]
memory=6GB
processors=6
swap=2GB
```

Then from PowerShell: `wsl --shutdown`, and reopen Ubuntu.

**On 8 GB, skip this.** Let WSL2 use its defaults and close other apps instead.
Capping it further will starve the cluster.

---

# Part 3 — Install on Linux or macOS

Skip Part 2 entirely. You need Docker running, then continue to Part 4.

On macOS, `fraudloop.localhost` already resolves to 127.0.0.1 — no hosts file
edit needed.

Install Docker Desktop (macOS) or Docker Engine (Linux), then set the memory
limit to 4.5 GB in Docker Desktop's resources panel.

---

# Part 4 — Get the code running

## 4.1 Install the tooling

These are the command-line tools. Run them in Ubuntu (Windows) or your normal
shell (Linux/macOS).

### Base packages (Ubuntu only)

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates python3 python3-venv python3-pip pipx
pipx ensurepath
```

Close and reopen your terminal so `pipx` is on your PATH.

### kubectl

```bash
curl -fsSL -o /tmp/kubectl "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
kubectl version --client
```

On Apple Silicon or Linux ARM, replace `linux/amd64` with `linux/arm64`.

On macOS you can just run `brew install kubectl`.

### k3d

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
k3d version
```

On macOS: `brew install k3d`.

### Ansible

```bash
pipx install --include-deps ansible
ansible --version | head -1
```

On macOS: `brew install ansible`.

### The Kubernetes Python library

**This one is easy to miss and everything breaks without it.** The
`kubernetes.core` Ansible collection shells out to the `kubernetes` Python
package. Without it every cluster task fails with
*"Failed to import the required Python library (kubernetes)"*.

```bash
python3 -m pip install --break-system-packages kubernetes
python3 -c "import kubernetes; print(kubernetes.__version__)"
```

If `--break-system-packages` is rejected, pick one:

```bash
# option A — dedicated venv, then point Ansible at it
python3 -m venv ~/.ansible-k8s
~/.ansible-k8s/bin/pip install kubernetes
# then add to ansible/inventory.ini:
#   localhost ansible_connection=local ansible_python_interpreter=~/.ansible-k8s/bin/python

# option B — inject into the pipx environment
pipx inject ansible kubernetes
```

## 4.2 Clone the repository

```bash
cd ~
git clone https://github.com/KaushalrajPuwar/fraudloop.git
cd fraudloop
```

**Success looks like:** `ls` shows `app  ansible  compose  docker  docs  jenkins  k8s  ml  scripts  tests`.

## 4.3 Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

Your prompt should now start with `(.venv)`. **Every command from here on
assumes the venv is active.** If you open a new terminal, re-run
`source .venv/bin/activate`.

## 4.4 Generate the things that are not in the repo

Two directories are **gitignored** — a fresh clone has neither. This trips people
up constantly.

```bash
python ml/generate_data.py
```

**Success looks like:** `wrote data/transactions.csv  rows=50,000  fraud=1,004 (2.01%)`

```bash
python ml/train.py
```

**Success looks like:**

```
model      m-20261115053313
rows       50,000
PR-AUC     0.7284
ROC-AUC    0.9899
gate       >= 0.60

quality gate passed
```

That wrote `artifacts/model.pkl` and `artifacts/model_meta.json`. **The Docker
image copies `artifacts/` at build time.** If you skip this step the container
builds fine but `/readyz` returns 503 and the pod never becomes ready.

## 4.5 Check the code is sound

```bash
pytest -q
```

**Success looks like:** `14 passed`

```bash
ruff check app ml tests scripts
```

**Success looks like:** `All checks passed!`

## 4.6 Optional: run the app before touching Kubernetes

Worth doing once so you know the app itself works before adding cluster
complexity.

```bash
uvicorn app.main:app --port 8000
```

Open http://localhost:8000. You should see the dashboard. Press `Ctrl-C` to stop.

## 4.7 Preflight

```bash
./scripts/preflight.sh
```

This checks tooling, Docker memory, Python, host RAM, disk, ports, and cluster
reachability.

**Success looks like:** `passed N   warnings N   failed 0`

If it reports failures, fix them before continuing. Warnings are fine.

---

# Part 5 — Bring up the platform

## 5.1 One command

```bash
ansible-playbook ansible/site.yml
```

This takes **8–15 minutes** on a first run because Docker has to pull the
Elasticsearch, Logstash, and Kibana images.

**Success looks like:** `PLAY RECAP ... failed=0`

## 5.2 What it actually does

| Role | Effect |
|---|---|
| `cluster` | Creates the k3d cluster `fraudloop` (1 server, 1 agent), waits for both nodes, applies three namespaces |
| `elk` | Deploys Elasticsearch, Logstash, Kibana into `logging`, waits for all three to be ready |
| `vault` | Deploys Vault into `vault`, installs a read-only policy, stores the API key, issues a 24-hour scoped token, writes it as a Kubernetes secret |
| `jenkins` | Rewrites your kubeconfig so containers can reach the API, builds the Jenkins image, starts it with Compose, confirms it can see the cluster |

It is **idempotent** — running it again is safe and is the first thing to try
when something looks wrong.

Run one role at a time with `--tags`:

```bash
ansible-playbook ansible/site.yml --tags cluster
ansible-playbook ansible/site.yml --tags elk
ansible-playbook ansible/site.yml --tags vault
ansible-playbook ansible/site.yml --tags jenkins
```

## 5.3 Verify the platform

```bash
kubectl get nodes
```

**Success looks like:** two nodes, both `Ready`.

```bash
kubectl get pods -A | grep -v kube-system
```

**Success looks like:** `elasticsearch-...`, `kibana-...`, `logstash-...`,
`vault-...` all `Running`.

```bash
docker ps --filter name=fraudloop-jenkins
```

**Success looks like:** status contains `(healthy)`.

## 5.4 Deploy the application

The playbook sets up the platform but **not the app** — the app is supposed to be
deployed by Jenkins. For the first run, do it by hand so you can verify before
adding the pipeline.

```bash
docker build -f docker/Dockerfile \
  --build-arg APP_VERSION=0.1.0 \
  --build-arg BUILD_NUMBER=1 \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  -t kaushalrajpuwar/fraudloop-scorer:latest .

k3d image import kaushalrajpuwar/fraudloop-scorer:latest -c fraudloop

kubectl apply -f k8s/
kubectl -n fraudloop rollout status deployment/scorer --timeout=180s
```

**Success looks like:** `deployment "scorer" successfully rolled out`

```bash
./scripts/smoke.sh http://fraudloop.localhost:8080
```

**Success looks like:** five `ok` lines and `all checks passed`.

Open http://fraudloop.localhost:8080 — you should see the dashboard.

---

# Part 6 — Docker Hub

The pipeline pushes images to Docker Hub and Kubernetes pulls them from there.

**The repository is hardcoded to the account `kaushalrajpuwar`.** If you are
setting this up under a different account, change all three places:

| File | Change |
|---|---|
| `k8s/20-deployment.yaml` | `image: docker.io/<you>/fraudloop-scorer:latest` |
| `jenkins/Jenkinsfile` | `IMAGE_NAME = 'docker.io/<you>/fraudloop-scorer'` |
| `README.md` | the `docker build` / `docker push` lines |

## 6.1 Create an access token

1. Sign in at https://hub.docker.com
2. **Account Settings → Security → New Access Token**
3. Description `fraudloop-jenkins`, permissions **Read & Write**
4. Copy it — it is shown once

Never use your account password for this.

## 6.2 Log in from the shell

```bash
docker login -u <your-dockerhub-username>
```

Paste the token when it asks for a password.

## 6.3 Push one image by hand

Proves the account works before Jenkins is involved.

```bash
docker build -f docker/Dockerfile \
  --build-arg APP_VERSION=0.1.0 --build-arg BUILD_NUMBER=0 \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  -t <you>/fraudloop-scorer:latest .

docker push <you>/fraudloop-scorer:latest
```

**Success looks like:** a progress bar ending in `digest: sha256:...`

---

# Part 7 — Configure Jenkins

## 7.1 Unlock

```bash
docker exec fraudloop-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open http://localhost:8090 and paste it.

## 7.2 Install plugins

Choose **Install suggested plugins** and wait. Create the admin user when
prompted — any username and password, this is a local instance.

## 7.3 Add the Docker Hub credential

**Manage Jenkins → Credentials → System → Global credentials (unrestricted) →
Add Credentials**

| Field | Value |
|---|---|
| Kind | Username with password |
| Scope | Global |
| Username | your Docker Hub username |
| Password | the token from 6.1 |
| **ID** | **`dockerhub`** |
| Description | Docker Hub push token |

**The ID must be exactly `dockerhub`.** The Jenkinsfile references it by name.

## 7.4 Create the delivery job

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

## 7.5 Create the drift job

**New Item → Pipeline → name it `fraudloop-drift` → OK**

Same fields, except **Script Path** is `jenkins/Jenkinsfile.drift`.

It carries its own `cron('H/30 * * * *')` trigger, so it starts running on its
own once saved.

> The drift job calls `build job: 'fraudloop'`. That name must match the
> delivery job exactly or drift detection will silently do nothing.

## 7.6 Triggering on push

The delivery pipeline already polls SCM every two minutes, so a push starts a
build with no extra setup.

To use a real GitHub webhook — the mechanism the course PDF names — expose your
local Jenkins to GitHub:

```bash
gh auth login
gh webhook forward --repo=KaushalrajPuwar/fraudloop \
  --events=push --url=http://localhost:8090/github-webhook/
```

Leave it running during the demo. Once it works you can delete the `pollSCM`
block from `jenkins/Jenkinsfile` to avoid duplicate builds.

## 7.7 Run it

Click **Build Now** on `fraudloop`.

| Stage | Expected |
|---|---|
| Checkout | commit hash printed |
| CI image | `fraudloop-ci:latest` built |
| Lint | `All checks passed!` |
| Test | `14 passed` |
| Train and quality gate | `PR-AUC 0.72...`, `quality gate passed` |
| Build image | two tags |
| Push to Docker Hub | both tags pushed |
| Deploy to Kubernetes | `successfully rolled out` |
| Smoke test | `{"status":"ready",...}` |

---

# Part 8 — Kibana

Kibana is where the logs live. It is a cluster service, so you need a
port-forward.

```bash
# terminal 1 — leave this running
kubectl -n logging port-forward svc/kibana 5601:5601
```

```bash
# terminal 2
source .venv/bin/activate
python scripts/kibana_setup.py --url http://localhost:5601
```

**Success looks like:** five `ok` lines — index pattern, three Lens panels, the
dashboard.

Open http://localhost:5601/app/dashboards#/view/fl-dashboard

**Generate traffic first**, or the panels are empty:

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 20 --duration 20
```

Set the time range to **Last 15 minutes**.

---

# Part 9 — Understanding the dashboard

The dashboard at http://fraudloop.localhost:8080 is the thing you will point at
during the demo. This section explains every part of it so you are never
guessing.

## 9.1 What it is, technically

One static HTML file — `app/static/index.html`, about 340 lines. No React, no
npm, no build step. Vanilla JavaScript. FastAPI serves it as a plain file.

It works like this:

```
Browser loads the page once
   │
   ├─ every 3 seconds: GET /stats   -> all the numbers refresh
   └─ on button click: POST /score  -> one transaction is scored
```

**Every number on screen comes from that one `/stats` call.** There is no
WebSocket and no server-side rendering.

## 9.2 Why things move on their own

The page re-renders every 3 seconds. That is the only reason anything appears to
"happen automatically".

**The counters only change when a transaction is actually scored.** They do not
drift on their own. If nothing is sending traffic, the numbers sit still — the
page just redraws the same values.

Three things produce traffic:

1. **The "Score one transaction" button** — one request per click
2. **`scripts/loadgen.py`** — sustained traffic, this is what makes a demo look alive
3. **The drift demo** — same script with `--drift`

If the numbers are climbing and you did not click anything, a load generator is
still running somewhere. Find it:

```bash
ps aux | grep loadgen
```

**If you find the auto-refresh distracting, click "Pause updates".** The numbers
freeze so you can read them. Click again to resume. This is the single most
useful button on the page when you are trying to understand what is going on.

## 9.3 Every element, explained

### Header strip

```
v0.1.0 · build #3 · 26b5ff5
```

| Piece | Where it comes from | What it tells you |
|---|---|---|
| `v0.1.0` | `APP_VERSION` build arg | image version |
| `build #3` | Jenkins `BUILD_NUMBER` | which pipeline run built this |
| `26b5ff5` | `GIT_SHA` build arg | the exact commit that is running |

**This is the most important element for the demo.** It is baked into the image
at build time, so it is proof that a specific commit is live. Push a change, let
the pipeline run, refresh — the string changes.

### Status line

```
● live · 2 replicas · served by scorer-84857b8585-qpjz6
```

| Piece | Meaning |
|---|---|
| Green dot / `live` | the last `/stats` call succeeded |
| Red dot / `disconnected` | the call failed — app down, pods rolling, ingress broken |
| Amber dot / `paused` | you pressed pause |
| `2 replicas` | how many distinct pods the browser has talked to |
| `served by ...` | which pod answered this poll — **it alternates every 3 seconds, and that is the load balancer working** |

### The four counters

| Card | Counts | Subtitle on the card | What is normal |
|---|---|---|---|
| **Scored** | transactions scored since the pods started | "total since the pods started" | climbs with traffic |
| **Blocked** | those that returned `BLOCK` | "score ≥ 0.50" | about 2% of Scored |
| **Block rate** | `Blocked / Scored` | "dataset is ~2% fraud" | **near 2.0%** |
| **p95 latency** | 95th percentile of scoring time | "last 500 requests" | single-digit ms |

The block rate sitting near 2% is your sanity check. If it reads 0% or 50%,
something is wrong with the model or the threshold.

### Model card

```
version     m-3
trained     2026-11-15 05:33:13
PR-AUC      0.728
ROC-AUC     0.990
```

Read from `artifacts/model_meta.json`, which the training stage baked into the
image. The version is `m-<BUILD_NUMBER>`, so **model version tracks image
version** — that is why there is no MLflow in this project.

PR-AUC 0.728 is the number the CI gate checks against 0.60.

### Signing key card

```
source       vault
fingerprint  42aeab4dc485
```

- **`source`** is the one that matters. `vault` means the app fetched its HMAC
  signing key from HashiCorp Vault at startup. `env` or `generated` means Vault
  was unreachable and it fell back.
- **`fingerprint`** is the first 12 characters of the SHA-256 of that key.

This is your proof that Vault is load-bearing rather than decorative.

### Most recent transaction panel

This is the part that makes the page readable. For the last transaction scored:

```
0.9400  BLOCK     score is the model's fraud probability

Why: Pushed toward fraud: amount $2,400.00 ↑ · distance from home 420.0 km ↑
     · transactions in 24h 18 ↑

hour 3:00 · 18 txns/24h · avg $40.00 · distance 420.0 km · foreign
· merchant risk 0.92 · card 45 days old
```

**The "Why" line is the important bit.** The model is a logistic regression, so
each feature's contribution is exactly its coefficient times its scaled value —
no approximation. The three largest are shown, with ↑ for pushing toward fraud
and ↓ for pushing toward legitimate.

That single line turns "everything looks the same" into "this one was blocked
because the amount was enormous relative to the card's history and it was 420 km
from home".

### The table

Last 20 transactions, newest first, with a **Main driver** column naming the
biggest contributing feature. The newest row is highlighted.

## 9.4 What the numbers are not

Important for a viva, because an examiner may probe this.

- **Not persisted.** Everything is in process memory. A pod restart resets its
  counters to zero. That happens on every deploy.
- **Per replica.** Each pod counts independently. The dashboard sums the latest
  value it has seen from each pod so the total only goes up, but the underlying
  numbers are per-process.
- **Not a metrics system.** There is no Prometheus here. The durable, queryable
  record of every transaction is in Elasticsearch, which is what Kibana shows.

If asked "why not Prometheus?", the honest answer: the course rubric mandates
the ELK stack for logging, the HPA uses the metrics-server that ships with K3s,
and adding Prometheus would have cost another ~400 MB on an 8 GB laptop for no
extra marks.

## 9.5 The button

**"Score one transaction"** builds a random transaction in the browser — the same
shape as one row of the synthetic training data — and `POST`s it to `/score`.

It is the simplest way to produce a single, readable event when you want to show
the detail panel without running a load generator.

---

# Part 10 — Verification checklist

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

**Check 7 is the one people skip.** If it says `"source": "env"` or
`"generated"` instead of `"vault"`, the Vault role did not finish. Fix:

```bash
ansible-playbook ansible/site.yml --tags vault
kubectl -n fraudloop rollout restart deployment/scorer
```

---

# Part 11 — The demo

The order that shows every rubric item in about eight minutes.

**1. Push a change.** Edit the version string in `app/config.py`, commit, push.
Jenkins picks it up, runs the whole pipeline, deploys. Refresh the dashboard —
the build number and commit hash in the header change.
*This is the "new changes visible seamlessly" requirement.*

**2. Prove zero downtime.** Terminal 1:

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 80 --duration 70
```

Terminal 2, while it runs:

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

Trigger `fraudloop-drift` in Jenkins (or wait for the cron). It detects drift
and fires the delivery pipeline, which retrains, re-gates, and redeploys.

**6. Show Vault is load-bearing.**

```bash
kubectl -n vault scale deployment/vault --replicas=0
kubectl -n fraudloop rollout restart deployment/scorer
# the Signing key card flips from "vault" to "generated"
kubectl -n vault scale deployment/vault --replicas=1
ansible-playbook ansible/site.yml --tags vault
```

---

# Part 12 — Everyday operations

## Bring everything up from cold

```bash
open -a Docker                      # macOS; on Windows launch Docker Desktop
cd ~/fraudloop && source .venv/bin/activate
./scripts/preflight.sh
ansible-playbook ansible/site.yml
```

If the cluster was **deleted** (not just stopped) you must also redeploy the app —
see Part 5.4.

## From paused

```bash
open -a Docker
k3d cluster start fraudloop
cd compose && docker compose up -d
kubectl -n fraudloop rollout status deployment/scorer --timeout=120s
```

## Shut down

Four levels, pick by what you are doing next.

**Level 1 — stop looking at it.** Close the browser, `Ctrl-C` the port-forwards.
Everything keeps running.

**Level 2 — stop Jenkins only.**

```bash
cd compose && docker compose down
```

Jobs and credentials survive in the `jenkins_home` volume.

**Level 3 — pause the cluster (recommended for a break).**

```bash
k3d cluster stop fraudloop
cd compose && docker compose down
```

Keeps all cluster state — deployments, secrets, ELK indices. Fast to resume and
frees the RAM.

**Level 4 — full teardown.**

```bash
k3d cluster delete fraudloop
cd compose && docker compose down -v     # -v also drops the Jenkins volume
docker system prune -af
```

`-v` is the flag that matters: without it `jenkins_home` survives. With it you
are back to a first-run Jenkins.

## Port-forwards

Not persistent — they die when you close the terminal or the pod restarts.

```bash
kubectl -n logging port-forward svc/kibana 5601:5601
kubectl -n logging port-forward svc/elasticsearch 9200:9200
kubectl -n vault  port-forward svc/vault 8200:8200
```

The app (8080) and Jenkins (8090) do not need one.

## Generate traffic

```bash
python scripts/loadgen.py --url http://fraudloop.localhost:8080 --rate 20 --duration 30
```

`--rate` is requests per second, `--duration` is seconds. 120 rps is enough to
push the HPA to its maximum.

---

# Part 13 — Troubleshooting

## WSL2 specific

**`docker: command not found` inside Ubuntu.** Docker Desktop WSL integration is
off. Settings → Resources → WSL Integration → enable Ubuntu, restart the shell.

**`docker info` reports under 4 GB.** The memory setting did not apply. Change
it, click *Apply & restart*, confirm with `docker info --format '{{.MemTotal}}'`.

**Browser cannot reach localhost:8080.** Check the port is published:
`docker ps | grep 8080`. If not, the cluster was created without the port
mapping — `k3d cluster delete fraudloop` then
`ansible-playbook ansible/site.yml --tags cluster`.

**`fraudloop.localhost` does not resolve.** Part 2.4 — add the hosts entry, or
pass `-H "Host: fraudloop.localhost"`.

**Everything is slow.** The repo is on `/mnt/c`. Move it to `~/fraudloop`.

## General

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to import the required Python library (kubernetes)` | missing Python package | Part 4.1 |
| `readyz` returns 503 | no model in the image | `python ml/train.py` before `docker build` |
| Pods `ImagePullBackOff` | image not pushed, or wrong account | Part 6 |
| Elasticsearch `OOMKilled` | heap too large for the node | keep `-Xmx384m`; `kubectl top pods -n logging` |
| Kibana crash-loops with a V8 heap error | heap below ~512 MB | `NODE_OPTIONS` must stay `--max-old-space-size=640` |
| Logstash never ready | Elasticsearch not up first | `kubectl -n logging logs deploy/logstash` — it retries |
| HPA shows `<unknown>` | metrics-server still starting | wait 60 s, then `kubectl top pods -n fraudloop` |
| Jenkins cannot reach the cluster | kubeconfig points at 0.0.0.0 | `ansible-playbook ansible/site.yml --tags jenkins` |
| Pipeline fails at Push | `dockerhub` credential missing or misnamed | Part 7.3 |
| Dashboard numbers jumping between two values | two replicas, polled alternately | fixed — the dashboard sums across replicas. If it still jumps, hard-refresh the page |
| Dashboard shows 0 after a deploy | counters are per-process and reset on restart | expected, not a bug |

**When in doubt, re-run the playbook.** It is idempotent:

```bash
ansible-playbook ansible/site.yml
```

---

# Part 14 — Reference

## Repository layout

```
app/        FastAPI service, model loader, secret resolution, logging, dashboard
ml/         data generator, training with quality gate, drift check
tests/      14 tests covering the API contract and model behaviour
docker/     application image and CI image
k8s/        namespaces, config, deployment, service, ingress, HPA, PDB
ansible/    site.yml plus cluster, elk, vault, jenkins roles
jenkins/    delivery pipeline and scheduled drift pipeline
compose/    host-side Jenkins
scripts/    preflight, load generator, smoke test, Kibana provisioning
docs/       requirements analysis, plan, proposal, runbook, this guide
```

## Ports

| Port | What | Reachable from |
|---|---|---|
| 8080 | the application, via k3d load balancer | browser |
| 8090 | Jenkins | browser |
| 5601 | Kibana | port-forward only |
| 9200 | Elasticsearch | port-forward only |
| 8200 | Vault | port-forward only |

## Command cheat sheet

```bash
# platform
ansible-playbook ansible/site.yml
./scripts/preflight.sh

# app by hand
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

# lifecycle
k3d cluster stop fraudloop
k3d cluster start fraudloop
k3d cluster delete fraudloop
cd compose && docker compose down
cd compose && docker compose down -v
```

## Known limitations

Deliberate, documented, and worth knowing before a viva.

- **Vault runs in dev mode.** In-memory storage, fixed root token. The
  application-facing contract — policy-scoped token, KV v2 path — is real, but a
  restart loses the secret until the playbook re-seeds it.
- **Elasticsearch has security disabled.** Single-node local cluster, not
  exposed beyond the port-forward.
- **Logs ship from the app directly to Logstash over TCP**, not through
  Filebeat. Keeps a DaemonSet off an 8 GB laptop. `kubectl logs` still works.
- **The cluster is not highly available.** One server, one agent. The
  zero-downtime guarantee is about pods, not nodes.
- **Dashboard counters are in process memory.** They reset on restart and are
  not aggregated across the cluster by any server-side mechanism — the browser
  does the summing.
