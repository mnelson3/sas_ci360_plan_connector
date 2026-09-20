# SAS CI360 Plan Connector

> **Status: canonical.** The reference connector pattern for CI360's Plan connector framework — no duplicate implementation exists.

A serverless connector that lets [SAS Customer Intelligence 360](https://www.sas.com/en_us/software/customer-intelligence-360.html) (CI360) manage offers in a third-party offer/coupon platform through CI360's connector framework — deployable to **Azure Functions**, **AWS Lambda**, or **Google Cloud Functions** from the same integration logic.

<br>

### Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Endpoints](#endpoints)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Testing](#testing)
- [Registering the Connector in CI360](#registering-the-connector-in-ci360)
- [Branching Model](#branching-model)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Additional Resources](#additional-resources)

<br>

### Overview

CI360's connector framework lets a tenant call out to a third-party REST API directly, or through a small piece of custom integration code when the third-party API doesn't match what CI360 expects. This project is that custom integration layer: five CRUD operations (create, read one, read all, update, delete) on an offer, each of which translates a CI360 "Offer" attribute payload into the request/response shape required by a third-party offer-management API, signs the request with an HMAC signature, and forwards it on.

The integration logic — payload transformation, HMAC signing, and the HTTP call to the partner API — is written once, as a cloud-agnostic Python package (`connector/core/`), and imports no cloud SDK. Each cloud target is a thin adapter around it: a handful of handler functions that read the platform's own request format, fetch secrets from that platform's secret store, and call into `core`. Adding or dropping a cloud provider never touches the integration logic itself.

<br>

### Prerequisites

- A CI360 tenant with administrative rights
- Python 3.9+
- A cloud account for whichever target(s) you deploy to, plus its CLI tooling:
  - **Azure**: a subscription with access to Functions, API Management, and Key Vault, and the [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
  - **AWS**: an account with access to Lambda, API Gateway, and Secrets Manager, and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
  - **GCP**: a project with access to Cloud Functions (2nd gen) and Secret Manager, and the [gcloud CLI](https://cloud.google.com/sdk/docs/install)

<br>

### Project Structure

```
connector/
├── core/                       # Cloud-agnostic integration logic — no cloud SDK imports
│   ├── secrets.py              # SecretProvider contract + REQUIRED_SECRET_KEYS
│   ├── signing.py              # HMAC-SHA256 request signing
│   ├── transform.py            # CI360 offer payload -> partner API payload
│   └── offers.py               # create/read/read-by-id/update/delete, each calling the partner API
│
├── azure/                      # Azure Functions adapter
│   ├── host.json, requirements.txt, local.settings.json.example
│   ├── secrets_provider.py     # AzureKeyVaultSecretProvider
│   ├── build.sh                # Copies core/ in before `func azure functionapp publish`
│   └── createOffer/ readOffers/ readOfferById/ updateOffer/ deleteOffer/
│       (each an __init__.py entry point + function.json HTTP binding)
│
├── aws/                        # AWS Lambda adapter (SAM)
│   ├── template.yaml           # HTTP API + 5 Lambda functions
│   ├── handlers.py             # One handler per operation
│   ├── secrets_provider.py     # AWSSecretsManagerSecretProvider
│   ├── build.sh                # Copies core/ in before `sam build`
│   ├── requirements.txt, env.json.example
│
├── gcp/                        # GCP Cloud Functions (2nd gen) adapter
│   ├── main.py                 # 5 functions-framework HTTP entry points
│   ├── secrets_provider.py     # GCPSecretManagerSecretProvider
│   ├── build.sh                # Copies core/ in before `gcloud functions deploy`
│   ├── requirements.txt, .env.yaml.example
│
└── tests/                      # pytest suite covering connector/core (see Testing)
```

`core/` is the single source of truth. Each adapter's `build.sh` copies it into that adapter's own directory (`azure/core/`, `aws/core/`, `gcp/core/`) immediately before deploying, since each platform packages its function from its own directory; those copies are git-ignored.

<br>

### Endpoints

Every adapter exposes the same five operations. Azure and AWS take the offer id as a path segment; GCP takes it as a query parameter (`?id=...`), since Cloud Functions (2nd gen) HTTP triggers don't do path routing across separate functions the way Azure/AWS do — this keeps all three adapters' request shapes as close as possible.

| Operation | Method | Azure route | AWS route | GCP route |
|---|---|---|---|---|
| Create offer | POST | `/api/offers` | `/offers` | `/create-offer` |
| List offers | GET | `/api/offers` | `/offers` | `/read-offers` |
| Read offer by id | GET | `/api/offers/{id}` | `/offers/{id}` | `/read-offer-by-id?id=...` |
| Update offer | PUT | `/api/offers?id={id}` | `/offers/{id}` | `/update-offer?id=...` |
| Delete offer | DELETE | `/api/offers/{id}` | `/offers/{id}` | `/delete-offer?id=...` |

Every request is signed before it's sent to the downstream API: `core.signing.make_digest` builds an HMAC-SHA256 signature over the exact request URL using the partner API's shared secret, and `core.offers` appends it as an `authSignature` query parameter.

<br>

### Getting Started

1. Clone this repository.
2. Pick a cloud target and follow its steps below. `core/` needs no separate install — each adapter's `build.sh` copies it in before you run or deploy.

**Azure**
```
cd connector/azure
pip install -r requirements.txt
cp local.settings.json.example local.settings.json   # fill in for your environment
./build.sh
func start
```
Deploy with `func azure functionapp publish <app-name>` (or your CI/CD pipeline of choice) after running `build.sh`.

**AWS**
```
cd connector/aws
pip install -r requirements.txt
cp env.json.example env.json   # fill in for local `sam local` testing
./build.sh
sam build && sam deploy --guided --parameter-overrides SecretsManagerSecretName=<your-secret-name>
```

**GCP**
```
cd connector/gcp
pip install -r requirements.txt
cp .env.yaml.example .env.yaml   # fill in GCP_PROJECT_ID / GCP_SECRET_ID
./build.sh
gcloud functions deploy create-offer --gen2 --runtime=python311 \
  --entry-point=create_offer --trigger-http --env-vars-file=.env.yaml
```
Repeat the `gcloud functions deploy` step for each of `read-offers`, `read-offer-by-id`, `update-offer`, and `delete-offer`, setting `--entry-point` to the matching function in `main.py`.

<br>

### Configuration

This connector never stores third-party API credentials in source control. At runtime, each adapter's `SecretProvider` fetches the following keys (see `core/secrets.py`) from that cloud's own secret store:

| Key | Purpose |
|---|---|
| `ci360_connector_url` | Base URL CI360 uses to reach this connector |
| `ci360_connector_api_tenant_id` | CI360 tenant ID |
| `ci360_connector_api_secret` | Shared secret for the CI360-to-connector call |
| `partner_api_identifier` | Partner (offer/coupon platform) API client identifier |
| `partner_api_secret` | Partner API signing secret |
| `partner_api_url` | Base URL of the partner offer API |

`core.offers` validates that all six are present before signing a request, so a misconfigured secret store fails fast with a clear error rather than a downstream 401.

- **Azure**: one Key Vault secret per key (see `SECRET_NAME_MAP` in `azure/secrets_provider.py`), set `AZURE_KEY_VAULT_NAME` as an app setting.
- **AWS**: one Secrets Manager secret holding all six as a single JSON object, set `SECRETS_MANAGER_SECRET_NAME` (done for you via the SAM template parameter) and `AWS_REGION`.
- **GCP**: one Secret Manager secret holding all six as a single JSON object, set `GCP_PROJECT_ID` and `GCP_SECRET_ID` as environment variables.

Provision equivalent secrets for each environment you deploy to (sandbox, production, etc.) under names of your choosing — none of the adapters hardcode a secret name or environment suffix. `local.settings.json`, `env.json`, and `.env.yaml` are all git-ignored; use the `*.example` files as templates.

<br>

### Testing

```
pip install -r requirements-dev.txt
pytest connector/tests/
```

`connector/core/` has no cloud SDK dependencies, so it's fully unit-testable without a live Azure/AWS/GCP account — the suite covers request signing, secret validation, CI360-to-partner payload transformation, and the offer CRUD calls (with the outbound HTTP request mocked).

**All three cloud adapters are covered too** (0% before 2026-09-20; each adapter's `secrets_provider.py` and all 5 handler functions are now tested), without needing the real `azure-identity`/`boto3`/`google-cloud-secret-manager`/`azure-functions`/`functions-framework`/`flask` packages installed: fake modules are registered directly in `sys.modules` before the adapter code is imported, so no real cloud SDK is ever required just to run this test suite. See `connector/tests/_fakes.py` and `docs/DDD.md` §Testing design for how.

`connector/core` + all 3 adapters: 100% line coverage, 61 tests, as of 2026-09-20. CI runs this suite, plus flake8 and mypy (each cloud checked separately — see `docs/DDD.md`), on every push and pull request against `main`, `staging`, and `develop`.

<br>

### Registering the Connector in CI360

After deploying to your chosen cloud and exposing it behind that platform's own API gateway, register the resulting REST API as a connector endpoint in CI360:

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

- **Missing required secret(s) error from `core.offers`** — one of the six keys in `core/secrets.py` wasn't returned by your adapter's `SecretProvider`; check the secret names/JSON keys in your Key Vault / Secrets Manager / Secret Manager entry.
- **`401`/signature mismatch from the downstream API** — the HMAC signature is computed over the exact request URL sent to the partner API; confirm the base URL and timestamp aren't being altered after signing.
- **`ModuleNotFoundError: core` when running an adapter locally** — run that adapter's `build.sh` first; it copies `connector/core/` into the adapter directory so the platform's own packaging step picks it up.

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
- [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [Google Cloud Functions Python (2nd gen) guide](https://cloud.google.com/functions/docs/writing/write-http-functions)
