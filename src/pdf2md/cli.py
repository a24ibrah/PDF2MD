"""Command-line interface for PDF2MD."""

import argparse
import sys
from pathlib import Path
from typing import List

from . import __version__
from .converter import PDFToMarkdownConverter


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert lecture slides in PDF format into clean, structured Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf2md lecture.pdf
  pdf2md lecture.pdf -o notes.md
  pdf2md lecture.pdf --format obsidian
  pdf2md lecture.pdf --render-slides --extract-images
  pdf2md lecture.pdf --split -o ./lecture_notes_dir/
  pdf2md lecture.pdf --format marp -o presentation.md
  pdf2md lecture.pdf --ocr
        """,
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="PDF",
        help="One or more PDF presentation files to convert.",
    )

    parser.add_argument(
        "-o", "--output",
        dest="output",
        help="Output Markdown file or directory path.",
    )

    parser.add_argument(
        "-f", "--format",
        dest="format",
        choices=["standard", "marp", "obsidian"],
        default="standard",
        help="Markdown format style: standard (default), marp, or obsidian.",
    )

    parser.add_argument(
        "-s", "--split",
        dest="split",
        action="store_true",
        help="Split slides into individual markdown files in a directory.",
    )

    parser.add_argument(
        "-r", "--render-slides",
        dest="render_slides",
        action="store_true",
        help="Render full slide snapshots (PNG) and embed them in the markdown.",
    )

    parser.add_argument(
        "-i", "--extract-images",
        dest="extract_images",
        action="store_true",
        help="Extract embedded images/diagrams from slides into an images directory.",
    )

    parser.add_argument(
        "--dpi",
        dest="dpi",
        type=int,
        default=150,
        help="DPI resolution for rendered slides (default: 150).",
    )

    parser.add_argument(
        "--ocr",
        dest="use_ocr",
        action="store_true",
        default=True,
        help="Enable OCR fallback for slides without selectable text (default: enabled).",
    )

    parser.add_argument(
        "--no-ocr",
        dest="use_ocr",
        action="store_false",
        help="Disable OCR fallback.",
    )

    parser.add_argument(
        "--force-ocr",
        dest="force_ocr",
        action="store_true",
        help="Force OCR on all slides even if selectable text is present.",
    )

    parser.add_argument(
        "--keep-footers",
        dest="keep_footers",
        action="store_true",
        help="Do not filter out recurring slide footers, course headers, or page numbers.",
    )

    parser.add_argument(
        "--no-notes",
        dest="include_notes",
        action="store_false",
        help="Do not extract presenter notes / PDF annotations.",
    )

    parser.add_argument(
        "--title-prefix",
        dest="title_prefix",
        default="## Slide {page}: {title}",
        help="Custom slide heading format string (default: '## Slide {page}: {title}').",
    )

    parser.add_argument(
        "-q", "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress progress and informational messages.",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def print_progress(page: int, total: int):
    pct = int((page / total) * 100)
    bar_len = 25
    filled = int(bar_len * page // total)
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stdout.write(f"\r  [{bar}] {page}/{total} slides ({pct}%)")
    sys.stdout.flush()
    if page == total:
        sys.stdout.write("\n")


def main(argv: List[str] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    for pdf_input in args.inputs:
        pdf_path = Path(pdf_input)
        if not pdf_path.exists():
            print(f"Error: File not found: {pdf_input}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"\nConverting: {pdf_path.name}")
            print(f"  Format:        {args.format}")
            print(f"  Render slides: {'Yes' if args.render_slides else 'No'}")
            print(f"  Extract images:{'Yes' if args.extract_images else 'No'}")
            print(f"  Split mode:    {'Yes' if args.split else 'No'}")

        progress_cb = None if args.quiet else print_progress

        converter = PDFToMarkdownConverter(
            format_type=args.format,
            render_slides=args.render_slides,
            extract_images=args.extract_images,
            split_slides=args.split,
            use_ocr=args.use_ocr,
            force_ocr=args.force_ocr,
            keep_footers=args.keep_footers,
            include_notes=args.include_notes,
            dpi=args.dpi,
            title_prefix=args.title_prefix,
            progress_callback=progress_cb,
        )

        try:
            stats = converter.convert(str(pdf_path), output_path=args.output)
            if not args.quiet:
                print("Conversion complete!")
                print(f"  Slides processed: {stats['total_slides']}")
                if stats['tables_extracted'] > 0:
                    print(f"  Tables extracted: {stats['tables_extracted']}")
                if stats['images_extracted'] > 0:
                    print(f"  Images extracted: {stats['images_extracted']}")
                if stats['slides_rendered'] > 0:
                    print(f"  Slide snapshots:  {stats['slides_rendered']}")
                if stats['ocr_slides'] > 0:
                    print(f"  OCR slides:       {stats['ocr_slides']}")
                print(f"  Saved to:         {stats['primary_output']}\n")
        except Exception as e:
            print(f"\nError converting {pdf_input}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
