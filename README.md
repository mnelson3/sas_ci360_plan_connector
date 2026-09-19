# SAS CI360 Plan Connector

> **Status: canonical.** The reference connector pattern for CI360's Plan connector framework — no duplicate implementation exists.

An Azure Functions connector that lets [SAS Customer Intelligence 360](https://www.sas.com/en_us/software/customer-intelligence-360.html) (CI360) manage offers in a third-party offer/coupon platform through CI360's connector framework.

<br>

### Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Endpoints](#endpoints)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Registering the Connector in CI360](#registering-the-connector-in-ci360)
- [Branching Model](#branching-model)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Additional Resources](#additional-resources)

<br>

### Overview

CI360's connector framework lets a tenant call out to a third-party REST API directly, or through a small piece of custom integration code when the third-party API doesn't match what CI360 expects. This project is that custom integration layer: a set of [Azure Functions](https://learn.microsoft.com/azure/azure-functions/) written in Python that translate CI360 "Offer" attribute payloads into the request/response shape required by a third-party offer-management API, sign each request with an HMAC signature, and forward it on.

Each Azure Function corresponds to one CRUD operation on an offer: create, read (single or list), update, and delete.

<br>

### Prerequisites

- A CI360 tenant with administrative rights
- A Microsoft Azure subscription with access to Functions, API Management, Storage Accounts, and Key Vault
- Python 3.8+
- The [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) for local development

<br>

### Project Structure

```
connector/
├── host.json                        # Azure Functions host configuration
├── requirements.txt                 # Python dependencies
├── local.settings.json.example      # Template for local dev settings (copy to local.settings.json)
└── src/
    ├── connection.py                # Shared helpers: Key Vault secret retrieval, HMAC signing, HTTP calls
    ├── createOffer/                 # POST   /api/offers
    ├── readOffers/                  # GET    /api/offers
    ├── readOfferById/               # GET    /api/offers/{id}
    ├── updateOffer/                 # PUT    /api/offers
    └── deleteOffer/                 # DELETE /api/offers/{id}
```

Each function folder contains an `__init__.py` (the function entry point) and a `function.json` (its HTTP trigger binding).

<br>

### Endpoints

| Function | Method | Route | Description |
|---|---|---|---|
| `createOffer` | POST | `/api/offers` | Creates a new offer from the CI360 request body |
| `readOffers` | GET | `/api/offers` | Lists offers |
| `readOfferById` | GET | `/api/offers/{id}` | Fetches a single offer by ID |
| `updateOffer` | PUT | `/api/offers` | Updates an offer (ID passed as an `id` query parameter) |
| `deleteOffer` | DELETE | `/api/offers/{id}` | Deletes an offer by ID |

Every request is signed before it's sent to the downstream API: `connection.make_digest` builds an HMAC-SHA1 signature over the request URL using a secret key pulled from Azure Key Vault, and appends it as an `authSignature` query parameter.

<br>

### Getting Started

1. Clone this repository.
2. Install dependencies:
   ```
   cd connector
   pip install -r requirements.txt
   ```
3. Copy the local settings template and fill in values for your environment:
   ```
   cp local.settings.json.example local.settings.json
   ```
4. Run the function app locally:
   ```
   func start
   ```
5. Deploy to an Azure Function App (via the Azure CLI, VS Code Azure Functions extension, or your CI/CD pipeline of choice).

<br>

### Configuration

This connector does not store any third-party API credentials in source control. At runtime, `connection.fetch_secret()` retrieves the following secrets from an Azure Key Vault instance (see `keyVaultName` in `connector/src/connection.py`):

| Secret name | Purpose |
|---|---|
| `ci360-connector-url-sandbox` | Base URL CI360 uses to reach this connector |
| `ci360-connector-api-tenant-id-sandbox` | CI360 tenant ID |
| `ci360-connector-api-secret-sandbox` | Shared secret for the CI360-to-connector call |
| `km-api-identifier-sandbox` | Third-party API client identifier |
| `km-api-secret-sandbox` | Third-party API signing secret |
| `km-api-url-sandbox` | Base URL of the third-party offer API |

Provision equivalent `*-production` secrets in Key Vault before promoting to a production environment. `local.settings.json` is git-ignored — never commit real secret values to it; use `local.settings.json.example` as the template.

<br>

### Registering the Connector in CI360

After deploying the Function App and exposing it behind Azure API Management (or another gateway), register the resulting REST API as a connector endpoint in CI360:

- [Add and Register a Connector](http://documentation.sas.com/?cdcId=cintcdc&cdcVersion=production.a&docsetId=cintag&docsetTarget=p18n16127tbhtsn18jxoz5u1jkvl.htm&locale=en) — SAS CI360 admin guide
- [Add an Endpoint](http://documentation.sas.com/?cdcId=cintcdc&cdcVersion=production.a&docsetId=cintag&docsetTarget=p18n16127tbhtsn18jxoz5u1jkvl.htm&locale=en) — SAS CI360 admin guide
- [Write a Custom Connector](http://documentation.sas.com/?cdcId=cintcdc&cdcVersion=production.a&docsetId=cintag&docsetTarget=p1jq0pbjhm7x1in18jqg7dfdmk0v.htm&locale=en) — SAS CI360 admin guide

<br>

### Branching Model

| Branch | Environment |
|---|---|
| `main` | Production |
| `staging` | Pre-production validation |
| `develop` | Active development |

Work lands in `develop`, is promoted to `staging` for validation, and is promoted to `main` to ship.

<br>

### Troubleshooting

- **`ResourceNotFoundError` when fetching secrets** — confirm the Function App's managed identity has `get`/`list` access to the Key Vault, and that the secret names match the table above.
- **`401`/signature mismatch from the downstream API** — the HMAC signature is computed over the exact request URL sent to the third-party API; confirm the base URL and timestamp aren't being altered after signing.

<br>

### Contributing

We welcome your contributions! Please read [CONTRIBUTING](CONTRIBUTING.md) for details on how to submit contributions to this project.

<br>

### License

This project is licensed under the [Nelson Grey LLC Community License 1.0](LICENSE).

- **Free for individuals, education, and research**: use, modify, and distribute this software for non-commercial purposes
- **Commercial evaluation**: evaluate the software for a possible commercial use, free of charge
- **Commercial production use**: requires a commercial license from Nelson Grey LLC
- **Automatic conversion**: on December 13, 2029, this automatically converts to the Apache License 2.0

For commercial licensing inquiries, contact support@nelsongrey.com.

### Additional Resources

- [External Data Integration with Connectors](http://documentation.sas.com/?cdcId=cintcdc&cdcVersion=production.a&docsetId=cintag&docsetTarget=ext-connectors-manage.htm&locale=en#p0uwf5nm4rrkn1n1gwrm03rh911r) — SAS CI360 admin guide
- [Azure Functions Python developer guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
