"""Chat completion with provider routing."""

from onlist import Onlist, ProviderRouting

client = Onlist()

# Option 1: Pin to a specific provider (string shorthand)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"provider": "alice-shop"},
)
print("Provider pin:", response.choices[0].message.content)

# Option 2: Route to cheapest provider
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"provider": {"sort": "price"}},
)
print("Cheapest:", response.choices[0].message.content)

# Option 3: Use the typed ProviderRouting helper
routing = ProviderRouting(sort="price", allow_fallbacks=True)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"provider": routing.model_dump(exclude_none=True)},
)
print("Typed routing:", response.choices[0].message.content)
