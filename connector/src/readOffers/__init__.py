# coding=utf-8

import logging
import os
import json
import time
import urllib3
import hashlib
import hmac
import base64

import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError

import connection

logging.info("Initializing function")
http = urllib3.PoolManager()
epochtime = int(time.time())
logging.info("Epochtime: %s", epochtime)


"""
main:
Main event handler entry point for function request
def main(req: func.HttpRequest, msg: func.Out[func.QueueMessage]) -> str:	# Bojan
"""
def main(req: func.HttpRequest) -> func.HttpResponse:
	logging.info("Python HTTP trigger function processed a request.")

	resultDict = connection.fetch_secret()

	# Read Offers
	method = "GET"
	logging.info("method: %s", method)
	try:
		base_url = ("{0}v1/offers?identifier={1}&timestamp={2}").format(resultDict["km_api_url_sandbox"].value, resultDict["km_api_identifier_sandbox"].value, epochtime)
		print(base_url)
		key = resultDict["km_api_secret_sandbox"].value
		signature = connection.make_digest(message_in=base_url, key_in=key)
		print(signature)
		signed_url = ("{0}&authSignature={1}").format(base_url, signature)
		print(signed_url)
	except ValueError as e:
		logging.info(e.message)
	finally:
		result = connection.call_km_api(method_in=method, signed_url_in=signed_url)

	if method:
		logging.info("result.status: %s", result.status)
		logging.info("result.data: %s", result.data)
		logging.info("result.headers: %s", result.headers)
		return func.HttpResponse(("Method: {0}\nStatus: {1}\nData: {2}\nHeaders: {3}").format(method, result.status, result.data, result.headers))
	else:
		logging.info("result.status: %s", result.status)
		return func.HttpResponse("Please pass a method on the query string or in the request body", status_code=400)

