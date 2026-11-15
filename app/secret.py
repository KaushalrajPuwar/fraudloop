"""Fetching the API signing key, preferring HashiCorp Vault."""

from __future__ import annotations

import hashlib
import logging
import secrets as _secrets
from dataclasses import dataclass

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

VAULT_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class Secret:
    """A secret value plus where it came from, for display and debugging."""

    value: str
    source: str  # "vault" | "env" | "generated"

    @property
    def fingerprint(self) -> str:
        """A stable, non-reversible identifier safe to show on a dashboard."""
        return hashlib.sha256(self.value.encode("utf-8")).hexdigest()[:12]


def _fetch_from_vault(settings: Settings) -> str:
    """Read the API key from a Vault KV v2 path."""
    url = f"{settings.vault_addr.rstrip('/')}/v1/{settings.vault_secret_path.lstrip('/')}"
    response = httpx.get(
        url,
        headers={"X-Vault-Token": settings.vault_token or ""},
        timeout=VAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    api_key = payload["data"]["data"]["api_key"]
    if not api_key:
        raise ValueError("api_key present in Vault but empty")
    return str(api_key)


def load_secret(settings: Settings) -> Secret:
    """Resolve the signing key, falling back so local runs still work.

    The fallback is deliberate: Vault is a single point of failure, and a
    scoring service that refuses to boot because a secret store is down is
    worse than one that logs loudly and degrades.
    """
    if settings.vault_enabled:
        try:
            return Secret(value=_fetch_from_vault(settings), source="vault")
        except Exception as exc:  # noqa: BLE001 - any failure means fall back
            logger.warning(
                "vault_unavailable",
                extra={"vault_addr": settings.vault_addr, "error": str(exc)},
            )

    if settings.fallback_api_key:
        return Secret(value=settings.fallback_api_key, source="env")

    logger.warning("secret_generated", extra={"reason": "no vault and no APP_API_KEY"})
    return Secret(value=_secrets.token_hex(16), source="generated")
