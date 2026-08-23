from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Provenance(BaseModel):
    source_document_id: str
    source_page: int
    text_span: Optional[str] = None

class NormalizedConcept(BaseModel):
    system: str  # e.g., SNOMED, LOINC, RxNorm, CPT, UCUM
    code: str
    display: str

class ExtractedEntity(BaseModel):
    entity_id: str
    entity_type: str  # Condition, MedicationStatement, Observation, Procedure, etc.
    raw_text: str
    value: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[str] = "active"  # active / discontinued
    confidence: float
    provenance: List[Provenance]  # Changed from single item to List
    normalized_concept: Optional[NormalizedConcept] = None

class DocumentSegment(BaseModel):
    document_id: str
    document_type: str  # lab_report, discharge_summary, radiology, intake_form, cover_sheet, etc.
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