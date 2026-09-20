# coding=utf-8
"""
Offer CRUD operations shared by every cloud adapter.

Each function takes the secrets dict returned by a SecretProvider (see
secrets.py) plus whatever the operation needs, and returns a plain dict:
{"status": int, "data": str, "headers": dict}. Cloud adapters translate
that into their own platform's response object - nothing here imports a
cloud SDK.
"""

import logging
import time
from typing import Optional
from urllib.parse import urlsplit

import urllib3

from . import signing, transform
from .secrets import validate_secrets

logger = logging.getLogger(__name__)
_http = urllib3.PoolManager()


def _build_signed_url(secrets: dict, path: str) -> str:
    validate_secrets(secrets)
    epoch_time = int(time.time())
    base_url = "{0}v1/offers{1}?identifier={2}&timestamp={3}".format(
        secrets["partner_api_url"], path, secrets["partner_api_identifier"], epoch_time
    )
    signature = signing.make_digest(message_in=base_url, key_in=secrets["partner_api_secret"])
    return "{0}&authSignature={1}".format(base_url, signature)


def _call(method: str, signed_url: str, body: Optional[str] = None) -> dict:
    # signed_url's query string carries partner_api_identifier and the
    # request's own authSignature - log the path only, not the credential
    # or the valid-until-timestamp-mismatch signature that goes with it.
    logger.info("%s %s", method, urlsplit(signed_url).path)
    headers = {"Content-Type": "application/json"}
    if body is None:
        response = _http.request(method=method, url=signed_url, headers=headers)
    else:
        response = _http.request(method=method, url=signed_url, body=body, headers=headers)
    return {
        "status": response.status,
        "data": response.data.decode("utf-8", errors="replace"),
        "headers": dict(response.headers),
    }


def create_offer(secrets: dict, offer_payload: dict) -> dict:
    """POST a new offer, transforming it from CI360's connector format first."""
    signed_url = _build_signed_url(secrets, "")
    body = transform.transform_json(offer_payload)
    return _call("POST", signed_url, body=body)


def read_offers(secrets: dict) -> dict:
    """GET the full list of offers."""
    signed_url = _build_signed_url(secrets, "")
    return _call("GET", signed_url)


def read_offer_by_id(secrets: dict, offer_id: str) -> dict:
    """GET a single offer by id."""
    signed_url = _build_signed_url(secrets, "/{0}".format(offer_id))
    return _call("GET", signed_url)


def update_offer(secrets: dict, offer_id: str, offer_payload: dict) -> dict:
    """PUT an update to an existing offer, transforming it first."""
    signed_url = _build_signed_url(secrets, "/{0}".format(offer_id))
    body = transform.transform_json(offer_payload)
    return _call("PUT", signed_url, body=body)


def delete_offer(secrets: dict, offer_id: str) -> dict:
    """DELETE an existing offer."""
    signed_url = _build_signed_url(secrets, "/{0}".format(offer_id))
    return _call("DELETE", signed_url)
