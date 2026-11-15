# syntax=docker/dockerfile:1

# ---------- build stage: resolve dependencies once ----------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ---------- runtime stage ----------
FROM python:3.12-slim AS runtime

# Build identity, baked in so the dashboard can prove which commit is live.
ARG APP_VERSION=0.1.0
ARG BUILD_NUMBER=dev
ARG GIT_SHA=unknown

ENV APP_VERSION=${APP_VERSION} \
    BUILD_NUMBER=${BUILD_NUMBER} \
    GIT_SHA=${GIT_SHA} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_DIR=/app/artifacts \
    PORT=8000

COPY --from=builder /install /usr/local

RUN groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid app --no-create-home app

WORKDIR /app
COPY --chown=app:app app/ ./app/
COPY --chown=app:app artifacts/ ./artifacts/

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
