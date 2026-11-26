# PDF2MD — Lecture Slides PDF to Markdown Converter

A dedicated CLI tool to convert university and presentation lecture slides in PDF format into clean, organized, and structured Markdown (`.md`).

Unlike generic document converters, **PDF2MD** is tailored specifically for the quirks of presentation decks:
- **Slide Title Detection**: Automatically identifies slide headings based on font prominence and geometry.
- **Hierarchical Bullet Points**: Normalizes nested bullet points, sub-items, and numbered lists.
- **Multi-Column Preservation**: Distinguishes side-by-side columns (e.g. Pros vs. Cons) to prevent awkward interleaved reading order.
- **Header & Footer Cleanup**: Detects and filters recurring boilerplate (course codes, date, slide numbers, professor name, copyright) across slides.
- **Code Block Formatting**: Detects monospace code snippets and wraps them in syntax blocks.
- **Table Extraction**: Extracts structured tables into clean GitHub-flavored Markdown tables.
- **Slide Visual Snapshots (`-r, --render-slides`)**: Renders high-res slide images and embeds them inline with notes.
- **Deduplicated Image Extraction (`-i, --extract-images`)**: Extracts diagrams and figures while filtering out repeated institution logos.
- **Presenter Notes & Annotations**: Extracts PDF popup notes and annotations.
- **Multiple Output Formats**: Supports Standard GitHub Markdown, [Marp](https://marp.app) presentation decks, and [Obsidian](https://obsidian.md) vaults.
- **Split Slide Mode (`-s, --split`)**: Generates an individual `.md` file for every slide plus a table-of-contents `README.md`.
- **OCR Fallback**: Automatically invokes Tesseract OCR for scanned or image-based slides.

---

## Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Clone or navigate to the directory
cd PDF2MD

# Run directly without installation
uv run pdf2md --help

# Or install in editable mode
uv pip install -e .
```

Using standard `pip`:

```bash
pip install -e .
```

---

## Quick Start

### 1. Basic Conversion

Convert a lecture PDF into a single structured Markdown file:

```bash
pdf2md lecture01.pdf
# Generates lecture01.md
```

Specify a custom output path:

```bash
pdf2md lecture01.pdf -o ./notes/week1.md
```

### 2. Embed Visual Slide Images (Ideal for Note-Taking & Obsidian)

Renders high-resolution images of each slide and links them right above the extracted text:

```bash
pdf2md lecture01.pdf -r --format obsidian -o ./obsidian_vault/lecture01.md
```

### 3. Extract Embedded Figures & Diagrams

Extracts embedded images to an `images/` folder and links them inline:

```bash
pdf2md lecture01.pdf -i
```

### 4. Split Slides into Separate Files

Creates `slides_md/slide_001.md`, `slide_002.md`, ..., and an index `README.md`:

```bash
pdf2md lecture01.pdf --split -o ./lecture_deck/
```

### 5. Convert to Marp Presentation Deck

Export to Marp-compatible Markdown for editing and re-presenting:

```bash
pdf2md lecture01.pdf --format marp -o slides.md
```

### 6. OCR Scanned or Flattened Slides

If slides were exported as full-page bitmap images without selectable text:

```bash
pdf2md scanned_slides.pdf --ocr
```

---

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `PDF [PDF ...]` | Input PDF file(s) (supports batch processing) | *Required* |
| `-o, --output` | Output `.md` file path or directory | `<input_stem>.md` |
| `-f, --format` | Output format style: `standard`, `marp`, `obsidian` | `standard` |
| `-s, --split` | Split slides into separate `.md` files in a folder | `False` |
| `-r, --render-slides`| Render full visual slide images and embed in Markdown | `False` |
| `-i, --extract-images`| Extract embedded diagrams/images into an images folder | `False` |
| `--dpi` | DPI resolution for rendered slide images | `150` |
| `--ocr` / `--no-ocr` | Enable/disable OCR fallback for text-less slides | `True` |
| `--force-ocr` | Force OCR on all slides even if text is selectable | `False` |
| `--keep-footers` | Keep recurring slide footers, course tags & page numbers | `False` |
| `--no-notes` | Skip extracting PDF annotations / presenter notes | `False` |
| `--title-prefix` | Template for slide headers (e.g. `## Slide {page}: {title}`) | `## Slide {page}: {title}` |
| `-q, --quiet` | Suppress console progress bar and stats | `False` |
| `-v, --version` | Display version | |

---

## Python API Usage

You can also use PDF2MD programmatically inside Python scripts or workflows:

```python
from pdf2md import convert_pdf, PDFToMarkdownConverter

# Quick functional conversion
result = convert_pdf(
    "lecture.pdf",
    output_path="lecture_notes.md",
    format_type="obsidian",
    render_slides=True,
    extract_images=True,
)

print("Title:", result["title"])
print("Slides processed:", result["total_slides"])
print("Output file:", result["primary_output"])
```

---

## Running Tests

Run the included unit test suite:

```bash
uv run python -m unittest tests/test_converter.py
```
