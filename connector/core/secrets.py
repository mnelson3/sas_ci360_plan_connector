# coding=utf-8
"""
Secret provider contract.

Each cloud adapter implements fetch_secrets() against its own secret store
(Azure Key Vault, AWS Secrets Manager, GCP Secret Manager) and returns the
same shape, so core.offers never needs to know which cloud it's running on.

Required keys:
    ci360_connector_url                - base URL of the CI360 Plan connector
    ci360_connector_api_tenant_id       - CI360 tenant id for this connector
    ci360_connector_api_secret          - CI360 connector shared secret
    partner_api_identifier              - partner (offer/coupon platform) API key id
    partner_api_secret                  - partner API shared secret, used to sign requests
    partner_api_url                     - base URL of the partner API
"""

from typing import Protocol

REQUIRED_SECRET_KEYS = (
    "ci360_connector_url",
    "ci360_connector_api_tenant_id",
    "ci360_connector_api_secret",
    "partner_api_identifier",
    "partner_api_secret",
    "partner_api_url",
)


class SecretProvider(Protocol):
    def fetch_secrets(self) -> dict:
        """Return a dict containing at least REQUIRED_SECRET_KEYS."""
        ...


def validate_secrets(secrets: dict) -> None:
    missing = [key for key in REQUIRED_SECRET_KEYS if not secrets.get(key)]
    if missing:
        raise ValueError("Missing required secret(s): {0}".format(", ".join(missing)))
