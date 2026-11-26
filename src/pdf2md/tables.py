"""Table extraction and Markdown conversion for PDF slides."""

from typing import List, Tuple, Any


def format_table_as_markdown(rows: List[List[Any]]) -> str:
    """Format a 2D list of cell strings as a clean GitHub-flavored Markdown table."""
    if not rows or not rows[0]:
        return ""

    # Clean cell texts
    cleaned_rows = []
    for row in rows:
        cleaned_row = [
            (str(cell).replace("\n", " ").strip() if cell is not None else "")
            for cell in row
        ]
        cleaned_rows.append(cleaned_row)

    # Ensure all rows have equal columns
    col_count = max(len(r) for r in cleaned_rows)
    for r in cleaned_rows:
        while len(r) < col_count:
            r.append("")

    header = cleaned_rows[0]
    separator = ["---"] * col_count
    body = cleaned_rows[1:] if len(cleaned_rows) > 1 else []

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]

    for row in body:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def extract_tables_from_page(page) -> List[Tuple[Tuple[float, float, float, float], str]]:
    """
    Extract tables from a PyMuPDF page.
    Returns a list of tuples: ((x0, y0, x1, y1), markdown_str).
    """
    results = []
    try:
        table_finder = page.find_tables()
        for tab in table_finder:
            # Check if to_markdown() is supported
            md_text = ""
            if hasattr(tab, "to_markdown"):
                try:
                    md_text = tab.to_markdown()
                except Exception:
                    md_text = ""
            if not md_text:
                extracted = tab.extract()
                if extracted:
                    md_text = format_table_as_markdown(extracted)

            if md_text.strip():
                bbox = tuple(tab.bbox)
                results.append((bbox, md_text.strip()))
    except Exception:
        pass

    return results
