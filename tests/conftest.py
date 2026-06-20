from __future__ import annotations

import pytest

from onlist import Onlist


@pytest.fixture
def api_key() -> str:
    return "test-key-for-unit-tests"


@pytest.fixture
def client(api_key: str) -> Onlist:
    return Onlist(api_key=api_key)
