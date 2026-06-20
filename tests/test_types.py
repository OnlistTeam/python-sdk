from __future__ import annotations

from onlist.types.routing import MaxPrice, ProviderRouting


class TestProviderRouting:
    def test_minimal(self) -> None:
        r = ProviderRouting(only=["alice"])
        d = r.model_dump(exclude_none=True)
        assert d == {"only": ["alice"]}

    def test_full(self) -> None:
        r = ProviderRouting(
            only=["alice"],
            sort="price",
            allow=["alice", "bob"],
            ignore=["charlie"],
            allow_fallbacks=True,
            max_price=MaxPrice(prompt=0.000003, completion=0.000015),
        )
        d = r.model_dump(exclude_none=True)
        assert d["sort"] == "price"
        assert d["allow_fallbacks"] is True
        assert d["max_price"]["prompt"] == 0.000003

    def test_empty_dumps_nothing(self) -> None:
        r = ProviderRouting()
        d = r.model_dump(exclude_none=True)
        assert d == {}
