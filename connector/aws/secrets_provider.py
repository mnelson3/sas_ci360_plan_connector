# coding=utf-8
"""AWS Secrets Manager implementation of core.secrets.SecretProvider.

Stores every required key (see core/secrets.py) as one JSON secret, rather
than one secret per value - the idiomatic pattern for Secrets Manager.
Set SECRETS_MANAGER_SECRET_NAME as a Lambda environment variable.
"""

import json
import logging
import os
from typing import Optional

import boto3

logger = logging.getLogger(__name__)


class AWSSecretsManagerSecretProvider:
    def __init__(self, secret_name: Optional[str] = None, region_name: Optional[str] = None):
        self.secret_name = secret_name or os.environ["SECRETS_MANAGER_SECRET_NAME"]
        self.region_name = region_name or os.environ.get("AWS_REGION")

    def fetch_secrets(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region_name)
        response = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(response["SecretString"])
