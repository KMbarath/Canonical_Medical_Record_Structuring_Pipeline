import pytesseract
from PIL import Image
import io
import pymupdf as fitz

def get_page_text(page: fitz.Page) -> str:
    """Extracts digital text or falls back to Tesseract OCR for scanned faxes/images."""
    text = page.get_text().strip()
    if len(text) < 20:
        try:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img).strip()
        except Exception as e:
            print(f"OCR Fallback Error on page {page.number}: {e}")
            return text
    return text