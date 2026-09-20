# Technical Requirements Document — sas-ci360-plan-connector

| | |
| --- | --- |
| Document | TRD-PLANCONNECTOR-1.0 |
| Owner | Nelson Grey LLC |

## 1. Overview & traceability

| BRD | TRD | Relationship |
| --- | --- | --- |
| PLANCONNECTOR-BR-1 | PLANCONNECTOR-NFR-1 | `core` cloud-SDK-free → enforced by never importing one, verified by `core`'s tests never needing one installed. |
| PLANCONNECTOR-BR-2 | PLANCONNECTOR-NFR-2 | No stored credentials → every `SecretProvider` resolves from a live cloud secret store, never a file. |
| PLANCONNECTOR-BG-3 | PLANCONNECTOR-NFR-3 | Coverage across `core` + adapters → real gap closed 2026-09-20. |

## 2. Functional requirements

| ID | Requirement | Location |
| --- | --- | --- |
| PLANCONNECTOR-FR-1 | Create/read (single)/read (list)/update/delete an offer, transforming CI360's payload shape to the partner API's. | `core/offers.py`, `core/transform.py` |
| PLANCONNECTOR-FR-2 | Sign every outbound request with HMAC-SHA256 over the exact request URL. | `core/signing.py` |
| PLANCONNECTOR-FR-3 | Validate that all 6 required secret keys are present before signing a request. | `core/secrets.py` |
| PLANCONNECTOR-FR-4 | Resolve secrets from Azure Key Vault at runtime. | `azure/secrets_provider.py::AzureKeyVaultSecretProvider` |
| PLANCONNECTOR-FR-5 | Resolve secrets from AWS Secrets Manager at runtime (one JSON secret holding all 6 keys). | `aws/secrets_provider.py::AWSSecretsManagerSecretProvider` |
| PLANCONNECTOR-FR-6 | Resolve secrets from GCP Secret Manager at runtime (one JSON secret holding all 6 keys). | `gcp/secrets_provider.py::GCPSecretManagerSecretProvider` |
| PLANCONNECTOR-FR-7 | Expose all 5 operations as Azure Functions HTTP triggers. | `azure/createOffer,readOffers,readOfferById,updateOffer,deleteOffer/__init__.py` |
| PLANCONNECTOR-FR-8 | Expose all 5 operations as AWS Lambda handlers (API Gateway HTTP API, payload format 2.0). | `aws/handlers.py` |
| PLANCONNECTOR-FR-9 | Expose all 5 operations as GCP Cloud Functions (2nd gen) HTTP entry points. | `gcp/main.py` |

## 3. Non-functional requirements

| ID | Category | Requirement | Status (2026-09-20) |
| --- | --- | --- | --- |
| PLANCONNECTOR-NFR-1 | Architecture | `core/` imports no cloud SDK. | Verified by construction — every cloud-specific import lives in that cloud's own adapter directory. |
| PLANCONNECTOR-NFR-2 | Security | No third-party credential in source control. | Verified: `local.settings.json`/`env.json`/`.env.yaml` are git-ignored; `.example` templates committed instead. |
| PLANCONNECTOR-NFR-3 | Testability | Every cloud adapter — not just `core` — must be independently unit-testable without a real cloud account or the real cloud SDK installed. | **Real gap closed 2026-09-20**: `core` was at 96% coverage; all three adapters were at 0% and weren't even in CI's lint/mypy/test scope. Added 31 tests using `sys.modules` stubbing for `azure-identity`/`boto3`/`google-cloud-secret-manager`/`azure-functions`/`functions-framework`/`flask`, so no real cloud SDK install is needed to run them. `core` + all 3 adapters: 100% line coverage, 61 tests. |
| PLANCONNECTOR-NFR-4 | Type safety | Every cloud adapter must pass mypy, checked separately per cloud. | **Found and fixed**: running mypy against the adapters for the first time caught 3 real (minor) type-hint bugs — implicit-Optional `str = None` constructor defaults — across all three `secrets_provider.py` files, widened to `Optional[str]`. Each cloud is mypy-checked in its own invocation (`mypy connector/azure`, `mypy connector/aws`, `mypy connector/gcp`) because `azure/secrets_provider.py` and `aws/secrets_provider.py` share the bare module name `secrets_provider`, which mypy treats as a collision if checked together. |
| PLANCONNECTOR-NFR-5 | Request integrity | Every outbound request to the partner API is HMAC-signed. | Verified: `core.offers._build_signed_url` appends `authSignature`; `core/tests/test_offers.py` and `test_signing.py` cover it directly. |

