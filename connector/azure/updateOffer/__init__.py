# coding=utf-8
"""Azure Functions adapter: PUT /offers/{id} -> core.offers.update_offer"""

import logging

import azure.functions as func

from core import offers
from secrets_provider import AzureKeyVaultSecretProvider

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    offer_id = req.route_params.get("id") or req.params.get("id")
    if not offer_id:
        return func.HttpResponse("Missing offer id", status_code=400)

    logger.info("updateOffer: processing request for %s", offer_id)
    secrets = AzureKeyVaultSecretProvider().fetch_secrets()
    result = offers.update_offer(secrets, offer_id, req.get_json())
    return func.HttpResponse(result["data"], status_code=result["status"])
