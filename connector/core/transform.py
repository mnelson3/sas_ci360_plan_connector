# coding=utf-8
"""
Transform an offer payload from SAS CI360's Plan connector format into the
partner (offer/coupon platform) API's request format.
"""

import json
import logging

# CI360 custom-attribute group id that carries the offer fields this
# connector maps. Set to match your own Plan connector's field group.
OFFER_FIELD_GROUP_ID = "43ba554d-97a7-4b5e-b7ce-f2a53747cf20"

logger = logging.getLogger(__name__)


def transform_json(json_in: dict) -> str:
    """
    Map a CI360 Plan connector offer payload to the partner API's schema.

    :param json_in: the offer payload as sent by CI360's connector framework
    :return: JSON string ready to send to the partner API
    """
    json_custom_attributes = json_in["customAttributes"]
    json_groups = json_custom_attributes["groups"]
    json_group = None
    for item in json_groups:
        if item["groupId"] == OFFER_FIELD_GROUP_ID:
            json_group = item
    if json_group is None:
        raise ValueError(
            "No custom-attribute group matching OFFER_FIELD_GROUP_ID found on this offer"
        )

    json_data = {
        "style": "{0}".format(str(json_group["fields"][0]["value"]).split(".")[1]),
        "type": "{0}".format(str(json_group["fields"][1]["value"]).split(".")[1]),
        "name": "{0}".format(json_group["fields"][2]["value"]),
        "headline": "{0}".format(json_group["fields"][3]["value"]),
        "subHeadline": "{0}".format(json_group["fields"][4]["value"]),
        "rebateDetails": "{0}".format(json_group["fields"][5]["value"]),
        "value": "{0}".format(json_group["fields"][6]["value"]),
        "priority": int(json_group["fields"][7]["value"]),
        "isActive": json_group["fields"][8]["value"],
        "isArchived": False,
        "isExhausted": False,
        "visibility": "{0}".format(str(json_group["fields"][9]["value"]).split(".")[1]),
        "disclaimerCopy": "{0}".format(json_group["fields"][10]["value"]),
        "instructionsCopy": "{0}".format(json_group["fields"][11]["value"]),
        "redeemedCopy": "{0}".format(json_group["fields"][12]["value"]),
        "hideViewMoreButton": True,
        "externalUrl": "{0}".format(json_group["fields"][13]["value"]),
        "redirectChannelCode": "{0}".format(
            str(json_group["fields"][14]["value"]).split(".")[1]
        ),
        "activationActionText": "",
        "activationActionAfterOfferAddedText": "",
        "printTemplate": "",
        "refOfferId": "",
        "imageConfig": {
            "offerImage": "{0}".format(json_group["fields"][15]["value"]),
            "additionalOfferImage": "{0}".format(json_group["fields"][16]["value"]),
            "desktopOfferImage": "{0}".format(json_group["fields"][17]["value"]),
            "size": "",
            "hideText": False,
        },
        "schedulingConfig": {
            "startDate": "{0}".format(json_group["fields"][18]["value"]),
            "endDate": "{0}".format(json_group["fields"][19]["value"]),
            "previewEnabled": json_group["fields"][20]["value"],
            "previewDate": "{0}".format(json_group["fields"][21]["value"]),
            "validDateDescription": "{0}".format(json_group["fields"][22]["value"]),
            "redemptionPeriodHours": json_group["fields"][23]["value"],
        },
        "receiptInstructions": {
            "headline": "{0}".format(json_group["fields"][24]["value"]),
            "subHeadline": "{0}".format(json_group["fields"][25]["value"]),
            "imageType": "{0}".format(str(json_group["fields"][26]["value"]).split(".")[1]),
        },
        "redempAssets": [
            {
                "redempStyleType": "{0}".format(
                    str(json_group["fields"][27]["value"]).split(".")[1]
                ),
                "barcodeSymbology": "{0}".format(
                    str(json_group["fields"][28]["value"]).split(".")[1]
                ),
                "barcodeValue": "{0}".format(json_group["fields"][29]["value"]),
                "algorithmName": "{0}".format(
                    str(json_group["fields"][30]["value"]).split(".")[1]
                ),
                "algorithmInputs": "{0}".format(json_group["fields"][31]["value"]),
            }
        ],
        "redempConfig": {
            "redempTimerMins": 0,
            "maxRedemptions": int(json_group["fields"][32]["value"]),
            "applyCapOnActivation": False,
            "perConsumerLimited": json_group["fields"][33]["value"],
            "redempLimitPolicy": {
                "primaryRedempLimit": int(json_group["fields"][34]["value"]),
                "primaryRedempInterval": "{0}".format(
                    str(json_group["fields"][35]["value"]).split(".")[1]
                ),
                "secondaryRedempLimitEnabled": False,
                "secondaryRedempLimit": 0,
                "secondaryRedempInterval": "",
            },
            "screenshotProtectionEnabled": False,
            "returnCodeType": "",
            "returnCodeString": "",
        },
        "channels": [
            {
                "channelCode": "{0}".format(
                    str(json_group["fields"][36]["value"]).split(".")[1]
                ),
                "headline": "",
                "subHeadline": "",
                "startDate": "",
                "endDate": "",
                "previewDate": "",
                "validDateDescription": "",
                "priority": "",
                "actionText": "",
                "staticRedempAsset0": "",
                "staticRedempAsset1": "",
                "hideRedempAsset0": False,
                "hideRedempAsset1": False,
            }
        ],
        "categories": ["{0}".format(str(json_group["fields"][37]["value"]).split(".")[1])],
        "productCategories": [{"categoryName": "", "subcategoryName": ""}],
        "segments": [""],
        "storeGroups": ["{0}".format(str(json_group["fields"][38]["value"]).split(".")[1])],
    }
    json_data_out = json.dumps(json_data)
    logger.debug("Transformed payload: %s", json_data_out)
    return json_data_out
