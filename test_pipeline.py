import pytest
import uuid
from src.normalizer import normalize_condition, normalize_observation, normalize_unit
from src.extraction import deduplicate_entities
from src.schemas import ExtractedEntity, Provenance

def test_normalize_condition_snomed():
    res, conf = normalize_condition("cervical strain")
    assert res["code"] == "128262009"
    assert conf == 0.95

def test_normalize_observation_loinc():
    res, conf = normalize_observation("blood pressure")
    assert res["code"] == "85354-9"
    assert conf == 0.95

def test_normalize_unit_ucum():
    res, conf = normalize_unit("mmHg")
    assert res["code"] == "mm[Hg]"

def test_deduplicate_entities_conflict_resolution():
    # Test conflict handling: keep entity with higher confidence score
    ent1 = ExtractedEntity(
        entity_id=str(uuid.uuid4()), entity_type="Condition", 
        raw_text="radiculopathy", confidence=0.70, 
        provenance=Provenance(source_page=1, source_document_id="doc-1")
    )
    ent2 = ExtractedEntity(
        entity_id=str(uuid.uuid4()), entity_type="Condition", 
        raw_text="radiculopathy", confidence=0.99, 
        provenance=Provenance(source_page=4, source_document_id="doc-2")
    )
    deduped = deduplicate_entities([ent1, ent2])
    assert len(deduped) == 1
    assert deduped[0].confidence == 0.99
    assert deduped[0].provenance.source_page == 4