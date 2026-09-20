# coding=utf-8
"""Tests for the 5 GCP Cloud Functions handlers in gcp/main.py. Same
wiring-only scope as the Azure and AWS adapter tests - core.offers is
covered separately. The by-id routes take the offer id as a query
parameter here, unlike Azure/AWS which use a path parameter.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

from _fakes import install_fake_module

GCP_DIR = Path(__file__).parents[1] / "gcp"

_functions_framework = install_fake_module("functions_framework")
if not hasattr(_functions_framework, "http"):
    _functions_framework.http = lambda fn: fn  # identity decorator, like the real one


class FakeFlaskResponse:
    def __init__(self, data, status=200, mimetype=None):
        self.data = data
        self.status = status
        self.mimetype = mimetype


_flask = install_fake_module("flask")
if not hasattr(_flask, "Response"):
    _flask.Response = FakeFlaskResponse
if not hasattr(_flask, "Request"):
    _flask.Request = MagicMock(name="Request")


class FakeGcpRequest:
    """Stand-in for flask.Request: only what each handler reads."""

    def __init__(self, json_body=None, args=None):
        self._json_body = json_body
        self.args = args or {}

    def get_json(self, silent=True):
        return self._json_body


def _load_module():
    fake_secrets_provider = install_fake_module("secrets_provider")
    fake_provider_cls = MagicMock(name="GCPSecretManagerSecretProvider")
    fake_secrets_provider.GCPSecretManagerSecretProvider = fake_provider_cls

    spec = importlib.util.spec_from_file_location(
        "_gcp_main_under_test", GCP_DIR / "main.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, fake_provider_cls


module, provider_cls = _load_module()


def _offers_result(status=200, data='{"ok": true}'):
    return {"status": status, "data": data}


def test_create_offer_parses_json_body_and_shapes_the_response():
    with patch("core.offers.create_offer", return_value=_offers_result(201)) as mock_create:
        response = module.create_offer(FakeGcpRequest(json_body={"name": "Fall Savings"}))

    provider_cls.return_value.fetch_secrets.assert_called()
    mock_create.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, {"name": "Fall Savings"}
    )
    assert response.status == 201
    assert response.data == '{"ok": true}'


def test_create_offer_defaults_to_an_empty_body():
    with patch("core.offers.create_offer", return_value=_offers_result(201)) as mock_create:
        module.create_offer(FakeGcpRequest(json_body=None))

    assert mock_create.call_args.args[1] == {}


def test_read_offers_lists():
    with patch("core.offers.read_offers", return_value=_offers_result(200)) as mock_read:
        response = module.read_offers(FakeGcpRequest())

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value)
    assert response.status == 200


def test_read_offer_by_id_uses_the_query_parameter():
    with patch("core.offers.read_offer_by_id", return_value=_offers_result(200)) as mock_read:
        response = module.read_offer_by_id(FakeGcpRequest(args={"id": "offer-42"}))

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-42")
    assert response.status == 200


def test_read_offer_by_id_missing_id_short_circuits():
    with patch("core.offers.read_offer_by_id") as mock_read:
        response = module.read_offer_by_id(FakeGcpRequest())

    mock_read.assert_not_called()
    assert response.status == 400


def test_update_offer_uses_query_parameter_and_body():
    with patch("core.offers.update_offer", return_value=_offers_result(200)) as mock_update:
        response = module.update_offer(FakeGcpRequest(json_body={"name": "New Name"}, args={"id": "offer-7"}))

    mock_update.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, "offer-7", {"name": "New Name"}
    )
    assert response.status == 200


def test_update_offer_missing_id_short_circuits():
    with patch("core.offers.update_offer") as mock_update:
        response = module.update_offer(FakeGcpRequest(json_body={}))

    mock_update.assert_not_called()
    assert response.status == 400


def test_delete_offer_uses_the_query_parameter():
    with patch("core.offers.delete_offer", return_value=_offers_result(204, data="")) as mock_delete:
        response = module.delete_offer(FakeGcpRequest(args={"id": "offer-7"}))

    mock_delete.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-7")
    assert response.status == 204


def test_delete_offer_missing_id_short_circuits():
    with patch("core.offers.delete_offer") as mock_delete:
        response = module.delete_offer(FakeGcpRequest())

    mock_delete.assert_not_called()
    assert response.status == 400
