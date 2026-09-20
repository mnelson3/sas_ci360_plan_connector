# coding=utf-8
"""Tests for azure.secrets_provider, stubbing azure-identity/azure-keyvault."""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

from _fakes import install_fake_module

AZURE_DIR = Path(__file__).parents[1] / "azure"

_core_exceptions = install_fake_module("azure.core.exceptions")
if not hasattr(_core_exceptions, "ResourceNotFoundError"):
    class ResourceNotFoundError(Exception):
        pass

    _core_exceptions.ResourceNotFoundError = ResourceNotFoundError

_identity = install_fake_module("azure.identity")
if not hasattr(_identity, "DefaultAzureCredential"):
    _identity.DefaultAzureCredential = MagicMock(name="DefaultAzureCredential")

_secrets_mod = install_fake_module("azure.keyvault.secrets")
if not hasattr(_secrets_mod, "SecretClient"):
    _secrets_mod.SecretClient = MagicMock(name="SecretClient")

ResourceNotFoundError = _core_exceptions.ResourceNotFoundError
SecretClient = _secrets_mod.SecretClient


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_azure_secrets_provider_under_test", AZURE_DIR / "secrets_provider.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = _load_module()


def _get_secret(value=None, raises=False):
    def _fn(name):
        if raises:
            raise ResourceNotFoundError(name)
        result = MagicMock()
        result.value = value if value is not None else "value-for-{0}".format(name)
        return result
    return _fn


def test_reads_vault_name_from_argument(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_NAME", raising=False)
    provider = module.AzureKeyVaultSecretProvider(vault_name="my-vault")
    assert provider.vault_name == "my-vault"
    assert provider.vault_uri == "https://my-vault.vault.azure.net/"


def test_reads_vault_name_from_env_when_not_given(monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_NAME", "env-vault")
    provider = module.AzureKeyVaultSecretProvider()
    assert provider.vault_name == "env-vault"


def test_missing_vault_name_raises(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_NAME", raising=False)
    try:
        module.AzureKeyVaultSecretProvider()
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_fetch_secrets_maps_every_key_to_its_vault_secret(monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_NAME", "my-vault")
    SecretClient.return_value.get_secret.side_effect = _get_secret()

    result = module.AzureKeyVaultSecretProvider().fetch_secrets()

    assert set(result) == set(module.SECRET_NAME_MAP)
    for key, secret_name in module.SECRET_NAME_MAP.items():
        assert result[key] == "value-for-{0}".format(secret_name)


def test_fetch_secrets_returns_none_for_a_missing_secret(monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_NAME", "my-vault")

    def _side_effect(name):
        if name == "ci360-connector-url":
            raise ResourceNotFoundError(name)
        return _get_secret()(name)

    SecretClient.return_value.get_secret.side_effect = _side_effect

    result = module.AzureKeyVaultSecretProvider().fetch_secrets()

    assert result["ci360_connector_url"] is None
    assert result["partner_api_secret"] is not None


def test_fetch_secrets_builds_client_with_the_vault_uri(monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_NAME", "another-vault")
    SecretClient.reset_mock()
    SecretClient.return_value.get_secret.side_effect = _get_secret()

    module.AzureKeyVaultSecretProvider().fetch_secrets()

    _, kwargs = SecretClient.call_args
    assert kwargs["vault_url"] == "https://another-vault.vault.azure.net/"
