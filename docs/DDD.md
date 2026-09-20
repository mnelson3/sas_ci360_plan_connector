# Detailed Design Document — sas-ci360-plan-connector

| | |
| --- | --- |
| Document | DDD-PLANCONNECTOR-1.0 |
| Owner | Nelson Grey LLC |

## Architecture overview

Layer 4 of the CI360 Connect toolkit — see [sas-ci360-sdk/docs/DDD.md](https://github.com/mnelson3/sas-ci360-sdk/blob/main/docs/DDD.md) for the full 4-layer picture.

```
CI360's connector framework
        │  calls whichever cloud's endpoint is registered
        ▼
Cloud adapter (azure/ | aws/ | gcp/)
        │  parses the platform's native request, fetches secrets
        ▼
core/  (payload transform, HMAC signing, the HTTP call to the partner API)
        │
        ▼
Third-party partner offer/coupon API
```

`core` is the single source of truth for the integration logic; each adapter's `build.sh` copies it into that adapter's own directory immediately before packaging, since every platform expects to deploy from one self-contained directory.

## Why each cloud adapter had zero tests until 2026-09-20

`core` was always independently unit-testable (no cloud SDK import), and had 96% coverage. The three adapters were never brought into the same testing discipline — not because they're harder to test in principle, but because doing so naively would mean installing three separate cloud SDKs (`azure-identity`, `boto3`, `google-cloud-secret-manager`) plus `azure-functions`, `functions-framework`, and `flask`, just to run a test suite that never needs to talk to a real cloud.

## The testing approach: fake the SDK, load the module directly

`connector/tests/_fakes.py::install_fake_module(dotted_name)` registers a `types.ModuleType` directly in `sys.modules`, wiring parent packages recursively (so `install_fake_module("win32.win32event")`-style dotted paths resolve without a real namespace package):

```python
def install_fake_module(dotted_name):
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]
    module = types.ModuleType(dotted_name)
    sys.modules[dotted_name] = module
    if "." in dotted_name:
        parent_name, attr = dotted_name.rsplit(".", 1)
        parent = install_fake_module(parent_name)
        setattr(parent, attr, module)
    return module
```

This is the exact pattern `sas-ci360-sdk`'s `sol-identity` package established first for its own uninstalled private dependency, and `sas-ci360-solutions`'s `SASCI360Service` tests later reused for pywin32 — this repository is the third and most elaborate application of it, faking three different cloud SDKs' worth of namespaces in one test suite.

**Handler modules are loaded via `importlib.util.spec_from_file_location`, under a private synthetic name**, rather than a normal `import`:

```python
spec = importlib.util.spec_from_file_location(
    "_azure_{0}_under_test".format(function_dir),
    AZURE_DIR / function_dir / "__init__.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

This matters specifically because `azure/secrets_provider.py` and `aws/secrets_provider.py` share the exact bare module name `secrets_provider` — the handler code in each cloud does `from secrets_provider import ...`. If all three clouds' tests ran in one process using ordinary `sys.path` insertion and `import`, the second cloud's test to run would get the *first* cloud's cached `secrets_provider` module instead of its own. Loading by explicit file path under a unique synthetic name sidesteps the collision entirely; the bare `secrets_provider` name itself is faked per-test via `install_fake_module("secrets_provider")` immediately before loading each handler, so each test controls exactly which fake `SecretProvider` class the handler under test sees.

## The 3 type-hint bugs mypy caught

Checking each adapter's types for the first time (as part of adding this test coverage) surfaced a real, minor, but genuine bug pattern repeated identically across all three `secrets_provider.py` files:

```python
def __init__(self, vault_name: str = None):   # implicit Optional under PEP 484
```

mypy's modern default (`no_implicit_optional=True`) correctly flags this — `str = None` isn't a valid default for a parameter typed `str`. Fixed by widening to `Optional[str]` in all three files. This required checking each cloud's `secrets_provider.py` in its own mypy invocation (see TRD.md NFR-4) — checking `connector/azure` and `connector/aws` together produces a `Duplicate module named "secrets_provider"` error, the same bare-module-name collision the test-loading approach above was built to avoid.

## Testing design

`connector/tests/` holds `core`'s own tests (`test_offers.py`, `test_secrets.py`, `test_signing.py`, `test_transform.py`, `conftest.py`) alongside the per-cloud adapter tests (`test_azure_secrets_provider.py`, `test_azure_handlers.py`, `test_aws_secrets_provider.py`, `test_aws_handlers.py`, `test_gcp_secrets_provider.py`, `test_gcp_main.py`) and the shared `_fakes.py` helper — all runnable together with one `pytest connector/tests/` invocation, at 100% combined coverage.

## CI/CD pipeline

flake8 (hard gate + advisory) runs across `connector/core`, `connector/azure`, `connector/aws`, `connector/gcp`, and `connector/tests`. mypy runs `connector/core` then each cloud separately (see TRD.md NFR-4). pytest runs the whole `connector/tests/` directory in one pass.
