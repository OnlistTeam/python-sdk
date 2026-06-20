"""Streaming chat completion."""

from onlist import Onlist

client = Onlist()

stream = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Write a haiku about API marketplaces."}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)

print()  # newline after stream
