# coding=utf-8
"""Request signing for the partner (offer/coupon platform) API."""

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def make_digest(message_in: str, key_in: str) -> str:
    """
    Create an HMAC-SHA1 signature for a partner API request.

    :param message_in: the exact URL (or message) being signed
    :param key_in: the partner API shared secret
    :return: hex-encoded signature
    """
    logger.debug("Signing message: %s", message_in)
    key = bytes(key_in, "UTF-8")
    message = bytes(message_in, "UTF-8")
    digester = hmac.new(key, message, hashlib.sha1)
    return digester.hexdigest()
