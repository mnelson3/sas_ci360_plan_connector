# Security Policy

## Supported Versions

This repository holds the SAS CI360 Plan Connector (Azure Functions). Only the code currently deployed on each environment branch is supported — there is no long-term support for older commits.

| Branch | Environment | Status |
|---|---|---|
| `main` | Production | Supported |
| `staging` | Staging | Supported |
| `develop` | Development | Supported |

## Reporting a Vulnerability

This is a private repository, so please do not open a public issue for a security concern.

Instead, email **support@nelsongrey.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a proof of concept if available
- Any relevant logs or affected code paths

You should get an acknowledgement within a few business days.

## Automated Dependency Scanning

Dependabot alerts and security updates are enabled on this repository. Native GitHub secret scanning and code scanning (CodeQL) require GitHub Advanced Security, which isn't currently licensed for this org's private repositories, so neither is enabled here. Avoid committing credentials or secrets to this repo regardless — third-party API credentials are managed via Azure Key Vault and Azure Function App settings, never committed to source. `connector/local.settings.json` is git-ignored for the same reason; use `connector/local.settings.json.example` as a template.
