# coding=utf-8
"""
AWS Lambda adapter, targeting API Gateway HTTP API (payload format 2.0).

Each handler below is the Lambda entry point configured for one route in
template.yaml. All of them do the same three things: parse the API
Gateway event, call the matching function in core.offers, and shape the
result into an API Gateway HTTP API response.
"""

import json
import logging

from core import offers
from secrets_provider import AWSSecretsManagerSecretProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _response(result: dict) -> dict:
    return {
        "statusCode": result["status"],
        "headers": {"Content-Type": "application/json"},
        "body": result["data"],
    }


def _body(event: dict) -> dict:
    raw = event.get("body") or "{}"
    return json.loads(raw)


def create_offer(event, context):
    logger.info("create_offer: processing request")
    secrets = AWSSecretsManagerSecretProvider().fetch_secrets()
    result = offers.create_offer(secrets, _body(event))
    return _response(result)


def read_offers(event, context):
    logger.info("read_offers: processing request")
    secrets = AWSSecretsManagerSecretProvider().fetch_secrets()
    result = offers.read_offers(secrets)
    return _response(result)


def read_offer_by_id(event, context):
    offer_id = (event.get("pathParameters") or {}).get("id")
    if not offer_id:
        return {"statusCode": 400, "body": "Missing offer id"}

    logger.info("read_offer_by_id: processing request for %s", offer_id)
    secrets = AWSSecretsManagerSecretProvider().fetch_secrets()
    result = offers.read_offer_by_id(secrets, offer_id)
    return _response(result)


def update_offer(event, context):
    offer_id = (event.get("pathParameters") or {}).get("id")
    if not offer_id:
        return {"statusCode": 400, "body": "Missing offer id"}

    logger.info("update_offer: processing request for %s", offer_id)
    secrets = AWSSecretsManagerSecretProvider().fetch_secrets()
    result = offers.update_offer(secrets, offer_id, _body(event))
    return _response(result)


def delete_offer(event, context):
    offer_id = (event.get("pathParameters") or {}).get("id")
    if not offer_id:
        return {"statusCode": 400, "body": "Missing offer id"}

    logger.info("delete_offer: processing request for %s", offer_id)
    secrets = AWSSecretsManagerSecretProvider().fetch_secrets()
    result = offers.delete_offer(secrets, offer_id)
    return _response(result)
