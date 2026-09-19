# coding=utf-8
"""Shared fixtures for core/ tests."""

import pytest

from core.transform import OFFER_FIELD_GROUP_ID

# Values in field order expected by transform_json. Fields whose transform
# does `.split(".")[1]` are given "Enum.Value"-shaped strings; everything
# else is a plain value of the type transform_json expects back out.
OFFER_FIELD_VALUES = [
    "OfferStyle.Coupon",  # 0 style
    "OfferType.Percentage",  # 1 type
    "Fall Savings",  # 2 name
    "Save big this fall",  # 3 headline
    "Limited time only",  # 4 subHeadline
    "20% off your next purchase",  # 5 rebateDetails
    "20",  # 6 value
    "5",  # 7 priority
    True,  # 8 isActive
    "Visibility.Public",  # 9 visibility
    "See store for details",  # 10 disclaimerCopy
    "Show this offer at checkout",  # 11 instructionsCopy
    "Offer redeemed",  # 12 redeemedCopy
    "https://example.com/offer",  # 13 externalUrl
    "ChannelCode.Email",  # 14 redirectChannelCode
    "https://example.com/offer.png",  # 15 offerImage
    "https://example.com/offer-extra.png",  # 16 additionalOfferImage
    "https://example.com/offer-desktop.png",  # 17 desktopOfferImage
    "2026-01-01",  # 18 startDate
    "2026-01-31",  # 19 endDate
    False,  # 20 previewEnabled
    "2025-12-25",  # 21 previewDate
    "Valid through January",  # 22 validDateDescription
    "72",  # 23 redemptionPeriodHours
    "Thanks for redeeming",  # 24 receiptInstructions.headline
    "See you again soon",  # 25 receiptInstructions.subHeadline
    "ImageType.Standard",  # 26 receiptInstructions.imageType
    "RedempStyleType.Barcode",  # 27 redempStyleType
    "BarcodeSymbology.Code128",  # 28 barcodeSymbology
    "1234567890",  # 29 barcodeValue
    "AlgorithmName.None",  # 30 algorithmName
    "",  # 31 algorithmInputs
    "3",  # 32 maxRedemptions
    True,  # 33 perConsumerLimited
    "1",  # 34 primaryRedempLimit
    "RedempInterval.Day",  # 35 primaryRedempInterval
    "ChannelCode.App",  # 36 channelCode
    "Category.Grocery",  # 37 categories[0]
    "StoreGroup.All",  # 38 storeGroups[0]
]


def _offer_payload(group_id: str = OFFER_FIELD_GROUP_ID, extra_groups=()) -> dict:
    fields = [{"value": value} for value in OFFER_FIELD_VALUES]
    groups = list(extra_groups) + [{"groupId": group_id, "fields": fields}]
    return {"customAttributes": {"groups": groups}}


@pytest.fixture
def offer_payload_factory():
    return _offer_payload
