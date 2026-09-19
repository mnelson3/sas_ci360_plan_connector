# coding=utf-8
"""Azure Functions adapter: GET /offers -> core.offers.read_offers"""

import logging

import azure.functions as func

from core import offers
from secrets_provider import AzureKeyVaultSecretProvider

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("readOffers: processing request")
    secrets = AzureKeyVaultSecretProvider().fetch_secrets()
    result = offers.read_offers(secrets)
    return func.HttpResponse(result["data"], status_code=result["status"])
