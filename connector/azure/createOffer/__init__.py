# coding=utf-8
"""Azure Functions adapter: POST /offers -> core.offers.create_offer"""

import logging

import azure.functions as func

from core import offers
from secrets_provider import AzureKeyVaultSecretProvider

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("createOffer: processing request")
    secrets = AzureKeyVaultSecretProvider().fetch_secrets()
    result = offers.create_offer(secrets, req.get_json())
    return func.HttpResponse(result["data"], status_code=result["status"])
