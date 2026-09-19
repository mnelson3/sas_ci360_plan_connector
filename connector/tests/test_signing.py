# coding=utf-8
"""Tests for core.signing.make_digest."""

import hashlib
import hmac

from core import signing


def test_make_digest_matches_reference_hmac_sha1():
    message = "https://partner.example.com/v1/offers?identifier=abc&timestamp=123"
    key = "shared-secret"

    expected = hmac.new(
        bytes(key, "UTF-8"), bytes(message, "UTF-8"), hashlib.sha1
    ).hexdigest()

    assert signing.make_digest(message_in=message, key_in=key) == expected


def test_make_digest_is_deterministic():
    digest_a = signing.make_digest(message_in="same-message", key_in="same-key")
    digest_b = signing.make_digest(message_in="same-message", key_in="same-key")

    assert digest_a == digest_b


def test_make_digest_changes_with_key():
    message = "same-message"

    digest_a = signing.make_digest(message_in=message, key_in="key-one")
    digest_b = signing.make_digest(message_in=message, key_in="key-two")

    assert digest_a != digest_b
