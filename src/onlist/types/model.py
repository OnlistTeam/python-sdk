from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Pricing(BaseModel):
    prompt: str = "0"
    completion: str = "0"
    request: str | None = None


class Architecture(BaseModel):
    modality: str | None = None
    input_modalities: list[str] | None = None
    output_modalities: list[str] | None = None
    tokenizer: str | None = None


class TopProvider(BaseModel):
    context_length: int | None = None
    max_completion_tokens: int | None = None
    is_moderated: bool | None = None


class Model(BaseModel):
    id: str
    name: str | None = None
    author: str | None = None
    owned_by: str | None = None
    canonical_slug: str | None = None
    created: int | None = None
    description: str | None = None
    context_length: int | None = None
    max_output_length: int | None = None
    architecture: Architecture | None = None
    pricing: Pricing | None = None
    supported_parameters: list[str] | None = None
    quantization: str | None = None
    top_provider: TopProvider | None = None
    is_ready: bool | None = None

    model_config = {"extra": "allow"}


class ProviderOffer(BaseModel):
    listing_id: int | None = None
    provider_id: int | None = None
    slug: str | None = None
    name: str | None = None
    logo_url: str | None = None
    score: float | None = None
    price_input_usd: str | None = None
    price_output_usd: str | None = None
    availability_7d: float | None = None

    model_config = {"extra": "allow"}


class ModelDetail(BaseModel):
    id: str
    name: str | None = None
    author: str | None = None
    owned_by: str | None = None
    context_length: int | None = None
    max_output_length: int | None = None
    architecture: Architecture | None = None
    pricing: Pricing | None = None
    description: str | None = None
    providers: list[ProviderOffer] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class ModelListResponse(BaseModel):
    """Response from ``marketplace.models.list()``."""

    data: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
    offset: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
