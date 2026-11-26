"""Markdown formatters for presentation slides (Standard, Marp, Obsidian, Split)."""

import os
from datetime import datetime
from typing import List, Optional
from .slide_parser import SlideContent


def format_single_slide(
    slide: SlideContent,
    format_type: str = "standard",
    title_prefix: str = "## Slide {page}: {title}",
    include_image_embeds: bool = True,
) -> str:
    """Format a single SlideContent object into Markdown."""
    lines = []

    # Slide Header
    raw_title = slide.title or f"Slide {slide.page_number}"
    header_text = title_prefix.format(page=slide.page_number, title=raw_title)
    lines.append(header_text)
    lines.append("")

    # Full visual slide snapshot if rendered
    if slide.slide_image_path and include_image_embeds:
        lines.append(f"![Slide {slide.page_number}]({slide.slide_image_path})")
        lines.append("")

    # Body elements (bullet points, code blocks)
    if slide.body_elements:
        lines.extend(slide.body_elements)
        lines.append("")

    # Tables
    if slide.tables:
        for tbl in slide.tables:
            lines.append(tbl)
            lines.append("")

    # Extracted embedded images
    if slide.embedded_images and include_image_embeds:
        for idx, img_path in enumerate(slide.embedded_images, start=1):
            lines.append(f"![Slide {slide.page_number} Figure {idx}]({img_path})")
        lines.append("")

    # Presenter Notes / Annotations
    if slide.presenter_notes:
        if format_type == "obsidian":
            lines.append("> [!note] Presenter Notes")
            for note in slide.presenter_notes:
                for nline in note.splitlines():
                    lines.append(f"> {nline}")
        else:
            lines.append("> **Presenter Notes:**")
            for note in slide.presenter_notes:
                for nline in note.splitlines():
                    lines.append(f"> {nline}")
        lines.append("")

    return "\n".join(lines).strip()


def format_document(
    slides: List[SlideContent],
    doc_title: str,
    format_type: str = "standard",
    title_prefix: str = "## Slide {page}: {title}",
) -> str:
    """Assemble all slides into a single continuous Markdown document."""
    parts = []

    if format_type == "marp":
        parts.append("---\nmarp: true\ntheme: default\npaginate: true\n---")
    elif format_type == "obsidian":
        today = datetime.now().strftime("%Y-%m-%d")
        frontmatter = [
            "---",
            f"title: \"{doc_title}\"",
            f"date: {today}",
            f"total_slides: {len(slides)}",
            "tags:",
            "  - lecture-notes",
            "  - slides",
            "---",
        ]
        parts.append("\n".join(frontmatter))
        parts.append(f"# {doc_title}\n")
    else:
        parts.append(f"# {doc_title}\n")

    for idx, slide in enumerate(slides):
        slide_md = format_single_slide(slide, format_type=format_type, title_prefix=title_prefix)
        parts.append(slide_md)

    # In Marp, slides are separated by '---'
    # In standard/obsidian, '---' acts as visual divider
    return "\n\n---\n\n".join(parts) + "\n"


def write_split_slides(
    slides: List[SlideContent],
    doc_title: str,
    output_dir: str,
    format_type: str = "standard",
    title_prefix: str = "## Slide {page}: {title}",
) -> List[str]:
    """Write individual slide files and an index README.md."""
    slides_dir = os.path.join(output_dir, "slides_md")
    os.makedirs(slides_dir, exist_ok=True)

    created_files = []
    toc_lines = [f"# {doc_title}\n", "## Table of Contents\n"]

    for slide in slides:
        filename = f"slide_{slide.page_number:03d}.md"
        filepath = os.path.join(slides_dir, filename)

        slide_title = slide.title or f"Slide {slide.page_number}"
        toc_lines.append(f"- [Slide {slide.page_number}: {slide_title}](slides_md/{filename})")

        slide_md = format_single_slide(slide, format_type=format_type, title_prefix=title_prefix)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(slide_md + "\n")

        created_files.append(filepath)

    index_path = os.path.join(output_dir, "README.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(toc_lines) + "\n")
    created_files.append(index_path)

    return created_files
