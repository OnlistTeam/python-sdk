"""Async client usage."""

import asyncio

from onlist import AsyncOnlist


async def main() -> None:
    client = AsyncOnlist()

    response = await client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Say hello in Japanese."}],
    )
    print(response.choices[0].message.content)

    # Marketplace queries also work async
    models = await client.marketplace.models.list(limit=3)
    for m in models.data:
        print(f"  {m.id}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
