"""Account API: balance, key management, per-call costs, and daily usage.

Everything except ``generations.get()`` needs a management key (``mgmt_...``),
which you create at https://onlist.io/management-keys. Set it as
``ONLIST_MANAGEMENT_KEY`` or pass it explicitly, as below.
"""

import sys

from onlist import Onlist, PermissionDeniedError, exchange_auth_code, generate_pkce

client = Onlist(api_key="sk-...", management_key="mgmt_...")

# --- Balance ---------------------------------------------------------------
credits = client.credits.get()
print(f"balance: ${credits.total_credits - credits.total_usage:.4f} USD")
print(f"  purchased ${credits.total_credits:.2f}, used ${credits.total_usage:.2f}")

# --- Which credential am I holding? ----------------------------------------
current = client.api_keys.current()
print(f"credential: {current.label} (management={current.is_management_key})")

# --- Manage inference keys -------------------------------------------------
created = client.api_keys.create("ci-runner", limit=5.0, limit_reset="daily")
# `created.key` is the only time you will ever see the plaintext secret.
print(f"created {created.data.hash}: {created.key}")

# Omitted arguments are left alone; `None` clears the value.
client.api_keys.update(created.data.hash, limit=None)  # drop the spend cap
client.api_keys.update(created.data.hash, disabled=True)  # stop it spending

# Pages are a fixed 100 with no total — read until you get a short page.
offset = 0
while True:
    page = client.api_keys.list(offset=offset, include_disabled=True)
    for key in page:
        print(f"  {key.hash:>6}  {key.name:20s}  ${key.usage:.4f} used")
    if len(page) < 100:
        break
    offset += 100

client.api_keys.delete(created.data.hash)

# --- What did one call cost? ----------------------------------------------
response = client.chat.completions.with_raw_response.create(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello!"}],
)
request_id = response.headers.get("X-Oneapi-Request-Id")
if request_id:
    gen = client.generations.get(request_id)
    print(f"{gen.model} via {gen.provider_name}: ${gen.total_cost:.6f}")
    print(f"  {gen.tokens_prompt} in / {gen.tokens_completion} out, {gen.latency}ms to first token")

# --- Daily usage rollups ---------------------------------------------------
# Last 30 complete UTC days; today is excluded because it is still moving.
for row in client.activity.list():
    print(f"{row.date}  {row.model:35s}  {row.requests:5d} req  ${row.usage:.4f}")

# --- Sign in with Onlist (PKCE) -------------------------------------------
# Sketch: the user approves in a browser and your callback receives ?code=...
# `exchange_auth_code` is module-level because an app running this flow has no
# API key yet, and constructing `Onlist` requires one.
verifier, challenge = generate_pkce()
print(
    "open: https://onlist.io/auth"
    "?callback_url=http://localhost:8976/callback"
    f"&code_challenge={challenge}&code_challenge_method=S256"
)
code = sys.argv[1] if len(sys.argv) > 1 else ""
if code:
    exchanged = exchange_auth_code(code, code_verifier=verifier)
    print(f"user key: {exchanged.key}")

# --- What an inference key gets on the account face ------------------------
buyer = Onlist(api_key="sk-...")  # no management key
try:
    buyer.credits.get()
except PermissionDeniedError as exc:
    print(f"403: {exc.message}")

client.close()
buyer.close()
