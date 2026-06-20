from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Provider(BaseModel):
    id: int | None = None
    slug: str
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    listing_count: int | None = None
    follower_count: int | None = None
    weighted_score: float | None = None
    sample_count: int | None = None
    max_rpm: int | None = None
    availability_7d: float | None = None

    @property
    def score(self) -> float | None:
        return self.weighted_score

    @property
    def model_count(self) -> int | None:
        return self.listing_count

    model_config = {"extra": "allow"}


class ProviderDetail(BaseModel):
    id: int | None = None
    slug: str
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    listing_count: int | None = None
    follower_count: int | None = None
    weighted_score: float | None = None
    max_rpm: int | None = None
    availability_7d: float | None = None
    listings: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def score(self) -> float | None:
        return self.weighted_score

    @property
    def model_count(self) -> int | None:
        return self.listing_count

    model_config = {"extra": "allow"}


class ProviderListResponse(BaseModel):
    """Response from ``marketplace.providers.list()``."""

    items: list[Provider] = Field(default_factory=list)

    @property
    def data(self) -> list[Provider]:
        return self.items

    @property
    def total(self) -> int:
        return len(self.items)

    model_config = {"extra": "allow"}
