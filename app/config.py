"""Runtime configuration, read once from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    """Everything the service needs to boot.

    Built from environment variables so the same image runs locally, in
    Docker Compose, and in Kubernetes without modification.
    """

    # Kubernetes sets HOSTNAME to the pod name; used to tell replicas apart.
    pod: str = field(default_factory=lambda: _env("HOSTNAME", "local") or "local")

    # Build identity - baked into the image at build time, shown on the dashboard.
    version: str = field(default_factory=lambda: _env("APP_VERSION", "0.1.0") or "0.1.0")
    build_number: str = field(default_factory=lambda: _env("BUILD_NUMBER", "dev") or "dev")
    git_sha: str = field(default_factory=lambda: _env("GIT_SHA", "unknown") or "unknown")

    # Model artifacts.
    model_dir: Path = field(default_factory=lambda: Path(_env("MODEL_DIR", "artifacts") or "artifacts"))

    # Logging.
    log_level: str = field(default_factory=lambda: (_env("LOG_LEVEL", "INFO") or "INFO").upper())
    logstash_host: str | None = field(default_factory=lambda: _env("LOGSTASH_HOST"))
    logstash_port: int = field(default_factory=lambda: int(_env("LOGSTASH_PORT", "5000") or 5000))

    # Vault.
    vault_addr: str | None = field(default_factory=lambda: _env("VAULT_ADDR"))
    vault_token: str | None = field(default_factory=lambda: _env("VAULT_TOKEN"))
    vault_secret_path: str = field(
        default_factory=lambda: _env("VAULT_SECRET_PATH", "secret/data/fraudloop/api-key")
        or "secret/data/fraudloop/api-key"
    )
    # Used when Vault is unreachable so local development still works.
    fallback_api_key: str | None = field(default_factory=lambda: _env("APP_API_KEY"))

    # Behaviour.
    fraud_threshold: float = field(
        default_factory=lambda: float(_env("FRAUD_THRESHOLD", "0.5") or 0.5)
    )
    stats_window: int = field(default_factory=lambda: int(_env("STATS_WINDOW", "500") or 500))
    recent_window: int = field(default_factory=lambda: int(_env("RECENT_WINDOW", "20") or 20))

    @property
    def logstash_enabled(self) -> bool:
        return bool(self.logstash_host)

    @property
    def vault_enabled(self) -> bool:
        return bool(self.vault_addr and self.vault_token)
