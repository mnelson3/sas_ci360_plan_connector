# coding=utf-8
"""Google Secret Manager implementation of core.secrets.SecretProvider.

Like the AWS adapter, stores every required key (see core/secrets.py) as
one JSON secret rather than one secret per value. Set GCP_PROJECT_ID and
GCP_SECRET_ID as environment variables on each Cloud Function.
"""

import json
import logging
import os
from typing import Optional

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class GCPSecretManagerSecretProvider:
    def __init__(self, project_id: Optional[str] = None, secret_id: Optional[str] = None, version: str = "latest"):
        self.project_id = project_id or os.environ["GCP_PROJECT_ID"]
        self.secret_id = secret_id or os.environ["GCP_SECRET_ID"]
        self.version = version

    def fetch_secrets(self) -> dict:
        client = secretmanager.SecretManagerServiceClient()
        name = "projects/{0}/secrets/{1}/versions/{2}".format(
            self.project_id, self.secret_id, self.version
        )
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)
