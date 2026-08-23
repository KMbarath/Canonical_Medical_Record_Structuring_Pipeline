import hashlib
from typing import List
from src.schemas import DocumentSegment
from src.ocr import get_page_text

def segment_pdf(doc) -> List[DocumentSegment]:
    segments = []
    seen_hashes = set()
    current_doc_type = "intake_form"
    current_pages = []
    
    for page_num, page in enumerate(doc, start=1):
        text = get_page_text(page)
        
        # Blank page detection (< 10 chars)
        is_blank = len(text.strip()) < 10
        
        # Duplicate page detection using MD5 hash
        page_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        is_duplicate = page_hash in seen_hashes
        if not is_duplicate and not is_blank:
            seen_hashes.add(page_hash)
            
        # Classify document type based on keywords
        lower_text = text.lower()
        if "discharge summary" in lower_text:
            doc_type = "discharge_summary"
        elif "lab report" in lower_text or "blood test" in lower_text or "panel" in lower_text:
            doc_type = "lab_report"
        elif "radiology" in lower_text or "mri" in lower_text or "scan" in lower_text:
            doc_type = "radiology"
        elif "insurance" in lower_text or "claim" in lower_text:
            doc_type = "insurance"
        elif "cover sheet" in lower_text or "fax" in lower_text:
            doc_type = "cover_sheet"
        else:
            doc_type = "clinical_note"
            
        segments.append(DocumentSegment(
            document_id=f"doc_{page_num:02d}",
            document_type=doc_type,
            pages=[page_num],
            confidence=0.92,
            is_duplicate=is_duplicate,
            is_blank=is_blank
        ))
        
    return segments