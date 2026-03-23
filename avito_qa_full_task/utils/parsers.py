from __future__ import annotations

import re
from typing import Iterable, List

PRICE_RE = re.compile(r"\d+[\d\s\u00A0]*")


def normalize_space(value: str) -> str:
    return " ".join(value.replace("\u00A0", " ").split())


def parse_price(value: str) -> int:
    normalized = normalize_space(value)
    match = PRICE_RE.search(normalized)
    if not match:
        raise ValueError(f"Could not parse price from: {value!r}")
    digits = re.sub(r"\D", "", match.group(0))
    return int(digits)


def is_non_decreasing(values: Iterable[int]) -> bool:
    vals = list(values)
    return all(left <= right for left, right in zip(vals, vals[1:]))


def is_non_increasing(values: Iterable[int]) -> bool:
    vals = list(values)
    return all(left >= right for left, right in zip(vals, vals[1:]))


def compact_texts(values: Iterable[str]) -> List[str]:
    return [normalize_space(v) for v in values if normalize_space(v)]
