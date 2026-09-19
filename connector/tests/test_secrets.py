# coding=utf-8
"""Tests for core.secrets.validate_secrets."""

import pytest

from core.secrets import REQUIRED_SECRET_KEYS, validate_secrets


def _complete_secrets() -> dict:
    return {key: "value-for-{0}".format(key) for key in REQUIRED_SECRET_KEYS}


def test_validate_secrets_accepts_a_complete_dict():
    validate_secrets(_complete_secrets())


def test_validate_secrets_rejects_a_missing_key():
    secrets = _complete_secrets()
    del secrets["partner_api_secret"]

    with pytest.raises(ValueError, match="partner_api_secret"):
        validate_secrets(secrets)


def test_validate_secrets_rejects_an_empty_value():
    secrets = _complete_secrets()
    secrets["ci360_connector_url"] = ""

    with pytest.raises(ValueError, match="ci360_connector_url"):
        validate_secrets(secrets)


def test_validate_secrets_reports_every_missing_key():
    with pytest.raises(ValueError) as excinfo:
        validate_secrets({})

    for key in REQUIRED_SECRET_KEYS:
        assert key in str(excinfo.value)
