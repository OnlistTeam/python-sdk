# Changelog

## 0.4.0 (2026-09-21)

### Added
- `marketplace.models.list_for_user()` (and the `AsyncOnlist` mirror) — `GET /v1/models/user`,
  the OpenRouter-aligned authenticated catalog. Returns the same entry shape as
  `client.models.list()`, filtered to what the client's API key can actually call: its model
  access list, then the denied providers of its routing policy, then its allowed providers.
  The allowed-provider filter applies even when the key falls back to every provider once its
  allowlist is exhausted. Built for a model picker holding one specific key.
- `UserModelListResponse` type (`object` + `data`), exported from the top-level package.

## 0.3.0 (2026-09-07)

### Added
- **Account API** — the OpenRouter-compatible `/api/v1/*` face, as five namespaces on the client:
  - `credits.get()` — account balance.
  - `api_keys.current() / list() / create() / get() / update() / delete()` — inference key management. `create()` returns the plaintext secret once.
  - `generations.get(request_id)` — cost, tokens and latency for one call, keyed on the `X-Oneapi-Request-Id` response header.
  - `activity.list()` — daily usage by model and provider, last 30 complete UTC days.
  - `oauth.exchange()` — "Sign in with Onlist" PKCE authorization-code exchange.
- `management_key` client parameter and `ONLIST_MANAGEMENT_KEY` environment variable. Falls back to the API key, so a single-credential client still reaches the account endpoints.
- `generate_pkce()` module-level helper returning an S256 `(verifier, challenge)` pair.
- `exchange_auth_code()` / `async_exchange_auth_code()` module-level functions for the OAuth exchange. `client.oauth.exchange()` does the same thing, but constructing `Onlist` requires an API key and an app running the sign-in flow does not have one yet.
- Account response types: `APIKey`, `CurrentKey`, `CreatedKey`, `Credits`, `Generation`, `ActivityRow`, `ExchangedKey`, `RateLimit`. Field names match the wire format one-for-one, and all allow extra keys.
- `BadRequestError` (400) and `PermissionDeniedError` (403) exceptions.
- Full `AsyncOnlist` coverage for every new namespace.

### Fixed
- Error responses whose `code` is an integer no longer raise `AttributeError` while being parsed. The account API sends the HTTP status as an int, so every 4xx/5xx from it used to crash inside the error handler.
- `examples/list_models.py` and `examples/async_usage.py` still used dict subscripting on model objects, which stopped working when responses became typed in 0.2.0.

### Changed
- Retries are now limited to `GET`. Replaying `POST /api/v1/keys` would mint a second key and replaying the OAuth exchange would burn an already-consumed code; marketplace behaviour is unchanged, since it is all reads.
- The request loop, envelope parsing and retry policy moved to a shared internal transport module. No public API change.

## 0.2.1 (2026-06-30)

### Fixed
- Python 3.9 compatibility: added the `eval_type_backport` dependency so `X | Y` annotations resolve at runtime.
- `OPENAI_API_KEY` is read as a fallback when `ONLIST_API_KEY` is unset, matching the TypeScript SDK and the docs.

## 0.2.0 (2026-06-30)

### Added
- Rankings API: `marketplace.rankings.models()` and `marketplace.rankings.apps()` for model usage leaderboards and app usage data.
- `NotFoundError` exception for 404 responses.
- Context manager support for `Onlist`, `AsyncOnlist`, `Marketplace`, and `AsyncMarketplace`.
- Automatic retry with exponential backoff and jitter for transient errors (408, 429, 5xx) on marketplace requests. Configurable via `max_retries` parameter.
- `ProviderOffer` type exported from top-level package.

### Changed
- `ModelListResponse.data` is now `list[Model]` instead of `list[dict]`, giving typed access to model fields.
- `ModelDetail` now inherits from `Model` instead of duplicating all fields.
- `ProviderDetail` now inherits from `Provider` instead of duplicating all fields.

## 0.1.0 (2026-06-20)

Initial release.

- Drop-in replacement for `openai.OpenAI` / `openai.AsyncOpenAI`.
- Marketplace API: models, providers.
- Provider routing with typed `ProviderRouting` helper.
- Full async support via `AsyncOnlist`.
