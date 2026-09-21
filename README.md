# Onlist Python SDK

The official Python client for [Onlist](https://onlist.io), the AI API marketplace.

Onlist aggregates 40+ AI model providers behind a single OpenAI-compatible API.
This SDK is a drop-in replacement for the OpenAI Python client, so you can switch
with one line of code.

[![PyPI version](https://img.shields.io/pypi/v/onlist.svg)](https://pypi.org/project/onlist/)
[![Python versions](https://img.shields.io/pypi/pyversions/onlist.svg)](https://pypi.org/project/onlist/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OnlistTeam/python-sdk/blob/main/LICENSE)

## Installation

```bash
pip install onlist
```

Requires Python 3.10 or newer.

## Quick Start

```python
from onlist import Onlist

client = Onlist(api_key="sk-...")  # or set ONLIST_API_KEY env var

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "What is Onlist?"}],
)
print(response.choices[0].message.content)
```

Get your API key at [onlist.io](https://onlist.io).

## Authentication

The client reads your API key from:
1. The `api_key` parameter
2. The `ONLIST_API_KEY` environment variable
3. The `OPENAI_API_KEY` environment variable (fallback, for easy migration)

```bash
export ONLIST_API_KEY="sk-..."
```

For the [Account API](#account-api) there is a second, optional credential —
a management key, read from the `management_key` parameter or
`ONLIST_MANAGEMENT_KEY`, falling back to your API key:

```bash
export ONLIST_MANAGEMENT_KEY="mgmt_..."
```

## Context Manager

Both sync and async clients support use as context managers, which ensures
the underlying HTTP connections are properly closed:

```python
from onlist import Onlist

with Onlist(api_key="sk-...") as client:
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)
# Connections are automatically closed here
```

```python
import asyncio
from onlist import AsyncOnlist

async def main():
    async with AsyncOnlist(api_key="sk-...") as client:
        response = await client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

## Provider Routing

Onlist's marketplace lets you choose which provider serves your request.
Use the `provider` field via `extra_body`:

```python
# Pin to a specific provider
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={"provider": "alice-shop"},
)

# Route to the cheapest provider
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={"provider": {"sort": "price"}},
)

# Full routing control
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={
        "provider": {
            "allow": ["alice-shop", "bob-relay"],
            "sort": "price",
            "allow_fallbacks": True,
            "max_price": {"prompt": 0.000003, "completion": 0.000015},
        }
    },
)
```

You can also use the typed helper:

```python
from onlist import ProviderRouting

routing = ProviderRouting(
    allow=["alice-shop", "bob-relay"],
    sort="price",
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={"provider": routing.model_dump(exclude_none=True)},
)
```

## Streaming

```python
stream = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Write a haiku about APIs"}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

## Async Usage

```python
import asyncio
from onlist import AsyncOnlist

async def main():
    client = AsyncOnlist(api_key="sk-...")

    response = await client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Marketplace API

Query the Onlist marketplace for models and providers:

```python
from onlist import Onlist

client = Onlist(api_key="sk-...")

# List available models with pricing
models = client.marketplace.models.list(limit=10)
for m in models.data:
    print(f"{m.id} - input: {m.pricing.prompt if m.pricing else 'N/A'}")

# Get detailed model info with all provider offers
detail = client.marketplace.models.get("anthropic/claude-sonnet-4")
print(f"{detail.id} - {len(detail.providers)} providers")

# Browse providers
providers = client.marketplace.providers.list()
for p in providers.data:
    print(f"{p.slug} - score: {p.score}")

# Get a specific provider's profile
provider = client.marketplace.providers.get("alice-shop")
print(f"{provider.display_name} - {provider.model_count} models")
```

To list only what your key can call, use `GET /v1/models/user` — the authenticated sibling of
`client.models.list()`. Handy for a model picker: the key's model access list and the
allow/deny of providers in its routing policy are applied server-side, so nothing in the
dropdown can come back as a `403`.

```python
mine = client.marketplace.models.list_for_user()
for m in mine.data:
    print(m.id)
```

## Rankings API

View model usage rankings and app usage data:

```python
from onlist import Onlist

client = Onlist(api_key="sk-...")

# Model usage leaderboard
rankings = client.marketplace.rankings.models(sort="popular", window="week")
for entry in rankings.leaderboard:
    print(f"#{entry.rank} {entry.model_name} by {entry.author} - {entry.total_tokens} tokens")

# Trending models
trending = client.marketplace.rankings.models(sort="trending", window="month")
for entry in trending.leaderboard:
    if entry.growth_pct is not None:
        print(f"{entry.model_name}: +{entry.growth_pct:.1f}%")

# App usage rankings
apps = client.marketplace.rankings.apps(sort="popular", window="month")
for app in apps.apps:
    print(f"#{app.rank} {app.title} ({app.domain}) - {app.total_requests} requests")

# Filter by category
coding_apps = client.marketplace.rankings.apps(category="coding")
for app in coding_apps.apps:
    print(f"{app.title}: {app.categories}")
```

## Account API

Balance, API key management, per-call costs and daily usage. These endpoints
are OpenRouter-compatible: same paths, same field names.

Most of them need a **management key** (`mgmt_...`), which you create at
[onlist.io/management-keys](https://onlist.io/management-keys). It is a
separate credential from your inference key and cannot make model calls:

```python
from onlist import Onlist

client = Onlist(api_key="sk-...", management_key="mgmt_...")
# or set ONLIST_API_KEY and ONLIST_MANAGEMENT_KEY
```

If you pass only `api_key`, it is used for the account endpoints too. That
matches OpenRouter's single-keyhole shape, and the server returns
`PermissionDeniedError` where a management key is actually required.

### Credits

```python
credits = client.credits.get()
balance = credits.total_credits - credits.total_usage
print(f"${balance:.4f} remaining")
```

### API keys

```python
# Create — `.key` is the plaintext secret, returned exactly once
created = client.api_keys.create("ci-runner", limit=5.0, limit_reset="daily")
print(created.key)

# List — fixed pages of 100, no total; read until you get a short page
keys = client.api_keys.list(offset=0, include_disabled=True)

# Read one
key = client.api_keys.get(created.data.hash)

# Update — omitted arguments are left unchanged, `None` clears the value
client.api_keys.update(key.hash, limit=None)      # remove the spend cap
client.api_keys.update(key.hash, disabled=True)   # stop it spending

client.api_keys.delete(key.hash)

# Describe the credential this client is holding
me = client.api_keys.current()
print(me.label, me.is_management_key)
```

`update()` distinguishes three states. An omitted argument is left alone; an
explicit `None` clears the value. Because of that, `name` and `disabled` do
not accept `None` at all — the server reads `{"name": null}` as an empty name
and `{"disabled": null}` as `false`, which would re-enable a key you only
meant to leave alone.

`limit_reset` accepts `"daily"`, `"weekly"`, or `None` for a lifetime total.

### Generation

What one call cost, and where it went. This one also accepts a plain
inference key, which can look up the calls it made itself:

```python
response = client.chat.completions.with_raw_response.create(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello!"}],
)
gen = client.generations.get(response.headers["X-Oneapi-Request-Id"])
print(f"{gen.provider_name}: ${gen.total_cost:.6f}, {gen.latency}ms to first token")
```

### Activity

Daily usage grouped by model and provider, covering the last 30 complete UTC
days. Today is excluded, so the same query always returns the same numbers:

```python
for row in client.activity.list():
    print(f"{row.date}  {row.model}  {row.requests} req  ${row.usage:.4f}")

# Narrow to one day or one key
client.activity.list(date="2026-09-05")
client.activity.list(api_key_hash="42")
```

## Sign in with Onlist

Let your users authorize your app and get their own inference key, without
ever pasting one. This is the OAuth PKCE flow, compatible with OpenRouter's:

```python
import webbrowser
from onlist import Onlist, exchange_auth_code, generate_pkce

verifier, challenge = generate_pkce()

webbrowser.open(
    "https://onlist.io/auth"
    "?callback_url=http://localhost:8976/callback"
    f"&code_challenge={challenge}"
    "&code_challenge_method=S256"
)

# ...user approves, your callback receives ?code=...

result = exchange_auth_code(code, code_verifier=verifier)
client = Onlist(api_key=result.key)  # a new sk-... key, scoped to that user
```

`exchange_auth_code()` is a module-level function, not a client method,
because an app running this flow has no API key yet — that is the whole point
of it — and constructing `Onlist` requires one. `async_exchange_auth_code()`
is the async version. If you already have a client, `client.oauth.exchange()`
does the same thing.

The code is single-use and is consumed even when the verifier does not match,
so a failed exchange means restarting the browser flow.

## Other APIs

Since Onlist is fully OpenAI-compatible, all standard endpoints work:

```python
# Embeddings
embedding = client.embeddings.create(
    model="openai/text-embedding-3-small",
    input="Hello world",
)

# Image generation
image = client.images.generate(
    model="openai/gpt-image-2",
    prompt="A sunset over Tokyo",
)

# Text-to-speech
audio = client.audio.speech.create(
    model="openai/tts-1",
    voice="alloy",
    input="Welcome to Onlist.",
)
```

## Error Handling

For OpenAI-compatible API calls (`chat.completions`, `embeddings`, etc.), the
standard `openai` exceptions are raised:

```python
import openai
from onlist import Onlist

client = Onlist(api_key="sk-...")

try:
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
    )
except openai.AuthenticationError:
    print("Invalid API key")
except openai.RateLimitError as e:
    print(f"Rate limited: {e.message}")
```

For marketplace API calls (`client.marketplace.*`), Onlist-specific exceptions
are raised:

```python
from onlist import Onlist, AuthenticationError, NotFoundError, APIError

client = Onlist(api_key="sk-...")

try:
    detail = client.marketplace.models.get("nonexistent/model")
except NotFoundError:
    print("Model not found")
except AuthenticationError:
    print("Invalid API key for marketplace")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

Account API calls raise the same family, plus `BadRequestError` (400) and
`PermissionDeniedError` (403). The server's message is passed through
unchanged:

```python
from onlist import Onlist, PermissionDeniedError

client = Onlist(api_key="sk-...")  # inference key only

try:
    client.credits.get()
except PermissionDeniedError as e:
    print(e.message)  # "Only management keys can perform this operation"
```

Marketplace requests are automatically retried on transient errors (408, 429, 5xx)
with exponential backoff. Configure the retry limit:

```python
# Disable retries
client = Onlist(api_key="sk-...", max_retries=0)

# More retries
client = Onlist(api_key="sk-...", max_retries=5)
```

Only `GET` requests are retried. Creating a key or exchanging an
authorization code is never replayed: a duplicate key or a burnt code is
worse than surfacing the transient error.

## Migrate from OpenAI or OpenRouter

Already using the OpenAI SDK? Change one line:

```diff
- from openai import OpenAI
- client = OpenAI(api_key="sk-...")
+ from onlist import Onlist
+ client = Onlist(api_key="sk-...")
```

Or, if you prefer to keep using `openai` directly:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-onlist-key",
    base_url="https://onlist.io/v1",
)
```

## Routing Metadata

Onlist returns routing information in response headers. Access them to see
which provider actually served your request:

```python
# Use the with_raw_response pattern from the openai SDK:
raw_response = client.chat.completions.with_raw_response.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
print(raw_response.headers.get("x-onlist-route-id"))
print(raw_response.headers.get("x-onlist-provider"))

# Parse the completion as usual:
response = raw_response.parse()
print(response.choices[0].message.content)
```

## Links

- [Onlist Website](https://onlist.io)
- [API Documentation](https://onlist.io/docs)
- [Model Catalog](https://onlist.io/models)
- [Provider Directory](https://onlist.io/providers)
- [GitHub](https://github.com/OnlistTeam/python-sdk)
