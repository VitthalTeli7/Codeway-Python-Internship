from __future__ import annotations

from typing import Optional

try:
    import pytesseract
    from PIL import Image
    TESS_AVAILABLE = True
except Exception:
    TESS_AVAILABLE = False


def read_plate(image_path: str) -> Optional[str]:
    if not TESS_AVAILABLE:
        return None
    text = pytesseract.image_to_string(Image.open(image_path))
    text = text.strip().replace("\n", " ")
    return text if text else None

