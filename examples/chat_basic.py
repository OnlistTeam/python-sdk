"""Basic chat completion with Onlist."""

from onlist import Onlist

client = Onlist()  # reads ONLIST_API_KEY from environment

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Explain what Onlist is in one sentence."}],
)

print(response.choices[0].message.content)
