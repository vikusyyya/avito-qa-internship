from __future__ import annotations

import allure
import pytest

from src.api_client import (
    extract_created_item_id,
    find_item,
    generate_payload,
    generate_unique_seller_id,
    normalize_items,
    normalize_statistics,
)


@allure.title("Create item with valid payload")
@pytest.mark.smoke
def test_create_item_success(client, response_time_threshold_ms):
    payload = generate_payload()

    with allure.step("Create item"):
        response = client.create_item(payload)

    with allure.step("Check status code"):
        assert response.status_code in (200, 201), response.response.text

    with allure.step("Check response time"):
        assert response.elapsed_ms <= response_time_threshold_ms

    with allure.step("Check content type"):
        assert "application/json" in response.response.headers.get("Content-Type", "")

    with allure.step("Check created id exists"):
        item_id = extract_created_item_id(response.json())
        assert item_id is not None


@allure.title("Create item and get it by id")
@pytest.mark.smoke
@pytest.mark.e2e
def test_create_then_get_by_id(client):
    payload = generate_payload()

    create_response = client.create_item(payload)
    assert create_response.status_code in (200, 201), create_response.response.text
    item_id = extract_created_item_id(create_response.json())

    get_response = client.get_item(item_id)
    assert get_response.status_code == 200, get_response.response.text

    items = normalize_items(get_response.json())
    item = find_item(items, item_id) or items[0]

    assert item.get("sellerId") == payload["sellerId"]
    assert item.get("name") == payload["name"]
    assert item.get("price") == payload["price"]


@allure.title("Create two items and get them by sellerId")
@pytest.mark.smoke
@pytest.mark.e2e
def test_get_items_by_seller_id(client):
    seller_id = generate_unique_seller_id()
    payload_1 = generate_payload(seller_id=seller_id)
    payload_2 = generate_payload(seller_id=seller_id)

    create_1 = client.create_item(payload_1)
    create_2 = client.create_item(payload_2)

    assert create_1.status_code in (200, 201), create_1.response.text
    assert create_2.status_code in (200, 201), create_2.response.text

    item_id_1 = extract_created_item_id(create_1.json())
    item_id_2 = extract_created_item_id(create_2.json())

    seller_response = client.get_items_by_seller(seller_id)
    assert seller_response.status_code == 200, seller_response.response.text

    items = normalize_items(seller_response.json())
    fetched_1 = find_item(items, item_id_1)
    fetched_2 = find_item(items, item_id_2)

    assert fetched_1 is not None, f"Item {item_id_1} not found in seller list"
    assert fetched_2 is not None, f"Item {item_id_2} not found in seller list"


@allure.title("Create item and get statistics by itemId")
@pytest.mark.smoke
@pytest.mark.e2e
def test_get_statistics_by_item_id(client):
    payload = generate_payload()

    create_response = client.create_item(payload)
    assert create_response.status_code in (200, 201), create_response.response.text
    item_id = extract_created_item_id(create_response.json())

    stats_response = client.get_statistics(item_id)
    assert stats_response.status_code == 200, stats_response.response.text

    stats = normalize_statistics(stats_response.json())
    expected_stats = payload["statistics"]

    for key, value in expected_stats.items():
        assert stats.get(key) == value, f"Expected {key}={value}, got {stats.get(key)}"


@allure.title("Repeated POST with same payload should create different ids")
@pytest.mark.e2e
def test_repeated_post_same_payload_creates_new_item(client):
    payload = generate_payload()

    first = client.create_item(payload)
    second = client.create_item(payload)

    assert first.status_code in (200, 201), first.response.text
    assert second.status_code in (200, 201), second.response.text

    first_id = extract_created_item_id(first.json())
    second_id = extract_created_item_id(second.json())

    assert first_id != second_id, "Identical POST requests should create different unique item ids"


@allure.title("Create item without required field should fail")
@pytest.mark.negative
@pytest.mark.parametrize("missing_field", ["sellerId", "name", "price", "statistics"])
def test_create_item_missing_required_field(client, missing_field):
    payload = generate_payload()
    payload.pop(missing_field)

    response = client.create_item(payload)
    assert response.status_code in (400, 422), (
        f"Expected validation error for missing field '{missing_field}', "
        f"got {response.status_code}: {response.response.text}"
    )


@allure.title("Create item with invalid types should fail")
@pytest.mark.negative
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sellerId", "not-an-int"),
        ("sellerId", 12.34),
        ("price", "1000"),
        ("price", 99.99),
        ("statistics", "wrong-type"),
    ],
)
def test_create_item_invalid_types(client, field, value):
    payload = generate_payload()
    payload[field] = value

    response = client.create_item(payload)
    assert response.status_code in (400, 422), (
        f"Expected validation error for field '{field}', got "
        f"{response.status_code}: {response.response.text}"
    )


@allure.title("Get non-existing item by id")
@pytest.mark.negative
def test_get_non_existing_item(client):
    response = client.get_item(9_999_999_999)
    assert response.status_code in (404, 400), response.response.text


@allure.title("Get statistics for non-existing item")
@pytest.mark.negative
def test_get_statistics_for_non_existing_item(client):
    response = client.get_statistics(9_999_999_999)
    assert response.status_code in (404, 400), response.response.text


@allure.title("Boundary sellerId values are accepted")
@pytest.mark.parametrize("seller_id", [111111, 999999])
def test_seller_id_boundaries(client, seller_id):
    payload = generate_payload(seller_id=seller_id)
    response = client.create_item(payload)
    assert response.status_code in (200, 201), response.response.text


@allure.title("Unicode and special symbols in name are handled correctly")
def test_name_with_unicode_and_special_symbols(client):
    payload = generate_payload()
    payload["name"] = "Тестовое объявление №1 / QA ♥ 中文"

    create_response = client.create_item(payload)
    assert create_response.status_code in (200, 201), create_response.response.text

    item_id = extract_created_item_id(create_response.json())
    get_response = client.get_item(item_id)
    assert get_response.status_code == 200, get_response.response.text

    items = normalize_items(get_response.json())
    item = find_item(items, item_id) or items[0]
    assert item.get("name") == payload["name"]


@allure.title("E2E business flow: create -> get by id -> get by seller -> get stats")
@pytest.mark.e2e
@pytest.mark.nonfunctional
def test_full_e2e_flow_and_basic_nonfunctional_checks(client, response_time_threshold_ms):
    payload = generate_payload()

    create_response = client.create_item(payload)
    assert create_response.status_code in (200, 201), create_response.response.text
    assert create_response.elapsed_ms <= response_time_threshold_ms
    assert "application/json" in create_response.response.headers.get("Content-Type", "")

    item_id = extract_created_item_id(create_response.json())

    get_response = client.get_item(item_id)
    assert get_response.status_code == 200, get_response.response.text
    assert get_response.elapsed_ms <= response_time_threshold_ms

    seller_response = client.get_items_by_seller(payload["sellerId"])
    assert seller_response.status_code == 200, seller_response.response.text
    assert seller_response.elapsed_ms <= response_time_threshold_ms

    stats_response = client.get_statistics(item_id)
    assert stats_response.status_code == 200, stats_response.response.text
    assert stats_response.elapsed_ms <= response_time_threshold_ms
