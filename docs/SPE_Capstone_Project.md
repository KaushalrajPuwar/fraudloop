**CSE 816 — Software Production Engineering**

**Capstone Project (25 Marks) — Problem Statement**

*End-to-End DevOps Project — Team of Two*

M.Tech (CSE) — Term I, 2026-27

**Faculty: Prof. B. Thangaraju**

| Item | Detail |
| ----- | ----- |
| **Project type** | Team of two (2 students) · end-to-end DevOps project |
| **Weightage** | 25 marks (25% of course) |
| **Domain** | Free choice — any domain/application the team is passionate about |
| **Infrastructure** | Local Kubernetes clusters (Minikube / kind / K3s) — laptop-runnable |
| **Kicked off** | Class 20 — Wed, 04-Nov-2026 |
| **Final demo** | End Term Exam window, 07-12 Dec-2026 |

# **1\. Objective**

Working in a team of two, design and build a complete, automated, end-to-end DevOps pipeline for an application of your choice. The mini-project introduced the pipeline on a fixed, simple application using a fixed toolset. The capstone removes those guardrails: you choose the domain, you choose the architecture, and you choose your tools — provided you demonstrate every stage of the DevOps lifecycle and add at least one cutting-edge capability beyond what was taught in class.

**Philosophy:** We assess DevOps engineering, not application complexity. A simple app with a flawless, automated, observable pipeline scores far higher than an impressive app deployed by hand.

# **2\. Team & Domain**

* Teams of exactly two students. Both members must contribute to code and to DevOps work — this will be verified by Git history and an individual viva.

* Free choice of domain and application. Pick something you care about; you will work on it for \~5 weeks.

* Each team registers its topic and a one-paragraph abstract on the shared sheet at kickoff so the class can see the spread of ideas.

* Two teams may work in the same domain, but the applications and pipelines must be your own original work.

## **2.1 Suggested domain tracks (for inspiration — not mandatory)**

| Track | Example project idea |
| ----- | ----- |
| Full-stack web app | Multi-tier web app (frontend \+ API \+ DB) with GitOps-driven deployment |
| Machine Learning / MLOps | Training→serving pipeline (MLflow / KServe) with automated retraining |
| AI / LLMOps | LLM-backed app with CI/CD, model/version registry, request tracing |
| Security / DevSecOps | Pipeline hardened with scanning, SBOM, image signing, policy-as-code |
| Networking / Service Mesh | Istio/Linkerd mesh with eBPF (Cilium) observability |
| Deep Learning | GPU/accelerated workload on K8s with a distributed training pipeline |
| IoT / Edge / Embedded / Real-time | K3s or KubeEdge cluster; edge deployment pipeline (e.g. Pi fleet) |
| Platform Engineering | Internal developer platform with Backstage \+ Crossplane self-service |

# **3\. Mandatory Pipeline Stages (flexible tools)**

Your pipeline must cover every stage below, end to end and automated. The course tool is the default and is always acceptable; the alternatives show the freedom you have. You may mix and match, but every stage must be present and demonstrably working.

| DevOps stage | Course default | Acceptable alternatives |
| ----- | ----- | ----- |
| Source control | Git \+ GitHub | GitLab, Bitbucket |
| CI / CD | Jenkins | GitHub Actions, GitLab CI, Jenkins X, Tekton, Argo CD/Flux (GitOps) |
| Build & containerize | Docker | Buildah/Podman, Cloud Native Buildpacks, Kaniko |
| Config mgmt / IaC | Ansible | Terraform, Pulumi, Helm, Crossplane |
| Orchestration / deploy | Kubernetes (local) | kind, K3s, KubeEdge; Argo Rollouts for progressive delivery |
| Monitoring / observability | Prometheus \+ Grafana | OpenTelemetry, Loki, Tempo/Jaeger, eBPF (Cilium/Pixie) |

**Requirement:** a single code change pushed to your repository should flow automatically through build → test → image → deploy to your local cluster, with the running application observable in your monitoring stack.

# **4\. Cutting-Edge Extension (required — at least one)**

Beyond the baseline, every team must integrate at least one current, industry-relevant capability. This is where the project earns its innovation marks. Pick what fits your domain:

## **GitOps & progressive delivery**

Argo CD / Flux for Git-driven deployment; Argo Rollouts for canary or blue-green releases.

## **Observability 2.0**

OpenTelemetry (instrument once, export anywhere); eBPF-based zero-instrumentation tracing (Cilium/Pixie); distributed tracing with Tempo/Jaeger; logs with Loki.

## **DevSecOps & software supply chain**

SAST/DAST (SonarQube, Trivy, Snyk); SBOM generation; image signing with Sigstore/Cosign; policy-as-code with OPA/Gatekeeper; secrets with HashiCorp Vault.

