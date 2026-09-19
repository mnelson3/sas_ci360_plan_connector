# coding=utf-8
"""
Cloud-agnostic core for the SAS CI360 Plan connector.

Everything in this package is pure Python with no cloud SDK dependency.
Each cloud adapter (connector/azure, connector/aws, connector/gcp) supplies
a SecretProvider for that platform's secret store and a thin handler that
translates its platform's request/response shape to and from the plain
functions in offers.py. The offer-transformation and request-signing logic
lives here exactly once.
"""
