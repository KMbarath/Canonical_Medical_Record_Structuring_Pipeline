import io
import pytesseract
from PIL import Image
import pymupdf as fitz


try:
    import docx
except ImportError:
    docx = None

try:
    import pandas as pd
except ImportError:
    pd = None


def get_page_text(page: fitz.Page) -> str:
    """Extracts digital text or falls back to Tesseract OCR for scanned PDFs."""
    text = page.get_text().strip()
    
    # If the page has very little text, assume it is a scanned image
    if len(text) < 20:
        try:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img).strip()
        except Exception as e:
            print(f"OCR Fallback Error on page {page.number}: {e}")
            return text
            
    return text


def extract_text_from_image(file_path: str) -> str:
    """Extracts text directly from an image file (PNG, JPG, JPEG)."""
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        print(f"Image Extraction Error ({file_path}): {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a Microsoft Word document."""
    if not docx:
        print("Missing dependency: python-docx. Please install to parse Word files.")
        return ""
    
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        print(f"Word Extraction Error ({file_path}): {e}")
        return ""


def extract_text_from_excel(file_path: str) -> str:
    """Extracts text from a Microsoft Excel spreadsheet."""
    if not pd:
        print("Missing dependency: pandas & openpyxl. Please install to parse Excel files.")
        return ""
    
    try:
        # Read all sheets into a dictionary of DataFrames
        df_dict = pd.read_excel(file_path, sheet_name=None)
        text_blocks = []
        for sheet_name, df in df_dict.items():
            text_blocks.append(f"--- Sheet: {sheet_name} ---")
            # Convert dataframe to a flat string for the regex processor
            text_blocks.append(df.to_string(index=False))
        return "\n".join(text_blocks).strip()
    except Exception as e:
        print(f"Excel Extraction Error ({file_path}): {e}")
        return ""