## **Platform engineering**

Internal developer platform with Backstage; Kubernetes-native infrastructure with Crossplane.

## **AIOps / LLMOps & others**

AI-assisted anomaly detection on metrics/pipelines; MLflow/Kubeflow/KServe for ML; chaos engineering with LitmusChaos / Chaos Mesh; service mesh with Istio/Linkerd.

# **5\. Infrastructure Constraints**

* The entire project must run on local clusters (Minikube, kind, or K3s) on your own laptops — no paid cloud is required.

* If you use any free-tier cloud service it must be optional; the project must still demonstrate fully on a laptop for the viva.

* Keep resource usage realistic for a laptop; document the minimum specs needed to run your stack.

# **6\. Milestones & Timeline**

| Milestone | Target | Deliverable |
| ----- | ----- | ----- |
| Kickoff & registration | Class 20 (04-Nov) | Team formed, topic \+ abstract registered |
| Proposal approved | \~11-Nov | 1-page proposal: app, architecture, chosen tools, extension |
| Pipeline working | \~Class 25 (25-Nov) | Automated CI/CD building and deploying to local cluster |
| Deployed \+ observable | \~02-Dec | App running on K8s with monitoring dashboards live |
| Final briefing | Class 28 (04-Dec) | Demo logistics, report submission window opens |
| Final demo & viva | 07-12 Dec | Live end-to-end demo \+ individual Q\&A |

# **7\. Deliverables**

1. Git repository (GitHub/GitLab) containing all source, pipeline definitions, IaC, and Kubernetes manifests.

2. A one-page proposal (approved milestone) and a final report (4-6 pages, PDF): architecture diagram, tool choices and rationale, the cutting-edge extension, and challenges.

3. A working demonstration: push a change and show it flow end-to-end to the running cluster, with monitoring.

4. A short screen-recorded backup of the full pipeline run, in case of live-demo issues.

5. Individual contribution statement signed by both members.

# **8\. Evaluation Rubric (25 Marks)**

Criteria are stage-based and tool-agnostic — you are marked on whether each DevOps stage is present, automated, and sound, regardless of which tool you chose.

| Criterion | Marks | Focus |
| ----- | ----- | ----- |
| Proposal & architecture design | 3.0 | Design |
| Version control & team collaboration (both members) | 2.0 | VCS |
| CI/CD pipeline (automated build/test/deploy) | 4.0 | CI/CD |
| Containerization & Kubernetes orchestration | 5.0 | Containers/K8s |
| Configuration management / IaC | 2.0 | IaC |
| Monitoring & observability | 3.0 | Observability |
| Cutting-edge extension (innovation & correctness) | 4.0 | Innovation |
| Report, live demo & individual viva | 2.0 | Demo/Viva |
| **Total** | **25.0** |  |

# **9\. Policies**

* Both teammates are assessed individually at the viva; marks may differ within a team based on demonstrated understanding and Git contribution.

* Reusing another team's repository, pipeline, or manifests is plagiarism. You may use open-source components and AI assistants, but you must understand and be able to explain everything you submit.

* Progressive commits from both members are expected; a repository with last-minute, single-author history will lose collaboration marks.

* The pipeline must genuinely run during the viva; screenshots or recordings alone do not earn the deployment and observability marks.

*Tip: build on your mini-project. Your Calculator pipeline already covers Git → CI → Docker. Extend that muscle memory to Kubernetes, IaC, monitoring, and one cutting-edge capability, and you have a capstone.*

# **10\. Example Project Topics (60)**

The following 60 ideas are starting points, not a fixed list — teams may pick any of them or propose their own. Every project must still cover the full pipeline (Section 3\) on a local cluster and integrate at least one cutting-edge extension (Section 4). The *Cutting-edge* note on each idea is only a suggestion.

## **Full-Stack Web Applications  (10)**

**1\. E-Commerce Storefront —** Containerize a multi-tier shopping app (catalog, cart, mock payments) and deploy to Kubernetes with horizontal autoscaling under load.  *Cutting-edge: Argo Rollouts canary releases*

**2\. Blogging / CMS Platform —** Build a CI/CD pipeline for a content-management app with database persistence and full-text search.  *Cutting-edge: GitOps with Argo CD*

**3\. Online Learning Portal (LMS) —** Deploy a course platform (lessons, quizzes, progress) and monitor end-to-end request latency.  *Cutting-edge: OpenTelemetry distributed tracing*

**4\. Job Board & Applicant Tracker —** Multi-service app with role-based access and automated test gates in the pipeline.  *Cutting-edge: DevSecOps scanning (Trivy \+ SonarQube)*

