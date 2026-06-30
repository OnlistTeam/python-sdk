# Changelog

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
