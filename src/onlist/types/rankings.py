from __future__ import annotations

from pydantic import BaseModel, Field


class ModelRankingEntry(BaseModel):
    """A single entry in the model usage leaderboard."""

    rank: int
    model_name: str
    author: str | None = None
    author_icon: str | None = None
    total_tokens: str = "0"
    total_requests: int = 0
    growth_pct: float | None = None

    model_config = {"extra": "allow"}


class ChartPoint(BaseModel):
    """A single data point in the usage chart (VChart long format)."""

    bucket: str
    value: int = 0
    type: str = ""

    model_config = {"extra": "allow"}


class ModelRankingsResponse(BaseModel):
    """Response from ``marketplace.rankings.models()``."""

    leaderboard: list[ModelRankingEntry] = Field(default_factory=list)
    series: list[ChartPoint] = Field(default_factory=list)
    top_models: list[str] = Field(default_factory=list)
    sort: str | None = None
    window: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    model_config = {"extra": "allow"}


class AppEntry(BaseModel):
    """A single app in the app rankings."""

    app_id: int | None = None
    url_key: str | None = None
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    domain: str | None = None
    icon_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    rank: int = 0
    total_requests: int = 0
    total_tokens: str = "0"
    growth_pct: float | None = None

    model_config = {"extra": "allow"}


class AppListResponse(BaseModel):
    """Response from ``marketplace.rankings.apps()``."""

    apps: list[AppEntry] = Field(default_factory=list)
    page: int | None = None
    limit: int | None = None
    has_more: bool = False
    sort: str | None = None
    window: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    model_config = {"extra": "allow"}