**5\. Real-Time Chat Application —** WebSocket-based chat that scales horizontally on Kubernetes.  *Cutting-edge: Service mesh (Linkerd) traffic management*

**6\. URL Shortener with Analytics —** High-throughput redirect service plus an analytics dashboard.  *Cutting-edge: Custom Prometheus metrics \+ Grafana SLOs*

**7\. Personal Finance / Expense Tracker —** Budget app with secure handling of credentials and user secrets.  *Cutting-edge: HashiCorp Vault for secrets*

**8\. Hotel / Flight Booking System —** Microservices (search, booking, payment) with inter-service communication.  *Cutting-edge: Distributed tracing (Jaeger / Tempo)*

**9\. Social Media Feed App —** Feed service with a Redis caching layer, deployed via Helm.  *Cutting-edge: Blue-green progressive delivery*

**10\. Food Delivery Tracker —** Order and delivery tracking with live status updates and resilience testing.  *Cutting-edge: Chaos engineering (LitmusChaos)*

## **Machine Learning / MLOps  (8)**

**11\. House-Price Prediction MLOps —** Train, register, and serve a regression model with automated retraining on new data.  *Cutting-edge: MLflow \+ KServe*

**12\. Sentiment Analysis Pipeline —** CI/CD that retrains a text classifier and redeploys the model API automatically.  *Cutting-edge: Model registry \+ drift monitoring*

**13\. Image Classification Service —** Containerized inference API serving versioned image models.  *Cutting-edge: Kubeflow Pipelines*

**14\. Recommendation Engine —** Batch training plus online serving with A/B testing of competing models.  *Cutting-edge: Argo Rollouts model canary*

**15\. Fraud Detection Pipeline —** Feature pipeline and model serving with monitoring of live prediction metrics.  *Cutting-edge: Prometheus model metrics \+ alerting*

**16\. Spam Email Filter —** End-to-end flow from data preparation to a deployed classifier service.  *Cutting-edge: GitOps for model manifests*

**17\. Customer Churn Predictor —** Scheduled retraining via CI with dashboarded model performance.  *Cutting-edge: MLflow tracking server*

**18\. Demand Forecasting Service —** Time-series model retrained on a schedule and served on Kubernetes.  *Cutting-edge: Drift detection \+ automated rollback*

## **Artificial Intelligence / LLMOps  (8)**

**19\. RAG Document Q\&A App —** LLM plus vector-database app with CI/CD and tracing of every retrieval/inference call.  *Cutting-edge: OpenTelemetry for LLM calls*

**20\. AI FAQ Chatbot —** Containerized LLM-backed chatbot with versioned prompts and safe rollout.  *Cutting-edge: Prompt/version registry \+ canary*

**21\. AI Code-Review Assistant —** LLM service wired into a CI pipeline to comment automatically on pull requests.  *Cutting-edge: GitHub/GitLab CI integration*

**22\. AI Image Generation Service —** GPU-aware inference deployment that autoscales with demand.  *Cutting-edge: KEDA event-driven autoscaling*

**23\. Summarization Microservice —** LLM summarizer with rate limiting and observability of token usage and cost.  *Cutting-edge: Cost/usage dashboards in Grafana*

**24\. Multilingual Translation API —** Translation model served behind a cache, traced without code changes.  *Cutting-edge: eBPF zero-instrumentation tracing*

**25\. Voice-to-Text Transcription —** Speech model serving fed by an asynchronous job queue.  *Cutting-edge: KEDA queue-based autoscaling*

**26\. AI Agent Orchestration —** Deploy a multi-step agent workflow with monitoring of each agent action.  *Cutting-edge: OpenTelemetry agent tracing*

## **Security / DevSecOps  (8)**

**27\. Secure CI/CD Reference Pipeline —** Pipeline with SAST, DAST, dependency and image-scanning gates that block bad builds.  *Cutting-edge: SonarQube \+ Trivy \+ OWASP ZAP*

**28\. Software Supply-Chain Security —** Generate SBOMs, sign images, and verify signatures at deploy time.  *Cutting-edge: Sigstore / Cosign \+ admission policy*

**29\. Policy-as-Code Governance —** Enforce Kubernetes security policies automatically on every deployment.  *Cutting-edge: OPA/Gatekeeper or Kyverno*

**30\. Secrets Management Platform —** Centralized secrets with dynamic, short-lived credentials for an app.  *Cutting-edge: HashiCorp Vault*

**31\. Container Image Hardening —** Pipeline that builds minimal, non-root, scanned images behind a security gate.  *Cutting-edge: Distroless images \+ Trivy gate*

