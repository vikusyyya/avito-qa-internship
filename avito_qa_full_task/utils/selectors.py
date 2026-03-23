CARD_CANDIDATES = [
    "[data-testid='item-card']",
    "[data-marker='item']",
    "[data-marker='catalog-serp'] [data-marker='item']",
    "article",
    "[class*='item']",
]

PRICE_CANDIDATES = [
    "[data-testid='item-price']",
    "[data-marker='item-price']",
    "[class*='price']",
    "text=/₽|руб/i",
]

CATEGORY_FILTER_CANDIDATES = [
    "select[name='category']",
    "[data-testid='category-filter']",
    "[data-marker='category-filter']",
]

URGENT_TOGGLE_CANDIDATES = [
    "[data-testid='urgent-toggle']",
    "[data-marker='urgent-toggle']",
    "input[type='checkbox'][name*='urgent' i]",
]

THEME_TOGGLE_CANDIDATES = [
    "[data-testid='theme-toggle']",
    "[data-marker='theme-toggle']",
    "button[aria-label*='theme' i]",
    "button[aria-label*='тема' i]",
]
