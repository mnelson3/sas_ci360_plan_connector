# coding=utf-8
"""Tests for core.offers, mocking the outbound HTTP call and the clock."""

import json
from unittest.mock import MagicMock, patch

import pytest

from core import offers

SECRETS = {
    "ci360_connector_url": "https://ci360.example.com/",
    "ci360_connector_api_tenant_id": "tenant-123",
    "ci360_connector_api_secret": "connector-secret",
    "partner_api_identifier": "partner-id",
    "partner_api_secret": "partner-secret",
    "partner_api_url": "https://partner.example.com/",
}

INCOMPLETE_SECRETS = {"partner_api_url": "https://partner.example.com/"}


def _mock_response(status=200, data=b'{"ok": true}'):
    response = MagicMock()
    response.status = status
    response.data = data
    response.headers = {"Content-Type": "application/json"}
    return response


@patch("core.offers.time.time", return_value=1700000000)
def test_build_signed_url_includes_identifier_timestamp_and_signature(_mock_time):
    signed_url = offers._build_signed_url(SECRETS, "/offer-1")

    assert signed_url.startswith("https://partner.example.com/v1/offers/offer-1?")
    assert "identifier=partner-id" in signed_url
    assert "timestamp=1700000000" in signed_url
    assert "authSignature=" in signed_url


def test_build_signed_url_rejects_incomplete_secrets():
    with pytest.raises(ValueError, match="Missing required secret"):
        offers._build_signed_url(INCOMPLETE_SECRETS, "")


@patch("core.offers._http")
def test_read_offers_issues_a_get_and_passes_through_the_response(mock_http):
    mock_http.request.return_value = _mock_response(status=200, data=b'{"offers": []}')

    result = offers.read_offers(SECRETS)

    assert result == {"status": 200, "data": '{"offers": []}', "headers": {"Content-Type": "application/json"}}
    called_kwargs = mock_http.request.call_args.kwargs
    assert called_kwargs["method"] == "GET"


@patch("core.offers._http")
def test_read_offer_by_id_signs_a_path_with_the_id(mock_http):
    mock_http.request.return_value = _mock_response()

    offers.read_offer_by_id(SECRETS, "offer-42")

    signed_url = mock_http.request.call_args.kwargs["url"]
    assert "/v1/offers/offer-42" in signed_url


@patch("core.offers._http")
def test_create_offer_transforms_the_payload_before_posting(mock_http, offer_payload_factory):
    mock_http.request.return_value = _mock_response(status=201)

    result = offers.create_offer(SECRETS, offer_payload_factory())

    assert result["status"] == 201
    sent_body = json.loads(mock_http.request.call_args.kwargs["body"])
    assert sent_body["style"] == "Coupon"
    assert mock_http.request.call_args.kwargs["method"] == "POST"


@patch("core.offers._http")
def test_delete_offer_issues_a_delete_with_no_body(mock_http):
    mock_http.request.return_value = _mock_response(status=204, data=b"")

    result = offers.delete_offer(SECRETS, "offer-7")

    assert result["status"] == 204
    called_kwargs = mock_http.request.call_args.kwargs
    assert called_kwargs["method"] == "DELETE"
    assert "body" not in called_kwargs
