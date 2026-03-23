from __future__ import annotations

import re

import allure
import pytest

from pages.list_page import ListPage
from pages.stats_page import StatsPage
from utils.parsers import is_non_decreasing


@allure.epic("UI moderation platform")
@allure.feature("Desktop list page")
@pytest.mark.desktop
@pytest.mark.smoke
@allure.title("Price range filter returns only items inside the selected range")
def test_price_range_filter(desktop_page, base_url):
    page = ListPage(desktop_page, base_url)
    page.open_list()

    min_price = 1000
    max_price = 100000

    with allure.step(f"Set price range {min_price}-{max_price}"):
        page.set_price_range(min_price, max_price)

    with allure.step("Collect visible item prices"):
        prices = page.visible_prices(limit=12)

    with allure.step("Validate each visible price is within the selected range"):
        assert all(min_price <= price <= max_price for price in prices), (
            f"Found prices outside selected range {min_price}-{max_price}: {prices}"
        )


@allure.epic("UI moderation platform")
@allure.feature("Desktop list page")
@pytest.mark.desktop
@allure.title("Sorting by price orders visible cards in ascending order")
def test_sort_by_price(desktop_page, base_url):
    page = ListPage(desktop_page, base_url)
    page.open_list()

    with allure.step("Apply sorting by price"):
        page.choose_sort_by_price()

    with allure.step("Collect visible prices"):
        prices = page.visible_prices(limit=12)

    with allure.step("Validate ascending sort order"):
        assert is_non_decreasing(prices), f"Prices are not sorted ascending: {prices}"


@allure.epic("UI moderation platform")
@allure.feature("Desktop list page")
@pytest.mark.desktop
@allure.title("Category filter updates the active category state")
def test_category_filter(desktop_page, base_url):
    page = ListPage(desktop_page, base_url)
    page.open_list()

    with allure.step("Select a non-default category"):
        selected_category = page.select_category()

    with allure.step("Check that list still contains results"):
        assert page.card_count() > 0, "Category filter produced empty list unexpectedly"

    with allure.step("Validate category is reflected in UI or URL"):
        active_label = page.current_category_label().lower()
        current_url = desktop_page.url.lower()
        selected_lower = selected_category.lower()
        assert selected_lower in active_label or selected_lower in current_url, (
            f"Selected category '{selected_category}' is not reflected in active UI state or URL. "
            f"Active label: '{active_label}', URL: '{current_url}'"
        )


@allure.epic("UI moderation platform")
@allure.feature("Desktop list page")
@pytest.mark.desktop
@allure.title("Urgent only toggle leaves only urgent items in visible results")
def test_urgent_toggle(desktop_page, base_url):
    page = ListPage(desktop_page, base_url)
    page.open_list()

    with allure.step("Enable urgent only filter"):
        page.toggle_urgent()

    with allure.step("Collect visible card texts"):
        texts = [text.lower() for text in page.cards_text(limit=15)]
        assert texts, "No visible items after enabling urgent filter"

    with allure.step("Validate visible cards are marked as urgent"):
        non_urgent = [text for text in texts if "сроч" not in text and "urgent" not in text]
        assert not non_urgent, (
            "Urgent filter is enabled, but some visible cards do not contain urgent marker. "
            f"Examples: {non_urgent[:3]}"
        )


@allure.epic("UI moderation platform")
@allure.feature("Statistics page")
@pytest.mark.desktop
@pytest.mark.stats
@allure.title("Refresh button updates the statistics container")
def test_stats_refresh_button(desktop_page, base_url):
    page = StatsPage(desktop_page, base_url)
    page.open_stats()

    with allure.step("Capture snapshot before refresh"):
        before = page.stats_snapshot()

    with allure.step("Click refresh"):
        page.click_refresh()

    with allure.step("Capture snapshot after refresh"):
        after = page.stats_snapshot()

    with allure.step("Validate stats page remains populated after refresh"):
        assert after, "Statistics container became empty after refresh"
        assert len(after) >= len(before) * 0.5, "Statistics content shrank unexpectedly after refresh"


@allure.epic("UI moderation platform")
@allure.feature("Statistics page")
@pytest.mark.desktop
@pytest.mark.stats
@allure.title("Stop button pauses timer updates")
def test_stats_stop_timer(desktop_page, base_url):
    page = StatsPage(desktop_page, base_url)
    page.open_stats()

    with allure.step("Read timer and stop it"):
        before = page.timer_value()
        page.stop_timer()

    with allure.step("Wait and read timer again"):
        after = page.wait_and_get_timer(seconds=2.5)

    with allure.step("Validate timer value did not change while stopped"):
        assert after == before, f"Timer changed after stop. Before: {before}, after: {after}"


@allure.epic("UI moderation platform")
@allure.feature("Statistics page")
@pytest.mark.desktop
@pytest.mark.stats
@allure.title("Start button resumes timer updates")
def test_stats_start_timer(desktop_page, base_url):
    page = StatsPage(desktop_page, base_url)
    page.open_stats()

    with allure.step("Stop timer first to put page into known state"):
        page.stop_timer()
        stopped_value = page.wait_and_get_timer(seconds=1.0)

    with allure.step("Start timer"):
        page.start_timer()

    with allure.step("Wait and read timer again"):
        resumed_value = page.wait_and_get_timer(seconds=2.5)

    with allure.step("Validate timer changed after resume"):
        assert resumed_value != stopped_value, (
            f"Timer did not resume after start. Stopped value: {stopped_value}, resumed value: {resumed_value}"
        )


@allure.epic("UI moderation platform")
@allure.feature("Mobile theme")
@pytest.mark.mobile
@allure.title("Mobile theme toggle switches between light and dark theme")
def test_mobile_theme_toggle(mobile_page, base_url):
    page = ListPage(mobile_page, base_url)
    page.open_mobile_home()

    with allure.step("Read initial theme"):
        initial_scheme = page.color_scheme()
        assert initial_scheme in {"light", "dark"}, f"Unexpected initial scheme: {initial_scheme}"

    with allure.step("Toggle theme"):
        page.toggle_theme()

    with allure.step("Read updated theme"):
        updated_scheme = page.color_scheme()

    with allure.step("Validate theme changed"):
        assert updated_scheme in {"light", "dark"}, f"Unexpected updated scheme: {updated_scheme}"
        assert updated_scheme != initial_scheme, (
            f"Theme did not change after toggle. Initial: {initial_scheme}, updated: {updated_scheme}"
        )
