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
    print(f"{m['id']} - input: {m.get('pricing', {}).get('prompt', 'N/A')}")

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
from onlist import Onlist, AuthenticationError, APIError

client = Onlist(api_key="sk-...")

try:
    providers = client.marketplace.providers.list()
except AuthenticationError:
    print("Invalid API key for marketplace")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

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
