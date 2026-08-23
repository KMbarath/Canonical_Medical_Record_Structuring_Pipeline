import pymupdf as fitz
import uuid
from datetime import datetime
from src.segmentation import segment_pdf
from src.extraction import extract_and_normalize
from src.fhir_builder import build_fhir_bundle
from src.storage import init_db, save_pipeline_result
from src.schemas import PipelineResult

def run_pipeline(pdf_path: str) -> PipelineResult:
    init_db()
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    segments = segment_pdf(doc)
    entities, review_queue = extract_and_normalize(doc, segments)
    fhir_bundle = build_fhir_bundle(segments, entities)
    
    result = PipelineResult(
        pipeline_id=str(uuid.uuid4()),
        total_pages=total_pages,
        segments=segments,
        entities=entities,
        review_queue=review_queue,
        fhir_bundle=fhir_bundle,
        processed_at=datetime.utcnow().isoformat()
    )
    
    save_pipeline_result(result)
    return result