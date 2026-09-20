# coding=utf-8
"""Tests for the 5 Azure Functions handlers (azure/<name>/__init__.py).

Each handler does three things: pull the offer id out of the request (for
the by-id routes), fetch secrets, and call the matching core.offers
function - then shape the result into an azure.functions.HttpResponse.
core.offers itself is covered by test_offers.py; these tests only check
the wiring.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

from _fakes import install_fake_module

AZURE_DIR = Path(__file__).parents[1] / "azure"

_functions_mod = install_fake_module("azure.functions")


class FakeHttpResponse:
    def __init__(self, body, status_code=200):
        self.body = body
        self.status_code = status_code


if not hasattr(_functions_mod, "HttpResponse"):
    _functions_mod.HttpResponse = FakeHttpResponse
if not hasattr(_functions_mod, "HttpRequest"):
    _functions_mod.HttpRequest = MagicMock(name="HttpRequest")


class FakeRequest:
    """Stand-in for func.HttpRequest: only the attributes each handler reads."""

    def __init__(self, json_body=None, route_params=None, params=None):
        self._json_body = json_body if json_body is not None else {}
        self.route_params = route_params or {}
        self.params = params or {}

    def get_json(self):
        return self._json_body


def _load_handler(function_dir):
    fake_secrets_provider = install_fake_module("secrets_provider")
    fake_provider_cls = MagicMock(name="AzureKeyVaultSecretProvider")
    fake_secrets_provider.AzureKeyVaultSecretProvider = fake_provider_cls

    spec = importlib.util.spec_from_file_location(
        "_azure_{0}_under_test".format(function_dir),
        AZURE_DIR / function_dir / "__init__.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, fake_provider_cls


def _offers_result(status=200, data='{"ok": true}'):
    return {"status": status, "data": data}


def test_create_offer_fetches_secrets_and_posts_the_body():
    module, provider_cls = _load_handler("createOffer")
    with patch("core.offers.create_offer", return_value=_offers_result(201)) as mock_create:
        response = module.main(FakeRequest(json_body={"name": "Fall Savings"}))

    provider_cls.return_value.fetch_secrets.assert_called_once()
    mock_create.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, {"name": "Fall Savings"}
    )
    assert response.status_code == 201
    assert response.body == '{"ok": true}'


def test_read_offers_fetches_secrets_and_lists():
    module, provider_cls = _load_handler("readOffers")
    with patch("core.offers.read_offers", return_value=_offers_result(200)) as mock_read:
        response = module.main(FakeRequest())

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value)
    assert response.status_code == 200


def test_read_offer_by_id_uses_the_route_param():
    module, provider_cls = _load_handler("readOfferById")
    with patch("core.offers.read_offer_by_id", return_value=_offers_result(200)) as mock_read:
        response = module.main(FakeRequest(route_params={"id": "offer-42"}))

    mock_read.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-42")
    assert response.status_code == 200


def test_read_offer_by_id_falls_back_to_query_param():
    module, _provider_cls = _load_handler("readOfferById")
    with patch("core.offers.read_offer_by_id", return_value=_offers_result(200)) as mock_read:
        module.main(FakeRequest(params={"id": "offer-99"}))

    assert mock_read.call_args.args[1] == "offer-99"


def test_read_offer_by_id_missing_id_short_circuits_without_calling_core():
    module, _provider_cls = _load_handler("readOfferById")
    with patch("core.offers.read_offer_by_id") as mock_read:
        response = module.main(FakeRequest())

    mock_read.assert_not_called()
    assert response.status_code == 400


def test_update_offer_uses_the_route_param_and_body():
    module, provider_cls = _load_handler("updateOffer")
    with patch("core.offers.update_offer", return_value=_offers_result(200)) as mock_update:
        response = module.main(FakeRequest(json_body={"name": "New Name"}, route_params={"id": "offer-7"}))

    mock_update.assert_called_once_with(
        provider_cls.return_value.fetch_secrets.return_value, "offer-7", {"name": "New Name"}
    )
    assert response.status_code == 200


def test_update_offer_missing_id_short_circuits():
    module, _provider_cls = _load_handler("updateOffer")
    with patch("core.offers.update_offer") as mock_update:
        response = module.main(FakeRequest(json_body={}))

    mock_update.assert_not_called()
    assert response.status_code == 400


def test_delete_offer_uses_the_route_param():
    module, provider_cls = _load_handler("deleteOffer")
    with patch("core.offers.delete_offer", return_value=_offers_result(204, data="")) as mock_delete:
        response = module.main(FakeRequest(route_params={"id": "offer-7"}))

    mock_delete.assert_called_once_with(provider_cls.return_value.fetch_secrets.return_value, "offer-7")
    assert response.status_code == 204


def test_delete_offer_missing_id_short_circuits():
    module, _provider_cls = _load_handler("deleteOffer")
    with patch("core.offers.delete_offer") as mock_delete:
        response = module.main(FakeRequest())

    mock_delete.assert_not_called()
    assert response.status_code == 400
