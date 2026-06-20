"""List models and providers from the Onlist marketplace."""

from onlist import Onlist

client = Onlist(api_key="unused")  # marketplace APIs are mostly public

# List models
print("=== Models ===")
models = client.marketplace.models.list(limit=5)
for m in models.data:
    pricing = m.get("pricing", {})
    print(f"  {m['id']:40s}  input=${pricing.get('prompt', '?')}/tok")

# List providers
print("\n=== Providers ===")
providers = client.marketplace.providers.list()
for p in providers.data:
    print(f"  @{p.slug:20s}  score={p.score}  models={p.model_count}")
