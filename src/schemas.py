from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Provenance(BaseModel):
    source_document_id: str
    source_page: int
    text_span: Optional[str] = None

class NormalizedConcept(BaseModel):
    system: str  
    code: str
    display: str

class ExtractedEntity(BaseModel):
    entity_id: str
    entity_type: str 
    raw_text: str
    value: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[str] = "active" 
    confidence: float
    provenance: List[Provenance] 
    normalized_concept: Optional[NormalizedConcept] = None

class DocumentSegment(BaseModel):
    document_id: str
    document_type: str 
    pages: List[int]
    confidence: float
    is_duplicate: bool = False
    is_blank: bool = False

class PipelineResult(BaseModel):
    pipeline_id: str
    total_pages: int
    segments: List[DocumentSegment]
    entities: List[ExtractedEntity]
    review_queue: List[ExtractedEntity]
    fhir_bundle: Dict[str, Any]
    processed_at: str