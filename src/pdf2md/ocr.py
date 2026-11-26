"""OCR fallback for scanned or image-based slides using Tesseract."""

import io
from typing import Optional
from PIL import Image

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


def ocr_page(page, dpi: int = 200, lang: str = "eng") -> Optional[str]:
    """Perform OCR on a PDF page using Tesseract."""
    if not HAS_PYTESSERACT:
        return None

    try:
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception:
        return None
