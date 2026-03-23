from __future__ import annotations

import os
import random
import string
import time
from dataclasses import dataclass
from typing import Any, Iterable

import requests


DEFAULT_BASE_URL = os.getenv("AVITO_BASE_URL", "https://qa-internship.avito.com").rstrip("/")
DEFAULT_TIMEOUT = float(os.getenv("AVITO_TIMEOUT", "10"))


class ApiResolutionError(RuntimeError):
    """Raised when none of the candidate routes works."""


@dataclass
class ApiResponse:
    response: requests.Response
    elapsed_ms: float

    @property
    def status_code(self) -> int:
        return self.response.status_code

    def json(self) -> Any:
        return self.response.json()


class AvitoApiClient:
    """
    Client with route fallbacks.

    The task statement defines business operations, but the exact collection is not
    available from this environment. To keep the solution practical, the client tries
    a small set of likely endpoint variants for read operations.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        url = f"{self.base_url}{path}"
        started = time.perf_counter()
        response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return ApiResponse(response=response, elapsed_ms=elapsed_ms)

    def _first_success(self, method: str, paths: Iterable[str], **kwargs: Any) -> ApiResponse:
        attempts: list[tuple[str, int]] = []
        last_response: ApiResponse | None = None
        for path in paths:
            result = self._request(method, path, **kwargs)
            attempts.append((path, result.status_code))
            last_response = result
            if result.status_code < 500 and result.status_code != 404:
                return result
        if last_response is None:
            raise ApiResolutionError("No candidate routes were provided")
        tried = ", ".join(f"{path} -> {status}" for path, status in attempts)
        raise ApiResolutionError(f"No candidate route resolved successfully. Attempts: {tried}")

    def create_item(self, payload: dict[str, Any]) -> ApiResponse:
        # Most likely from past Avito internship tasks.
        return self._request("POST", "/api/1/item", json=payload)

    def get_item(self, item_id: int | str) -> ApiResponse:
        return self._first_success(
            "GET",
            [
                f"/api/1/item/{item_id}",
                f"/api/1/{item_id}/item",
                f"/api/1/items/{item_id}",
            ],
        )

    def get_items_by_seller(self, seller_id: int | str) -> ApiResponse:
        return self._first_success(
            "GET",
            [
                f"/api/1/{seller_id}/item",
                f"/api/1/item?sellerId={seller_id}",
                f"/api/1/items?sellerId={seller_id}",
                f"/api/1/seller/{seller_id}/item",
            ],
        )

    def get_statistics(self, item_id: int | str) -> ApiResponse:
        return self._first_success(
            "GET",
            [
                f"/api/1/statistic/{item_id}",
                f"/api/1/statistics/{item_id}",
                f"/api/1/item/{item_id}/statistic",
                f"/api/1/item/{item_id}/statistics",
            ],
        )


def generate_unique_seller_id() -> int:
    return random.randint(111111, 999999)


def generate_payload(seller_id: int | None = None) -> dict[str, Any]:
    if seller_id is None:
        seller_id = generate_unique_seller_id()
    suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return {
        "sellerId": seller_id,
        "name": f"QA item {suffix}",
        "price": random.randint(1, 999_999),
        "statistics": {
            "likes": random.randint(0, 100),
            "viewCount": random.randint(0, 1000),
            "contacts": random.randint(0, 100),
        },
    }


def extract_created_item_id(body: Any) -> Any:
    if isinstance(body, dict):
        for key in ("id", "itemId"):
            if key in body:
                return body[key]
    if isinstance(body, list) and body:
        first = body[0]
        if isinstance(first, dict):
            for key in ("id", "itemId"):
                if key in first:
                    return first[key]
    raise AssertionError(f"Could not extract item id from response body: {body!r}")


def normalize_items(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if isinstance(body, dict):
        for key in ("items", "result", "data"):
            value = body.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [body]
    raise AssertionError(f"Unexpected items payload: {body!r}")


def find_item(items: list[dict[str, Any]], item_id: Any) -> dict[str, Any] | None:
    for item in items:
        if item.get("id") == item_id or item.get("itemId") == item_id:
            return item
    return None


def normalize_statistics(body: Any) -> dict[str, Any]:
    if isinstance(body, dict):
        for key in ("statistics", "result", "data"):
            value = body.get(key)
            if isinstance(value, dict):
                return value
        return body
    raise AssertionError(f"Unexpected statistics payload: {body!r}")
