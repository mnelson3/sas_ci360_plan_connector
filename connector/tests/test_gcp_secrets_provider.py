# coding=utf-8
"""Tests for gcp.secrets_provider, stubbing google-cloud-secret-manager."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

from _fakes import install_fake_module

GCP_DIR = Path(__file__).parents[1] / "gcp"

_secretmanager = install_fake_module("google.cloud.secretmanager")
if not hasattr(_secretmanager, "SecretManagerServiceClient"):
    _secretmanager.SecretManagerServiceClient = MagicMock(name="SecretManagerServiceClient")

SecretManagerServiceClient = _secretmanager.SecretManagerServiceClient


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_gcp_secrets_provider_under_test", GCP_DIR / "secrets_provider.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = _load_module()

SECRETS_JSON = json.dumps({
    "ci360_connector_url": "https://ci360.example.com/",
    "partner_api_identifier": "partner-id",
})


def test_reads_project_and_secret_id_from_arguments(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCP_SECRET_ID", raising=False)
    provider = module.GCPSecretManagerSecretProvider(project_id="my-proj", secret_id="my-secret")
    assert provider.project_id == "my-proj"
    assert provider.secret_id == "my-secret"
    assert provider.version == "latest"


def test_reads_project_and_secret_id_from_env_when_not_given(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "env-proj")
    monkeypatch.setenv("GCP_SECRET_ID", "env-secret")
    provider = module.GCPSecretManagerSecretProvider()
    assert provider.project_id == "env-proj"
    assert provider.secret_id == "env-secret"


def test_missing_project_id_raises(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.setenv("GCP_SECRET_ID", "env-secret")
    try:
        module.GCPSecretManagerSecretProvider()
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_fetch_secrets_builds_the_versioned_resource_name_and_parses_json():
    SecretManagerServiceClient.reset_mock()
    response = MagicMock()
    response.payload.data = SECRETS_JSON.encode("utf-8")
    SecretManagerServiceClient.return_value.access_secret_version.return_value = response

    provider = module.GCPSecretManagerSecretProvider(project_id="my-proj", secret_id="my-secret")
    result = provider.fetch_secrets()

    assert result["partner_api_identifier"] == "partner-id"
    called_kwargs = SecretManagerServiceClient.return_value.access_secret_version.call_args.kwargs
    assert called_kwargs["request"] == {"name": "projects/my-proj/secrets/my-secret/versions/latest"}


def test_fetch_secrets_honors_an_explicit_version():
    SecretManagerServiceClient.reset_mock()
    response = MagicMock()
    response.payload.data = SECRETS_JSON.encode("utf-8")
    SecretManagerServiceClient.return_value.access_secret_version.return_value = response

    provider = module.GCPSecretManagerSecretProvider(project_id="p", secret_id="s", version="3")
    provider.fetch_secrets()

    called_kwargs = SecretManagerServiceClient.return_value.access_secret_version.call_args.kwargs
    assert called_kwargs["request"] == {"name": "projects/p/secrets/s/versions/3"}
