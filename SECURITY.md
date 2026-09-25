# Security Policy

## Supported Versions

This repository holds the actively maintained SAS CI360 Plan Connector — an Azure Functions connector that lets SAS Customer Intelligence 360 manage offers in a third-party offer/coupon platform through CI360's connector framework. Only the code currently deployed on each environment branch is supported — there is no long-term support for older commits.

| Branch | Environment | Status |
|---|---|---|
| `main` | Production | Supported |
| `staging` | Staging | Supported |
| `develop` | Development | Supported |

## Reporting a Vulnerability

This repository doesn't have a public issue tracker, so please don't report security concerns that way. Use one of:

- GitHub's [private vulnerability reporting](https://github.com/mnelson3/sas_ci360_plan_connector/security/advisories/new) (enabled on this repo), or
- Email **support@nelsongrey.com**

Either way, include:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a proof of concept if available
- Any relevant logs, request/response samples, or affected endpoints

You should get an acknowledgement within a few business days.

## Automated Dependency Scanning

Dependabot alerts and security updates, native GitHub secret scanning (with push protection), and code scanning (CodeQL) are all enabled on this repository. Avoid committing credentials or secrets regardless — third-party API credentials are managed via Azure Key Vault and Azure Function App settings, never committed to source. `connector/local.settings.json` is git-ignored for the same reason; use `connector/local.settings.json.example` as a template.
