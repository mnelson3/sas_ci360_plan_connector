# Implementer Guide — sas-ci360-plan-connector

A practical walkthrough for deploying this connector against your own partner platform, or adapting it to a fourth cloud target. For requirements and design rationale, see [`docs/`](docs/); for the reference CLI/deployment steps for each existing cloud, see [`README.md`](README.md) §Getting Started — this guide covers what's *not* in a quick-start.

## 1. Understand the shape before you touch a cloud

```
core/secrets.py    - the 6 required secret keys, validated before any request goes out
core/signing.py    - HMAC-SHA1 over the exact request URL
core/transform.py  - CI360's offer payload shape -> the partner API's shape
core/offers.py     - the 5 CRUD calls, each: build signed URL -> transform (if applicable) -> HTTP call
```

Everything cloud-specific — `azure/`, `aws/`, `gcp/` — exists only to get a request from that platform's native trigger format into a call on `core`, and a `core` result back into that platform's native response format. If you're changing behavior (a new field in the partner payload, a different signing scheme), change it in `core` once; if you're changing where secrets come from or how a request arrives, that's adapter-only.

## 2. Point this at your own partner platform

`core/transform.py::transform_json` is the one place CI360's offer-field shape gets mapped to what your partner API expects. Read it alongside `core/tests/test_transform.py` (the test fixtures show a real example payload in both shapes) before changing it — the fields your partner platform doesn't use should simply not be copied over, not mapped to a placeholder.

`core/secrets.py::REQUIRED_SECRET_KEYS` names the 6 keys every `SecretProvider` must supply. If your partner platform's auth model needs a 7th piece of information (e.g. a separate signing algorithm identifier), add it here and to every cloud's `SecretProvider` and `*.example` config template together — a partial update here is exactly the kind of drift `core.offers`'s fail-fast validation exists to catch, but only if every adapter's secret store actually has the new key provisioned.

## 3. Deploy, then verify against a real tenant

The README's Getting Started section covers the deploy commands per cloud. After deploying:

1. **Register the connector in CI360** (README §Registering the Connector in CI360 has the admin-guide links) pointing at your deployed function app's URL.
2. **Trigger a real create-offer call from CI360** and confirm it reaches your partner API with a valid signature — the fastest way to catch a secret-store misconfiguration is a real round trip, since `core.offers`'s validation only catches *missing* keys, not wrong values.
3. There's no automated live-tenant/UAT tier for this repository yet (see `docs/TRD.md` §9) — this manual verification is currently the only way to confirm a real deployment works end to end. If you build one, follow the pattern `sas-ci360-sdk/UAT.md` establishes: env-var-gated, skipped not failed when credentials are absent, never run in the default CI job.

## 4. Adding a fourth cloud target

1. Create `connector/<cloud>/` with a `secrets_provider.py` implementing `core.secrets.SecretProvider`'s contract (fetch all 6 keys from that cloud's own secret store) and a `build.sh` that copies `core/` in before packaging.
2. Write 5 handler entry points (however that platform's function framework expects them) that each: parse the platform's native request, call the matching `core.offers` function, shape the result into that platform's native response.
3. Don't touch `core/` unless you're fixing something genuinely wrong there — the whole point of this architecture is that a new cloud target never requires it.
4. Add tests the same way the existing three clouds do: fake that cloud's SDK via `connector/tests/_fakes.py::install_fake_module` (see `docs/DDD.md` §The testing approach), load the handler module via `importlib.util.spec_from_file_location` under a private name if your new adapter's module names could collide with an existing one (they will, if you reuse `secrets_provider.py` as the filename, which is the established convention), and patch `core.offers`'s functions directly to test wiring rather than re-testing `core`'s own logic.
5. Add a CI job entry: lint, mypy (in its own invocation — see `docs/TRD.md` NFR-4 for why), and include your new test files in the `pytest connector/tests/` run (no config needed — pytest picks up any `test_*.py`/`Test*.py` file under that directory automatically).

## 5. Common pitfalls

- **Don't give a new cloud's `secrets_provider.py` module the same bare name as an existing one without checking `docs/DDD.md`'s collision note first** — `secrets_provider` is already shared by `azure/` and `aws/`, and mypy/tests already work around it; a fourth cloud using the same filename works fine with the existing conventions, but skipping straight to `import secrets_provider` in a new test file (instead of the fake-then-load-by-path pattern) will silently pick up whichever cloud's fake happened to load first.
- **Don't skip `core.secrets`'s validation by hardcoding a secret value "just for testing."** If a key is missing, you want `core.offers` to fail loudly before it ever builds a signed URL, not send a request with an empty signature.
- **Don't assume by-id routing works the same across clouds.** Azure/AWS use a path segment; GCP uses a query parameter. This is a real platform constraint (GCP Cloud Functions 2nd gen HTTP triggers don't route by path across separate functions), not an inconsistency to "fix."