## 4. Integration requirements

- **CI360 side**: registered as a connector endpoint via CI360's Plan connector framework (admin-guide links in `README.md` §Registering the Connector in CI360).
- **Partner side**: the partner offer API's own base URL, identifier, and signing secret — resolved per cloud, never hardcoded (see PLANCONNECTOR-FR-4 through PLANCONNECTOR-FR-6).
- **By-id routing differs per cloud**: Azure/AWS use a path segment (`/offers/{id}`); GCP uses a query parameter (`?id=...`), since GCP Cloud Functions (2nd gen) HTTP triggers don't route by path across separate functions the way Azure/AWS do. `core.offers` itself is agnostic to this — each adapter's handler extracts the id its own way before calling into `core`.

## 5. Data requirements

6 required secret keys (see `core/secrets.py::REQUIRED_SECRET_KEYS`): `ci360_connector_url`, `ci360_connector_api_tenant_id`, `ci360_connector_api_secret`, `partner_api_identifier`, `partner_api_secret`, `partner_api_url`.

## 6. Technology stack

`core`: `urllib3` only (no cloud SDK, no `requests` — a deliberate choice to keep the shared package's own dependency surface minimal). Per-cloud adapters: `azure-functions`/`azure-identity`/`azure-keyvault-secrets`; `boto3`; `functions-framework`/`google-cloud-secret-manager`/`flask`.

## 7. Environments

No environment-name config field in this repository (unlike `sas-ci360-sdk`'s domain clients) — environment separation is handled by provisioning separate secrets per environment under names of your choosing (see `README.md` §Configuration) and deploying to separate cloud resources per environment.

## 8. Dependency policy

Same PLANCONNECTOR-NFR-8 pattern as `sas-ci360-sdk`: a dependency is declared only where the code that declares it actually imports it. `core`'s `requirements-dev.txt` deliberately excludes every cloud SDK, since `core` itself never imports one and the adapter tests fake them via `sys.modules` rather than installing them (see PLANCONNECTOR-NFR-3 above).

## 9. Testing strategy

`core/tests/` — mocks the outbound HTTP call (`urllib3.PoolManager`) directly; covers signing, secret validation, payload transformation, and all 5 CRUD operations including `update_offer` (previously untested despite the other 4 each having a direct test).

`azure/aws/gcp` adapter tests — one `test_<cloud>_secrets_provider.py` and one `test_<cloud>_handlers.py` (`test_gcp_main.py` for GCP) per cloud, all in `connector/tests/` alongside `core`'s own tests. Each fakes its cloud's SDK via `_fakes.py::install_fake_module`, loads the real adapter module via `importlib.util.spec_from_file_location` under a private synthetic name (so `azure/secrets_provider.py` and `aws/secrets_provider.py` — same bare module name — never collide when the full suite runs together), and patches `core.offers`'s functions directly to test wiring (event parsing → the right `core` call → response shaping), leaving `core`'s own logic to its own dedicated tests.

Live-tenant / UAT coverage (a real CI360 tenant, a real partner API, a real cloud deployment) is not yet implemented for this repository — see [sas-ci360-sdk/UAT.md](https://github.com/mnelson3/sas-ci360-sdk/blob/main/UAT.md) §What's covered, which names this repository as follow-up work rather than silently omitted, and explains why it's more involved than the SDK's own tenant-only UAT tier (it would need real cloud deployment credentials in addition to CI360 and partner-API ones).

## 10. CI/CD requirements

flake8 and pytest run across `connector/core` and, since 2026-09-20, `connector/azure`/`connector/aws`/`connector/gcp` too. mypy runs against `connector/core` plus each cloud separately (see PLANCONNECTOR-NFR-4 above).
