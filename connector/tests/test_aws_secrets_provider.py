# coding=utf-8
"""Tests for aws.secrets_provider, stubbing boto3."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

from _fakes import install_fake_module

AWS_DIR = Path(__file__).parents[1] / "aws"

_boto3 = install_fake_module("boto3")
if not hasattr(_boto3, "client"):
    _boto3.client = MagicMock(name="boto3.client")

boto3_client = _boto3.client


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_aws_secrets_provider_under_test", AWS_DIR / "secrets_provider.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = _load_module()

SECRETS_JSON = json.dumps({
    "ci360_connector_url": "https://ci360.example.com/",
    "ci360_connector_api_tenant_id": "tenant-123",
    "ci360_connector_api_secret": "connector-secret",
    "partner_api_identifier": "partner-id",
    "partner_api_secret": "partner-secret",
    "partner_api_url": "https://partner.example.com/",
})


def test_reads_secret_name_from_argument(monkeypatch):
    monkeypatch.delenv("SECRETS_MANAGER_SECRET_NAME", raising=False)
    provider = module.AWSSecretsManagerSecretProvider(secret_name="my-secret")
    assert provider.secret_name == "my-secret"


def test_reads_secret_name_from_env_when_not_given(monkeypatch):
    monkeypatch.setenv("SECRETS_MANAGER_SECRET_NAME", "env-secret")
    provider = module.AWSSecretsManagerSecretProvider()
    assert provider.secret_name == "env-secret"


def test_missing_secret_name_raises(monkeypatch):
    monkeypatch.delenv("SECRETS_MANAGER_SECRET_NAME", raising=False)
    try:
        module.AWSSecretsManagerSecretProvider()
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_region_defaults_to_the_aws_region_env_var(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    provider = module.AWSSecretsManagerSecretProvider(secret_name="s")
    assert provider.region_name == "us-east-1"


def test_fetch_secrets_parses_the_json_secret_string(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    boto3_client.reset_mock()
    boto3_client.return_value.get_secret_value.return_value = {"SecretString": SECRETS_JSON}

    result = module.AWSSecretsManagerSecretProvider(secret_name="my-secret").fetch_secrets()

    assert result["partner_api_identifier"] == "partner-id"
    boto3_client.assert_called_once_with("secretsmanager", region_name=None)


def test_fetch_secrets_requests_the_configured_secret_name(monkeypatch):
    boto3_client.reset_mock()
    boto3_client.return_value.get_secret_value.return_value = {"SecretString": SECRETS_JSON}

    module.AWSSecretsManagerSecretProvider(secret_name="named-secret").fetch_secrets()

    boto3_client.return_value.get_secret_value.assert_called_once_with(SecretId="named-secret")
