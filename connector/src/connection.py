# coding=utf-8

import logging
import os
import json
import time
import urllib3
import hashlib
import hmac
import base64

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError


def fetch_secret():
	result = {}
	keyVaultName = "sas-qtkm-kv-sandbox"
	keyVaultUri = ("https://{0}.vault.azure.net/").format(keyVaultName)
	credential = DefaultAzureCredential()
	secret_client = SecretClient(vault_url=keyVaultUri, credential=credential)

	secret_names = {
		"ci360_connector_url": "ci360-connector-url-sandbox",
		"ci360_connector_api_tenant_id_sandbox": "ci360-connector-api-tenant-id-sandbox",
		"ci360_connector_api_secret_sandbox": "ci360-connector-api-secret-sandbox",
		"km_api_identifier_sandbox": "km-api-identifier-sandbox",
		"km_api_secret_sandbox": "km-api-secret-sandbox",
		"km_api_url_sandbox": "km-api-url-sandbox",
	}

	try:
		for key, secret_name in secret_names.items():
			result[key] = secret_client.get_secret(secret_name)
			logging.info("Fetched secret: %s", secret_name)
	except ResourceNotFoundError as e:
		logging.info(e.message)
	return result


"""
Create authorized signature
"""
def make_digest(message_in, key_in):
	logging.info("message: %s", message_in)
	key = bytes(key_in, "UTF-8")
	message = bytes(message_in, "UTF-8")
	digester = hmac.new(key, message, hashlib.sha1)
	result = digester.hexdigest()
	return result


"""
[CLIENT] API call
"""
def call_km_api(method_in, signed_url_in, body_in=None):
	logging.info("method: %s", method_in)
	logging.info("signed_url: %s", signed_url_in)
	logging.info("body: %s", body_in)

	http = urllib3.PoolManager()

	req_headers = {"Content-Type": "application/json"}

	if (method_in == "GET") or (method_in == "DELETE"):
		result = http.request(method=method_in, url=signed_url_in, headers=req_headers)
	else:
		data = transform_json(body_in)
		result = http.request(method=method_in, url=signed_url_in, body=data, headers=req_headers)

	return result


"""
Transform JSON data from SAS360 to JSON format required by [CLIENT] API call
"""
def transform_json(json_in):
	# logging.info("json_in: %s", json_in)
	json_custom_attributes = json_in['customAttributes']
	# logging.info("json_custom_attributes: %s", json_custom_attributes)
	json_groups = json_custom_attributes['groups']
	# logging.info("json_groups: %s", json_groups)
	for item in json_groups:
		if item['groupId'] == '43ba554d-97a7-4b5e-b7ce-f2a53747cf20':
			json_group = item
	# logging.info("json_group: %s", json_group)

	json_data = {
		"style": "{0}".format(str(json_group['fields'][0]['value']).split(".")[1]),
		"type": "{0}".format(str(json_group['fields'][1]['value']).split(".")[1]),
		"name": "{0}".format(json_group['fields'][2]['value']),
		"headline": "{0}".format(json_group['fields'][3]['value']),
		"subHeadline": "{0}".format(json_group['fields'][4]['value']),
		"rebateDetails": "{0}".format(json_group['fields'][5]['value']),
		"value": "{0}".format(json_group['fields'][6]['value']),
		"priority": int(json_group['fields'][7]['value']),
		"isActive": json_group['fields'][8]['value'],
		"isArchived": False,
		"isExhausted": False,
		"visibility": "{0}".format(str(json_group['fields'][9]['value']).split(".")[1]),
		"disclaimerCopy": "{0}".format(json_group['fields'][10]['value']),
		"instructionsCopy": "{0}".format(json_group['fields'][11]['value']),
		"redeemedCopy": "{0}".format(json_group['fields'][12]['value']),
		"hideViewMoreButton": True,
		"externalUrl": "{0}".format(json_group['fields'][13]['value']),
		"redirectChannelCode": "{0}".format(str(json_group['fields'][14]['value']).split(".")[1]),
		"activationActionText": "{0}".format(""),
		"activationActionAfterOfferAddedText": "{0}".format(""),
		"printTemplate": "{0}".format(""),
		"refOfferId": "{0}".format(""),
		"imageConfig": {
			"offerImage": "{0}".format(json_group['fields'][15]['value']),
			"additionalOfferImage": "{0}".format(json_group['fields'][16]['value']),
			"desktopOfferImage": "{0}".format(json_group['fields'][17]['value']),
			"size": "{0}".format(""),
			"hideText": False
		},
		"schedulingConfig": {
			"startDate": "{0}".format(json_group['fields'][18]['value']),
			"endDate": "{0}".format(json_group['fields'][19]['value']),
			"previewEnabled": json_group['fields'][20]['value'],
			"previewDate": "{0}".format(json_group['fields'][21]['value']),
			"validDateDescription": "{0}".format(json_group['fields'][22]['value']),
			"redemptionPeriodHours": json_group['fields'][23]['value']
		},
		"receiptInstructions": {
			"headline": "{0}".format(json_group['fields'][24]['value']),
			"subHeadline": "{0}".format(json_group['fields'][25]['value']),
			"imageType": "{0}".format(str(json_group['fields'][26]['value']).split(".")[1])
		},
 		"redempAssets":	[{
			"redempStyleType": "{0}".format(str(json_group['fields'][27]['value']).split(".")[1]),
			"barcodeSymbology": "{0}".format(str(json_group['fields'][28]['value']).split(".")[1]),
			"barcodeValue": "{0}".format(json_group['fields'][29]['value']),
			"algorithmName": "{0}".format(str(json_group['fields'][30]['value']).split(".")[1]),
			"algorithmInputs": "{0}".format(json_group['fields'][31]['value'])
		}],
		"redempConfig": {
			"redempTimerMins": int(0),
			"maxRedemptions": int(json_group['fields'][32]['value']),
			"applyCapOnActivation": False,
			"perConsumerLimited": json_group['fields'][33]['value'],
			"redempLimitPolicy": {
				"primaryRedempLimit": int(json_group['fields'][34]['value']),
				"primaryRedempInterval": "{0}".format(str(json_group['fields'][35]['value']).split(".")[1]),
				"secondaryRedempLimitEnabled": False,
				"secondaryRedempLimit": int(0),
				"secondaryRedempInterval": "{0}".format("")
			},
			"screenshotProtectionEnabled": False,
			"returnCodeType": "{0}".format(""),
			"returnCodeString": "{0}".format("")
		},
		"channels": [{
			"channelCode": "{0}".format(str(json_group['fields'][36]['value']).split(".")[1]),
			"headline": "{0}".format(""),
			"subHeadline": "{0}".format(""),
			"startDate": "{0}".format(""),
			"endDate": "{0}".format(""),
			"previewDate": "{0}".format(""),
			"validDateDescription": "{0}".format(""),
			"priority": "{0}".format(""),
			"actionText": "{0}".format(""),
			"staticRedempAsset0": "{0}".format(""),
			"staticRedempAsset1": "{0}".format(""),
			"hideRedempAsset0": False,
			"hideRedempAsset1": False
		}],
		"categories": ["{0}".format(str(json_group['fields'][37]['value']).split(".")[1])],
		"productCategories": [{
			"categoryName": "{0}".format(""),
			"subcategoryName": "{0}".format("")
		}],
		"segments": ["{0}".format("")],
		"storeGroups": ["{0}".format(str(json_group['fields'][38]['value']).split(".")[1])]
	}
	json_data_in = json.dumps(json_data)
	logging.info("json_data_in: %s", json_data_in)
	result = json_data_in
