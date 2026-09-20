# coding=utf-8
"""Azure Key Vault implementation of core.secrets.SecretProvider."""

import logging
import os
from typing import Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

# Maps this connector's secret keys (see core/secrets.py) to the secret
# names stored in Key Vault. Set AZURE_KEY_VAULT_NAME as an app setting -
# never hardcode a vault name here.
SECRET_NAME_MAP = {
    "ci360_connector_url": "ci360-connector-url",
    "ci360_connector_api_tenant_id": "ci360-connector-api-tenant-id",
    "ci360_connector_api_secret": "ci360-connector-api-secret",
    "partner_api_identifier": "partner-api-identifier",
    "partner_api_secret": "partner-api-secret",
    "partner_api_url": "partner-api-url",
}


class AzureKeyVaultSecretProvider:
    def __init__(self, vault_name: Optional[str] = None):
        self.vault_name = vault_name or os.environ["AZURE_KEY_VAULT_NAME"]
        self.vault_uri = "https://{0}.vault.azure.net/".format(self.vault_name)

    def fetch_secrets(self) -> dict:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=self.vault_uri, credential=credential)

        result = {}
        for key, secret_name in SECRET_NAME_MAP.items():
            try:
                result[key] = client.get_secret(secret_name).value
            except ResourceNotFoundError:
                logger.warning("Secret not found in Key Vault: %s", secret_name)
                result[key] = None
        return result
