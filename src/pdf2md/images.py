"""Image extraction and slide snapshot rendering."""

import hashlib
import os
from typing import List, Tuple, Set


def render_slide_image(
    page,
    slide_num: int,
    output_dir: str,
    subdir: str = "slides",
    dpi: int = 150,
    img_format: str = "png",
) -> str:
    """
    Render the entire slide page as a high-resolution image.
    Returns the relative path from output_dir to the saved image.
    """
    target_dir = os.path.join(output_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)

    filename = f"slide_{slide_num:03d}.{img_format}"
    filepath = os.path.join(target_dir, filename)

    pix = page.get_pixmap(dpi=dpi)
    pix.save(filepath)

    return os.path.join(subdir, filename)


def extract_embedded_images(
    page,
    slide_num: int,
    output_dir: str,
    seen_hashes: Set[str],
    subdir: str = "images",
    min_dimension: int = 32,
) -> List[Tuple[Tuple[float, float, float, float], str]]:
    """
    Extract embedded raster images from a slide page.
    Filters out tiny decorative pixels/bullets and deduplicates identical images (e.g. repeated logos).
    Returns a list of ((x0, y0, x1, y1), rel_path).
    """
    target_dir = os.path.join(output_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)

    extracted = []
    image_list = page.get_images(full=True)
    doc = page.parent

    img_counter = 1
    for img_info in image_list:
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image.get("image")
            image_ext = base_image.get("ext", "png")
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Filter out tiny icons, spacers or bullets
            if width < min_dimension or height < min_dimension:
                continue

            # Deduplicate by content hash
            img_hash = hashlib.md5(image_bytes).hexdigest()
            if img_hash in seen_hashes:
                continue
            seen_hashes.add(img_hash)

            filename = f"slide_{slide_num:03d}_img_{img_counter:02d}.{image_ext}"
            filepath = os.path.join(target_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            rel_path = os.path.join(subdir, filename)

            # Try to get bbox on page
            rects = page.get_image_rects(xref)
            bbox = tuple(rects[0]) if rects else (0, 0, 0, 0)

            extracted.append((bbox, rel_path))
            img_counter += 1
        except Exception:
            continue

    return extracted
