from __future__ import annotations

import os

import pytest

from src.api_client import AvitoApiClient


@pytest.fixture(scope="session")
def response_time_threshold_ms() -> int:
    return int(os.getenv("AVITO_RESPONSE_TIME_MS", "2000"))


@pytest.fixture()
def client() -> AvitoApiClient:
    return AvitoApiClient()
