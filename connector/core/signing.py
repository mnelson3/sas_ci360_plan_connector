# coding=utf-8
"""Request signing for the partner (offer/coupon platform) API."""

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def make_digest(message_in: str, key_in: str) -> str:
    """
    Create an HMAC-SHA256 signature for a partner API request.

    :param message_in: the exact URL (or message) being signed
    :param key_in: the partner API shared secret
    :return: hex-encoded signature
    """
    # message_in carries the partner_api_identifier in its query string, and
    # key_in is the signing secret itself - neither belongs in a log line.
    logger.debug("Signing request (%d byte message)", len(message_in))
    key = bytes(key_in, "UTF-8")
    message = bytes(message_in, "UTF-8")
    digester = hmac.new(key, message, hashlib.sha256)
    return digester.hexdigest()
