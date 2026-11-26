"""Parser for extracting structured content from individual lecture slides."""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set, Dict, Any

from .filters import is_page_number_string
from .tables import extract_tables_from_page
from .images import extract_embedded_images, render_slide_image
from .ocr import ocr_page

BULLET_REGEX = re.compile(r"^[\s\u2022\u25cf\u25cb\u25aa\u25ab\u2013\u2014\*\+\›\▸\►\■\❑\➢\-]\s*")
NUMBERED_LIST_REGEX = re.compile(r"^\s*(\d+[\.\)]|\([a-zA-Z0-9]+\)|[a-zA-Z][\.\)])\s+")

MONOSPACE_FONTS = {
    "courier", "cour", "consolas", "monaco", "menlo", "source code", "fira code",
    "dejavu sans mono", "ubuntu mono", "roboto mono", "jetbrains", "monospace"
}


@dataclass
class SlideContent:
    page_number: int
    title: Optional[str] = None
    slide_image_path: Optional[str] = None
    body_elements: List[str] = field(default_factory=list)
    embedded_images: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    presenter_notes: List[str] = field(default_factory=list)
    is_ocr: bool = False


def is_monospace(font_name: str) -> bool:
    """Check if font name indicates a monospace / code font."""
    fn = (font_name or "").lower()
    return any(mono in fn for mono in MONOSPACE_FONTS)


def bboxes_intersect(bbox1: Tuple[float, float, float, float], bbox2: Tuple[float, float, float, float]) -> bool:
    """Check if two bounding boxes overlap significantly."""
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2
    return not (x1_1 <= x0_2 or x1_2 <= x0_1 or y1_1 <= y0_2 or y1_2 <= y0_1)


