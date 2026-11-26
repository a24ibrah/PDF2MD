"""Core PDF to Markdown conversion engine for lecture slides."""

import os
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
import pymupdf

from .filters import detect_repeated_headers_and_footers
from .slide_parser import parse_slide, SlideContent
from .formatters import format_document, write_split_slides


class PDFToMarkdownConverter:
    """Configurable converter that transforms PDF lecture slides into clean Markdown."""

    def __init__(
        self,
        format_type: str = "standard",
        render_slides: bool = False,
        extract_images: bool = False,
        split_slides: bool = False,
        use_ocr: bool = True,
        force_ocr: bool = False,
        keep_footers: bool = False,
        include_notes: bool = True,
        dpi: int = 150,
        title_prefix: str = "## Slide {page}: {title}",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        self.format_type = format_type.lower()
        self.render_slides = render_slides
        self.extract_images = extract_images
        self.split_slides = split_slides
        self.use_ocr = use_ocr
        self.force_ocr = force_ocr
        self.keep_footers = keep_footers
        self.include_notes = include_notes
        self.dpi = dpi
        self.title_prefix = title_prefix
        self.progress_callback = progress_callback

    def convert(self, pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a PDF presentation into Markdown.
        Returns a dict with paths and summary metrics.
        """
        pdf_file = Path(pdf_path).resolve()
        if not pdf_file.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = pymupdf.open(str(pdf_file))
        total_pages = len(doc)
        if total_pages == 0:
            doc.close()
            raise ValueError(f"PDF contains no pages: {pdf_path}")

        # Determine output directory and main markdown file path
        if output_path:
            out_target = Path(output_path).resolve()
            if self.split_slides or out_target.is_dir() or (not out_target.suffix and not out_target.exists()):
                output_dir = out_target
                md_filepath = output_dir / f"{pdf_file.stem}.md"
            else:
                output_dir = out_target.parent
                md_filepath = out_target
        else:
            output_dir = pdf_file.parent
            md_filepath = output_dir / f"{pdf_file.stem}.md"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Detect repeated headers/footers
        repeated_text = set()
        if not self.keep_footers:
            repeated_text = detect_repeated_headers_and_footers(doc)

        seen_image_hashes = set()
        slides: List[SlideContent] = []

        # Document Title deduction (from PDF metadata or first slide)
        meta_title = doc.metadata.get("title", "").strip()
        doc_title = meta_title if meta_title else pdf_file.stem.replace("_", " ").title()

        # Parse each slide
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            if self.progress_callback:
                self.progress_callback(page_num, total_pages)

            page = doc[page_idx]
            slide_content = parse_slide(
                page=page,
                page_number=page_num,
                output_dir=str(output_dir),
                repeated_headers_footers=repeated_text,
                seen_image_hashes=seen_image_hashes,
                render_slides=self.render_slides,
                extract_images=self.extract_images,
                use_ocr_fallback=self.use_ocr,
                force_ocr=self.force_ocr,
                keep_footers=self.keep_footers,
                include_notes=self.include_notes,
                dpi=self.dpi,
            )
            slides.append(slide_content)

        # If first slide has a strong title and doc_title was just filename, use first slide's title
        if slides and slides[0].title and (not meta_title):
            doc_title = slides[0].title

        # Write output markdown
        created_files = []
        if self.split_slides:
            created_files = write_split_slides(
                slides=slides,
                doc_title=doc_title,
                output_dir=str(output_dir),
                format_type=self.format_type,
                title_prefix=self.title_prefix,
            )
        else:
            full_md = format_document(
                slides=slides,
                doc_title=doc_title,
                format_type=self.format_type,
                title_prefix=self.title_prefix,
            )
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(full_md)
            created_files.append(str(md_filepath))

        doc.close()

        total_tables = sum(len(s.tables) for s in slides)
        total_images = sum(len(s.embedded_images) for s in slides)
        rendered_slides_count = sum(1 for s in slides if s.slide_image_path)
        ocr_slides_count = sum(1 for s in slides if s.is_ocr)

        return {
            "title": doc_title,
            "total_slides": total_pages,
            "output_files": created_files,
            "primary_output": str(md_filepath) if not self.split_slides else str(output_dir / "README.md"),
            "tables_extracted": total_tables,
            "images_extracted": total_images,
            "slides_rendered": rendered_slides_count,
            "ocr_slides": ocr_slides_count,
        }


def convert_pdf(pdf_path: str, output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Convenience functional wrapper for PDFToMarkdownConverter."""
    converter = PDFToMarkdownConverter(**kwargs)
    return converter.convert(pdf_path, output_path)
