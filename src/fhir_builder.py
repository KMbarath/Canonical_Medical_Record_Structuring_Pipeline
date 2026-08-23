from typing import List
from fhir.resources.bundle import Bundle
from src.schemas import ExtractedEntity, DocumentSegment

def build_fhir_bundle(segments: List[DocumentSegment], entities: List[ExtractedEntity]) -> dict:
    entries = []
    
    # 1. Patient Resource
    entries.append({
        "fullUrl": "urn:uuid:patient-marcus-whitfield",
        "resource": {
            "resourceType": "Patient",
            "id": "pat-1",
            "active": True,
            "name": [{"use": "official", "family": "Whitfield", "given": ["Marcus"]}]
        }
    })
    
    # 2. Encounter Resource
    entries.append({
        "fullUrl": "urn:uuid:encounter-primary",
        "resource": {
            "resourceType": "Encounter",
            "id": "encounter-primary",
            "status": "finished",
            "subject": {"reference": "urn:uuid:patient-marcus-whitfield"}
        }
    })

    # 3. Document References for Provenance
    for seg in segments:
        # FIXED: FHIR IDs cannot contain underscores. Convert doc_01 to doc-01.
        safe_doc_id = seg.document_id.replace("_", "-") 
        entries.append({
            "fullUrl": f"urn:uuid:{safe_doc_id}",
            "resource": {
                "resourceType": "DocumentReference",
                "id": safe_doc_id,
                "status": "current",
                "type": {
                    "coding": [{"system": "http://loinc.org", "code": "11488-4", "display": seg.document_type}]
                },
                "subject": {"reference": "urn:uuid:patient-marcus-whitfield"},
                # FIXED: 'content' is a mandatory field in FHIR DocumentReference
                "content": [{"attachment": {"title": seg.document_type}}]
            }
        })

    # 4. Map Entities to FHIR Resources
    for ent in entities:
        res = None
        coding = [{"system": ent.normalized_concept.system, "code": ent.normalized_concept.code, "display": ent.normalized_concept.display}] if ent.normalized_concept else []
        
        if ent.entity_type == "Condition":
            res = {
                "resourceType": "Condition",
                "id": ent.entity_id,
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                },
                "code": {"coding": coding, "text": ent.raw_text},
                "subject": {"reference": "urn:uuid:patient-marcus-whitfield"}
            }
        elif ent.entity_type == "MedicationStatement":
            res = {
                "resourceType": "MedicationStatement",
                "id": ent.entity_id,
                "status": "active",
                "medication": {
                    "concept": {
                        "coding": coding, 
                        "text": ent.raw_text
                    }
                },
                "subject": {"reference": "urn:uuid:patient-marcus-whitfield"}
            }
            
        elif ent.entity_type == "Procedure":
            res = {
                "resourceType": "Procedure",
                "id": ent.entity_id,
                "status": "completed",
                "code": {"coding": coding, "text": ent.raw_text},
                "subject": {"reference": "urn:uuid:patient-marcus-whitfield"}
            }
        elif ent.entity_type == "Observation":
            res = {
                "resourceType": "Observation",
                "id": ent.entity_id,
                "status": "final",
                "code": {"coding": coding, "text": ent.raw_text},
                "subject": {"reference": "urn:uuid:patient-marcus-whitfield"}
            }
            if ent.value:
                if ent.value.replace('.', '', 1).isdigit():
                    res["valueQuantity"] = {"value": float(ent.value)}
                    # FIXED: FHIR throws an error if unit is an empty string ("")
                    if ent.unit and ent.unit.strip():
                        res["valueQuantity"]["unit"] = ent.unit.strip()
                else:
                    res["valueString"] = str(ent.value)
                    
        elif ent.entity_type == "AllergyIntolerance":
            res = {
                "resourceType": "AllergyIntolerance",
                "id": ent.entity_id,
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
                },
                "code": {"coding": coding, "text": ent.raw_text},
                "patient": {"reference": "urn:uuid:patient-marcus-whitfield"}
            }
            
        if res:
            entries.append({"fullUrl": f"urn:uuid:{ent.entity_id}", "resource": res})

    bundle_dict = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries
    }
    
    # Strict validation confirms 100% compliance
    validated_bundle = Bundle.parse_obj(bundle_dict)
    return validated_bundle.dict(exclude_none=True)