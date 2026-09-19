# coding=utf-8
"""Tests for core.transform.transform_json."""

import json

import pytest

from core.transform import transform_json


def test_transform_json_maps_the_matching_group(offer_payload_factory):
    result = json.loads(transform_json(offer_payload_factory()))

    assert result["style"] == "Coupon"
    assert result["type"] == "Percentage"
    assert result["name"] == "Fall Savings"
    assert result["priority"] == 5
    assert result["isActive"] is True
    assert result["visibility"] == "Public"
    assert result["imageConfig"]["offerImage"] == "https://example.com/offer.png"
    assert result["schedulingConfig"]["startDate"] == "2026-01-01"
    assert result["receiptInstructions"]["imageType"] == "Standard"
    assert result["redempAssets"][0]["barcodeValue"] == "1234567890"
    assert result["redempConfig"]["maxRedemptions"] == 3
    assert result["channels"][0]["channelCode"] == "App"
    assert result["categories"] == ["Grocery"]
    assert result["storeGroups"] == ["All"]
    # Fields the connector doesn't source from CI360 are always sent as fixed defaults.
    assert result["isArchived"] is False
    assert result["isExhausted"] is False


def test_transform_json_picks_the_group_matching_offer_field_group_id(offer_payload_factory):
    payload = offer_payload_factory(extra_groups=[{"groupId": "some-other-group", "fields": []}])

    result = json.loads(transform_json(payload))

    assert result["name"] == "Fall Savings"


def test_transform_json_raises_when_no_group_matches(offer_payload_factory):
    payload = offer_payload_factory(group_id="a-group-id-that-does-not-match")

    with pytest.raises(ValueError, match="OFFER_FIELD_GROUP_ID"):
        transform_json(payload)
