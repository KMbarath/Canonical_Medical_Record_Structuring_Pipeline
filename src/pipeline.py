import pymupdf as fitz
import datetime
import uuid
import os
from src.schemas import PipelineResult, DocumentSegment
from src.extraction import extract_and_normalize
from src.fhir_builder import build_fhir_bundle
from src.ocr import extract_text_from_image, extract_text_from_docx, extract_text_from_excel

class MockPage:
    """A fake PDF page to trick the extraction loop into accepting Word/Excel/Image text."""
    def __init__(self, text, page_num=1):
        self._text = text
        self.number = page_num

    def get_text(self):
        return self._text

def load_document(file_path: str):
    """Traffic router: Looks at the file extension and uses the correct parser."""
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        return fitz.open(file_path)
    
    # Handle Images
    elif ext in ['png', 'jpg', 'jpeg']:
        text = extract_text_from_image(file_path)
        return [MockPage(text)]
        
    # Handle Word
    elif ext == 'docx':
        text = extract_text_from_docx(file_path)
        return [MockPage(text)]
        
    # Handle Excel
    elif ext in ['xlsx', 'xls']:
        text = extract_text_from_excel(file_path)
        return [MockPage(text)]
        
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def run_pipeline(file_path: str) -> PipelineResult:
    pipeline_id = f"pipe-{uuid.uuid4().hex[:8]}"
    
    # 1. Route the file to the correct parser
    doc = load_document(file_path)
    
    # For non-PDFs, total_pages is just 1 (the mocked page)
    total_pages = len(doc) if hasattr(doc, '__len__') else 1
    
    # Create a basic segment for the whole document
    segments = [
        DocumentSegment(
            document_id=f"doc-{uuid.uuid4().hex[:6]}",
            document_type="clinical_note", 
            pages=list(range(1, total_pages + 1)),
            confidence=0.95
        )
    ]
    
    # 2. Extract and Normalize (This works perfectly with our MockPage!)
    entities, review_queue = extract_and_normalize(doc, segments)
    
    # 3. Build FHIR Bundle
    fhir_bundle = build_fhir_bundle(segments, entities)

    return PipelineResult(
        pipeline_id=pipeline_id,
        patient_id="pat-1",
        processed_at=datetime.datetime.utcnow().isoformat(),
        total_pages=total_pages,
        segments=segments,
        entities=entities,
        review_queue=review_queue,
        fhir_bundle=fhir_bundle
    )