**32\. Vulnerability Dashboard —** Aggregate scan results across services into a single dashboard.  *Cutting-edge: DefectDojo / Grafana*

**33\. Zero-Trust Microservice Auth —** Mutual TLS and authorization policies between services via a mesh.  *Cutting-edge: Istio mTLS \+ authorization policies*

**34\. Runtime Threat Detection —** Detect anomalous container/process behaviour at runtime.  *Cutting-edge: Falco / eBPF*

## **Networking / Service Mesh  (6)**

**35\. Service-Mesh Traffic Management —** Microservices with canary, retries, and timeouts driven by the mesh.  *Cutting-edge: Istio traffic policies*

**36\. eBPF Network Observability —** Visualize service-to-service traffic with no application code changes.  *Cutting-edge: Cilium Hubble*

**37\. API Gateway \+ Rate Limiting —** Gateway fronting microservices with quotas and exported metrics.  *Cutting-edge: Kong / Envoy \+ Prometheus*

**38\. Multi-Cluster Networking —** Connect two local clusters and route traffic between them.  *Cutting-edge: Cilium ClusterMesh / Submariner*

**39\. Network Policy Enforcement —** Implement and test Kubernetes NetworkPolicies for workload isolation.  *Cutting-edge: Cilium policies \+ audit logging*

**40\. Ingress, LB & DNS Routing —** Service demonstrating ingress, load balancing, and DNS-based routing.  *Cutting-edge: MetalLB \+ ExternalDNS*

## **Deep Learning  (5)**

**41\. Distributed Model Training —** Multi-pod training job orchestrated across the cluster.  *Cutting-edge: Kubeflow Training Operator*

**42\. GPU-Accelerated Inference —** Serve a CNN with GPU scheduling and request-based autoscaling.  *Cutting-edge: NVIDIA device plugin \+ KServe*

**43\. Object-Detection Pipeline —** Labeling to training to serving flow for a detection model.  *Cutting-edge: Argo Workflows orchestration*

**44\. Neural Style-Transfer Service —** Containerized DL inference with batched processing.  *Cutting-edge: Queue-based autoscaling*

**45\. Federated Learning Simulation —** Coordinate training across simulated edge nodes with central aggregation.  *Cutting-edge: K3s edge nodes \+ aggregator*

## **IoT / Edge / Embedded / Real-Time  (8)**

**46\. Smart-Home Telemetry Platform —** Ingest data from simulated sensors and deploy to an edge cluster.  *Cutting-edge: K3s \+ MQTT broker*

**47\. Edge ML Inference —** Deploy a model to edge devices with over-the-air model updates.  *Cutting-edge: KubeEdge*

**48\. Industrial Sensor Monitoring —** Real-time machine-sensor metrics with threshold-based alerting.  *Cutting-edge: Prometheus \+ Alertmanager at the edge*

**49\. IoT Fleet Device Management —** Manage and update a fleet of simulated devices via GitOps.  *Cutting-edge: Flux / Argo CD at the edge*

**50\. Real-Time Traffic Data Pipeline —** Stream and process vehicle/traffic events with low latency.  *Cutting-edge: Kafka \+ stream processing*

**51\. Air-Quality Monitoring —** Collect, store, and dashboard environmental sensor readings.  *Cutting-edge: TimescaleDB / Prometheus \+ Grafana*

**52\. Edge Video Analytics —** Run inference on a video stream at the edge with central monitoring.  *Cutting-edge: KubeEdge \+ lightweight model*

**53\. Wearable Health-Data Service —** Ingest and process simulated wearable data with secure storage.  *Cutting-edge: Edge K3s \+ Vault*

## **Platform Engineering  (7)**

**54\. Internal Developer Platform (IDP) —** Self-service portal where developers deploy services with one click.  *Cutting-edge: Backstage developer portal*

**55\. Self-Service Infrastructure —** Let teams provision namespaces and databases declaratively.  *Cutting-edge: Crossplane*

**56\. Golden-Path Service Templates —** Scaffolding plus CI/CD templates for spinning up new microservices.  *Cutting-edge: Backstage software templates*

**57\. Multi-Tenant Kubernetes Platform —** Namespace isolation, quotas, and RBAC for multiple teams.  *Cutting-edge: vCluster / Capsule*

**58\. Progressive-Delivery Platform —** Standardize canary and blue-green deploys across all services.  *Cutting-edge: Argo Rollouts \+ Argo CD*

**59\. Observability-as-a-Platform —** One command to add metrics, logs, and traces to any new service.  *Cutting-edge: OpenTelemetry Operator \+ LGTM stack*

**60\. Cost & Resource Governance —** Dashboard and enforce resource/cost limits across the cluster.  *Cutting-edge: OpenCost / Kubecost*