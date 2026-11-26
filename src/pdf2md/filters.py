"""Filters for detecting and removing repeated slide headers, footers, and page numbers."""

import re
from collections import Counter
from typing import Set


PAGE_NUM_PATTERNS = [
    re.compile(r"^\s*(?:page|slide)?\s*\d+\s*(?:[/|of]\s*\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\[\s*\d+\s*\]\s*$"),
    re.compile(r"^\s*\d+\s*$"),
]


def is_page_number_string(text: str) -> bool:
    """Check if a string is solely a page or slide counter."""
    stripped = text.strip()
    return any(p.match(stripped) for p in PAGE_NUM_PATTERNS)


def detect_repeated_headers_and_footers(
    doc,
    top_margin_pct: float = 0.10,
    bottom_margin_pct: float = 0.12,
    min_repeat_ratio: float = 0.35,
) -> Set[str]:
    """
    Detect repeated header or footer text across multiple slides.
    Returns a set of normalized string texts to ignore during body extraction.
    """
    total_pages = len(doc)
    if total_pages <= 2:
        return set()

    header_counter = Counter()
    footer_counter = Counter()

    for page_idx in range(total_pages):
        page = doc[page_idx]
        rect = page.rect
        height = rect.height

        top_limit = height * top_margin_pct
        bottom_limit = height * (1.0 - bottom_margin_pct)

        blocks = page.get_text("blocks")
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if len(b) < 5 or b[4] is None:
                continue
            text = b[4].strip()
            if not text:
                continue

            y0, y1 = b[1], b[3]

            # Normalize both full block text and individual lines for counting
            lines_in_block = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines_in_block:
                norm_line = re.sub(r"\s+", " ", line).strip().lower()
                if y1 <= top_limit:
                    header_counter[norm_line] += 1
                elif y0 >= bottom_limit:
                    footer_counter[norm_line] += 1

            if len(lines_in_block) > 1:
                norm_full = re.sub(r"\s+", " ", text).strip().lower()
                if y1 <= top_limit:
                    header_counter[norm_full] += 1
                elif y0 >= bottom_limit:
                    footer_counter[norm_full] += 1

    threshold = max(2, int(total_pages * min_repeat_ratio))
    repeated = set()

    for text, count in header_counter.items():
        if count >= threshold and len(text) < 100:
            repeated.add(text)

    for text, count in footer_counter.items():
        if count >= threshold and len(text) < 100:
            repeated.add(text)

    return repeated
