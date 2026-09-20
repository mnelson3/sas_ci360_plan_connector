# Business Requirements Document — sas-ci360-plan-connector

| | |
| --- | --- |
| Document | BRD-PLANCONNECTOR-1.0 |
| Owner | Nelson Grey LLC |
| Scope | Layer 4 of the CI360 Connect toolkit: the multi-cloud Plan connector |
| Basis | Adapted from the CI360 Connect BRD/TRD/DD (v1.1, 2026-09-20), scoped to this repository |
| Related | [sas-ci360-sdk BRD](https://github.com/mnelson3/sas-ci360-sdk/blob/main/docs/BRD.md) (Layers 1–2) |

## 1. Executive summary

`sas-ci360-plan-connector` is the reference implementation of CI360's Plan connector framework — the mechanism CI360 uses to call out to a third-party offer/coupon platform when that platform's own API doesn't match what CI360's connector framework expects. It implements the full CRUD round trip (create/read/update/delete an offer) once, as cloud-agnostic integration logic, deployable unchanged to Azure Functions, AWS Lambda, or GCP Cloud Functions.

## 2. Business context

CI360's Plan API includes a connector framework for third-party rewards/coupon platform integration, but the actual integration code — payload transformation, request signing, secret handling — is the implementer's responsibility. This repository is a complete, working reference for that: one cloud-agnostic `core` package plus one thin adapter per cloud target, so an implementer choosing (or later switching) a cloud provider doesn't need to rewrite the integration logic itself.

## 3. Goals & objectives

| ID | Objective | Primary metric |
| --- | --- | --- |
| PLANCONNECTOR-BG-1 | Demonstrate the full CRUD round trip against CI360's connector framework, deployable unchanged to 3 cloud targets. | 1 reference connector, 3 cloud targets |
| PLANCONNECTOR-BG-2 | Keep the integration logic (`core`) free of any cloud SDK import, so adding or dropping a cloud target never touches it. | 0 cloud-SDK imports in `core/` |
| PLANCONNECTOR-BG-3 | Every operation — `core` and every cloud adapter — verifiable without a live cloud account or live CI360 tenant. | 100% line coverage, `core` + all 3 adapters (achieved 2026-09-20) |
| PLANCONNECTOR-BG-4 | Never store a third-party API credential in source control. | Every secret resolved from that cloud's own secret store at runtime |

## 4. Stakeholders

- **Implementation engineer** integrating CI360's Plan connector framework with a specific third-party offer platform.
- **Integration architect** deciding which cloud to deploy the connector to, or evaluating a multi-cloud strategy.

## 5. Scope

### In scope
Offer create/read (single + list)/update/delete; HMAC-SHA256 request signing; CI360-to-partner payload transformation; per-cloud secret resolution (Azure Key Vault, AWS Secrets Manager, GCP Secret Manager); Azure Functions, AWS Lambda (via SAM), and GCP Cloud Functions (2nd gen) adapters.

### Out of scope
- The Plan API client for CI360-side campaign/audience management — that's `sol-planning`, in `sas-ci360-sdk`.
- Any cloud target beyond Azure/AWS/GCP.
- The third-party partner platform's own API design — this connector adapts to whatever shape it already expects.

## 6. Business requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| PLANCONNECTOR-BR-1 | `core/` must not import any cloud SDK. | P1 |
| PLANCONNECTOR-BR-2 | No third-party API credential may appear in source control, `local.settings.json`, `env.json`, or `.env.yaml` — all are git-ignored, with `.example` templates committed instead. | P1 |
| PLANCONNECTOR-BR-3 | Every cloud adapter must expose the same five operations, even where each platform's own request-routing conventions differ (Azure/AWS use path segments for the by-id operations, GCP uses a query parameter). | P2 |
| PLANCONNECTOR-BR-4 | Adding a fourth cloud target must mean writing one more adapter, not modifying `core`. | P2 |

## 7. Success metrics

- **Coverage parity across clouds**: no cloud adapter left untested while another is covered (was the case until 2026-09-20 — `core` had tests, none of the three adapters did).
- Same categories as the parent SDK — see [sas-ci360-sdk/docs/BRD.md](https://github.com/mnelson3/sas-ci360-sdk/blob/main/docs/BRD.md) §7.

## 8. Assumptions & constraints

- Assumes the third-party partner platform is reachable over HTTPS and accepts an HMAC-SHA256-signed request — this connector doesn't negotiate a different auth scheme.
- Each cloud's own hosted-runner CI cost model may differ; this repository's own CI runs on standard GitHub-hosted `ubuntu-latest` runners with no cloud-specific compute, so evaluating a cloud target doesn't incur CI cost by itself.

## 9. Licensing

Nelson Grey LLC Community License 1.0 — see [LICENSE](../LICENSE).