def parse_slide(
    page,
    page_number: int,
    output_dir: str,
    repeated_headers_footers: Set[str],
    seen_image_hashes: Set[str],
    render_slides: bool = False,
    extract_images: bool = False,
    use_ocr_fallback: bool = True,
    force_ocr: bool = False,
    keep_footers: bool = False,
    include_notes: bool = True,
    dpi: int = 150,
) -> SlideContent:
    """
    Parse a single slide page into structured SlideContent.
    """
    content = SlideContent(page_number=page_number)
    rect = page.rect
    page_width, page_height = rect.width, rect.height

    # 1. Render full slide screenshot if requested
    if render_slides:
        img_rel_path = render_slide_image(page, page_number, output_dir, dpi=dpi)
        content.slide_image_path = img_rel_path

    # 2. Extract embedded images if requested
    if extract_images:
        images = extract_embedded_images(page, page_number, output_dir, seen_image_hashes)
        for _, img_path in images:
            content.embedded_images.append(img_path)

    # 3. Extract tables
    tables = extract_tables_from_page(page)
    table_bboxes = [bbox for bbox, _ in tables]
    for _, table_md in tables:
        content.tables.append(table_md)

    # 4. Extract annotations / speaker notes
    if include_notes:
        annots = page.annots()
        if annots:
            for annot in annots:
                info = annot.info
                text = (info.get("content") or "").strip()
                if text:
                    content.presenter_notes.append(text)

    # 5. Extract Text Blocks & Layout
    page_dict = page.get_text("dict")
    raw_blocks = page_dict.get("blocks", [])

    # Filter out image blocks and blocks intersecting tables
    text_blocks = []
    total_text_length = 0

    for b in raw_blocks:
        if b.get("type") != 0:  # 0 is text
            continue
        bbox = tuple(b.get("bbox", (0, 0, 0, 0)))

        # Skip if within a detected table
        if any(bboxes_intersect(bbox, t_bbox) for t_bbox in table_bboxes):
            continue

        lines = b.get("lines", [])
        block_text = ""
        max_font_size = 0.0
        is_code_block = True
        span_count = 0

        for l in lines:
            line_text = ""
            for s in l.get("spans", []):
                stext = s.get("text", "")
                line_text += stext
                ssize = s.get("size", 0.0)
                if ssize > max_font_size:
                    max_font_size = ssize
                if not is_monospace(s.get("font", "")):
                    is_code_block = False
                span_count += 1
            block_text += line_text + "\n"

        block_text = block_text.strip()
        if not block_text:
            continue

        # Check for repeated header/footer
        norm_btext = re.sub(r"\s+", " ", block_text).strip().lower()
        if not keep_footers:
            if is_page_number_string(block_text):
                continue
            if norm_btext in repeated_headers_footers:
                continue

        total_text_length += len(block_text)
        text_blocks.append({
            "bbox": bbox,
            "text": block_text,
            "max_font_size": max_font_size,
            "is_code": is_code_block and span_count > 0,
            "raw_block": b,
        })

    # OCR Fallback if text is empty or sparse, or forced
    if force_ocr or (use_ocr_fallback and total_text_length < 20):
        ocr_text = ocr_page(page)
        if ocr_text:
            content.is_ocr = True
            lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
            if lines:
                content.title = lines[0]
                for line in lines[1:]:
                    if BULLET_REGEX.match(line):
                        clean_line = BULLET_REGEX.sub("", line).strip()
                        content.body_elements.append(f"- {clean_line}")
                    else:
                        content.body_elements.append(f"- {line}")
            return content

    if not text_blocks:
        return content

    # 6. Slide Title Detection
    # Titles are typically in the top 35% of the slide and have larger font size
    top_threshold_y = page_height * 0.35
    top_blocks = [b for b in text_blocks if b["bbox"][1] <= top_threshold_y]

    title_block = None
    if top_blocks:
        # Find block with largest font size
        max_size = max(b["max_font_size"] for b in top_blocks)
        # Average font size across all blocks
        all_sizes = [b["max_font_size"] for b in text_blocks]
        avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 12.0

        candidates = [b for b in top_blocks if b["max_font_size"] == max_size]
        # Sort candidates by y0 (topmost first)
        candidates.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

        top_candidate = candidates[0]
        # Title is valid if it's prominently larger or topmost in top 25%
        if top_candidate["max_font_size"] >= avg_size + 1.5 or top_candidate["bbox"][1] <= page_height * 0.20:
            title_block = top_candidate
            raw_title = title_block["text"].replace("\n", " ")
            # Clean title
            raw_title = re.sub(r"\s+", " ", raw_title).strip()
            content.title = raw_title

    # Remaining blocks for body
    body_blocks = [b for b in text_blocks if b is not title_block]

    if not body_blocks:
        return content

    # 7. Multi-column Layout Detection
    # Determine if body blocks are arranged in 2 columns
    left_col = []
    right_col = []
    mid_x = page_width * 0.5
    has_two_cols = False

    # Check if there are distinct left and right column clusters
    col_split_x = mid_x
    left_blocks = [b for b in body_blocks if b["bbox"][2] <= col_split_x + 30]
    right_blocks = [b for b in body_blocks if b["bbox"][0] >= col_split_x - 30]

    if len(left_blocks) >= 1 and len(right_blocks) >= 1 and (len(left_blocks) + len(right_blocks) >= len(body_blocks) * 0.8):
        # Good candidate for multi-column layout
        left_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
        right_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
        ordered_blocks = left_blocks + right_blocks
    else:
        # Single column or top-down flow: sort by y0, then x0
        ordered_blocks = sorted(body_blocks, key=lambda b: (b["bbox"][1], b["bbox"][0]))

    # 8. Process Body Blocks (Bullets, Indents, Code, Math)
    base_x0 = min((b["bbox"][0] for b in body_blocks), default=0.0)

    for block in ordered_blocks:
        if block.get("is_code"):
            code_text = block["text"]
            content.body_elements.append(f"```text\n{code_text}\n```")
            continue

        raw_block = block.get("raw_block", {})
        lines = raw_block.get("lines", [])

        # Process line by line within block
        for line in lines:
            spans = line.get("spans", [])
            line_str = "".join(s.get("text", "") for s in spans).strip()
            if not line_str:
                continue

            # Check if line itself is a repeated footer or page number
            if not keep_footers and is_page_number_string(line_str):
                continue

            line_x0 = line.get("bbox", (0, 0, 0, 0))[0]
            indent_delta = max(0.0, line_x0 - base_x0)

            # Determine markdown bullet indentation
            if indent_delta < 20:
                indent = ""
            elif indent_delta < 45:
                indent = "  "
            else:
                indent = "    "

            # Check if line already has a bullet or number
            if BULLET_REGEX.match(line_str):
                cleaned = BULLET_REGEX.sub("", line_str).strip()
                content.body_elements.append(f"{indent}- {cleaned}")
            elif NUMBERED_LIST_REGEX.match(line_str):
                content.body_elements.append(f"{indent}{line_str}")
            else:
                # If short or standard slide line, format as bullet
                content.body_elements.append(f"{indent}- {line_str}")

    return content
