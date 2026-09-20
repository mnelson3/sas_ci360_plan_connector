# coding=utf-8
"""Tests for the 5 AWS Lambda handlers in aws/handlers.py (API Gateway
HTTP API payload format 2.0). Same wiring-only scope as the Azure and
GCP adapter tests - core.offers is covered separately.
"""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from _fakes import install_fake_module

AWS_DIR = Path(__file__).parents[1] / "aws"

install_fake_module("boto3")


def _load_handlers():
    fake_secrets_provider = install_fake_module("secrets_provider")
    fake_provider_cls = MagicMock(name="AWSSecretsManagerSecretProvider")
    fake_secrets_provider.AWSSecretsManagerSecretProvider = fake_provider_cls

    spec = importlib.util.spec_from_file_location(
        "_aws_handlers_under_test", AWS_DIR / "handlers.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, fake_provider_cls


def _offers_result(status=200, data='{"ok": true}'):
    return {"status": status, "data": data, "headers": {"Content-Type": "application/json"}}


def _event(body=None, path_id=None):
    event = {}
    if body is not None:
        event["body"] = json.dumps(body)
    if path_id is not None:
        event["pathParameters"] = {"id": path_id}
    return event


def test_create_offer_parses_the_body_and_shapes_the_response():
    module, provider_cls = _load_handlers()
    with patch("core.offers.create_offer", return_value=_offers_result(201)) as mock_create:
        response = module.create_offer(_event(body={"name": "Fall Savings"}), None)

    provider_cls.return_value.fetch_secrets.assert_called_once()
    mock_create.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, {"name": "Fall Savings"}
    )
    assert response == {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": '{"ok": true}',
    }


def test_create_offer_defaults_to_an_empty_body():
    module, _provider_cls = _load_handlers()
    with patch("core.offers.create_offer", return_value=_offers_result(201)) as mock_create:
        module.create_offer({}, None)

    assert mock_create.call_args.args[1] == {}


def test_read_offers_lists():
    module, provider_cls = _load_handlers()
    with patch("core.offers.read_offers", return_value=_offers_result(200)) as mock_read:
        response = module.read_offers({}, None)

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value)
    assert response["statusCode"] == 200


def test_read_offer_by_id_uses_the_path_parameter():
    module, provider_cls = _load_handlers()
    with patch("core.offers.read_offer_by_id", return_value=_offers_result(200)) as mock_read:
        response = module.read_offer_by_id(_event(path_id="offer-42"), None)

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-42")
    assert response["statusCode"] == 200


def test_read_offer_by_id_missing_id_short_circuits():
    module, _provider_cls = _load_handlers()
    with patch("core.offers.read_offer_by_id") as mock_read:
        response = module.read_offer_by_id({}, None)

    mock_read.assert_not_called()
    assert response["statusCode"] == 400


def test_update_offer_uses_path_parameter_and_body():
    module, provider_cls = _load_handlers()
    with patch("core.offers.update_offer", return_value=_offers_result(200)) as mock_update:
        response = module.update_offer(_event(body={"name": "New Name"}, path_id="offer-7"), None)

    mock_update.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, "offer-7", {"name": "New Name"}
    )
    assert response["statusCode"] == 200


def test_update_offer_missing_id_short_circuits():
    module, _provider_cls = _load_handlers()
    with patch("core.offers.update_offer") as mock_update:
        response = module.update_offer(_event(body={}), None)

    mock_update.assert_not_called()
    assert response["statusCode"] == 400


def test_delete_offer_uses_the_path_parameter():
    module, provider_cls = _load_handlers()
    with patch("core.offers.delete_offer", return_value=_offers_result(204, data="")) as mock_delete:
        response = module.delete_offer(_event(path_id="offer-7"), None)

    mock_delete.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-7")
    assert response["statusCode"] == 204


def test_delete_offer_missing_id_short_circuits():
    module, _provider_cls = _load_handlers()
    with patch("core.offers.delete_offer") as mock_delete:
        response = module.delete_offer({}, None)

    mock_delete.assert_not_called()
    assert response["statusCode"] == 400
