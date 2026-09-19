# coding=utf-8
"""
GCP Cloud Functions adapter (2nd gen, functions-framework).

Deployed as five separate HTTP functions, one entry point each, mirroring
the Azure and AWS adapters. The by-id operations take the offer id as a
query parameter (?id=...) so all three cloud adapters can be driven the
same way regardless of each platform's own path-routing conventions.

Deploy, e.g.:
  gcloud functions deploy create-offer --gen2 --runtime=python311 \\
    --entry-point=create_offer --trigger-http --env-vars-file=.env.yaml
"""

import logging

import functions_framework
from flask import Request, Response

from core import offers
from secrets_provider import GCPSecretManagerSecretProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _response(result: dict) -> Response:
    return Response(result["data"], status=result["status"], mimetype="application/json")


@functions_framework.http
def create_offer(request: Request):
    logger.info("create_offer: processing request")
    secrets = GCPSecretManagerSecretProvider().fetch_secrets()
    result = offers.create_offer(secrets, request.get_json(silent=True) or {})
    return _response(result)


@functions_framework.http
def read_offers(request: Request):
    logger.info("read_offers: processing request")
    secrets = GCPSecretManagerSecretProvider().fetch_secrets()
    result = offers.read_offers(secrets)
    return _response(result)


@functions_framework.http
def read_offer_by_id(request: Request):
    offer_id = request.args.get("id")
    if not offer_id:
        return Response("Missing offer id", status=400)

    logger.info("read_offer_by_id: processing request for %s", offer_id)
    secrets = GCPSecretManagerSecretProvider().fetch_secrets()
    result = offers.read_offer_by_id(secrets, offer_id)
    return _response(result)


@functions_framework.http
def update_offer(request: Request):
    offer_id = request.args.get("id")
    if not offer_id:
        return Response("Missing offer id", status=400)

    logger.info("update_offer: processing request for %s", offer_id)
    secrets = GCPSecretManagerSecretProvider().fetch_secrets()
    result = offers.update_offer(secrets, offer_id, request.get_json(silent=True) or {})
    return _response(result)


@functions_framework.http
def delete_offer(request: Request):
    offer_id = request.args.get("id")
    if not offer_id:
        return Response("Missing offer id", status=400)

    logger.info("delete_offer: processing request for %s", offer_id)
    secrets = GCPSecretManagerSecretProvider().fetch_secrets()
    result = offers.delete_offer(secrets, offer_id)
    return _response(result)
