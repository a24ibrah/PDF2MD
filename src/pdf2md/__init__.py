"""PDF2MD: Convert lecture slides in PDF format to clean Markdown."""

__version__ = "0.1.0"

from .converter import PDFToMarkdownConverter, convert_pdf

__all__ = ["PDFToMarkdownConverter", "convert_pdf", "__version__"]
