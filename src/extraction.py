import re
import hashlib
from typing import List, Tuple
from src.schemas import ExtractedEntity, Provenance, NormalizedConcept, DocumentSegment
from src.normalizer import (
    normalize_condition, normalize_medication, normalize_procedure, 
    normalize_observation
)
from src.ocr import get_page_text

def generate_deterministic_id(entity_type: str, concept_code: str, display_text: str) -> str:
    """Generates a stable ID based on concept AND text to prevent generalized terms from overwriting each other."""
    unique_string = f"{entity_type.lower()}_{concept_code.lower()}_{display_text.lower().strip()}"
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def deduplicate_entities(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
    """Canonical Deduplication: Merges instances of the SAME clinical concept + display name across pages."""
    seen = {}
    for ent in entities:
        canonical_code = ent.normalized_concept.code if ent.normalized_concept else "UNKNOWN"
        canonical_display = ent.normalized_concept.display if ent.normalized_concept else ent.raw_text
        
        # Include canonical_display in the key so GENERAL_MED doesn't swallow distinct unmapped drugs
        key = f"{ent.entity_type}_{canonical_code}_{canonical_display.lower()}"
        
        if key not in seen:
            seen[key] = ent
        else:
            # Reconcile: Merge provenance pages, do not create a new database row
            existing = seen[key]
            existing.confidence = max(existing.confidence, ent.confidence)
            existing_pages = {p.source_page for p in existing.provenance}
            
            for prov in ent.provenance:
                if prov.source_page not in existing_pages:
                    existing.provenance.append(prov)
                    existing_pages.add(prov.source_page)
    return list(seen.values())

def extract_and_normalize(doc, segments: List[DocumentSegment]) -> Tuple[List[ExtractedEntity], List[ExtractedEntity]]:
    valid_entities = []
    review_queue = []
    
    generic_med_pattern = re.compile(r"\b(?!(?:Blood|Loss|With|Continue|Add|Titrate)\b)([A-Z][a-z]{3,20}(?:\s+[a-z]{3,15})?)\s+(\d+(?:/\d+)?(?:\.\d+)?\s*(?:mg|mcg|g|mL|tabs|caps))\b", re.IGNORECASE)
    generic_vital_pattern = re.compile(r"\b(BP|HR|Temperature|T)\s*[:=]?\s*(\d{2,3}(?:/\d{2,3})?|\d{2,3}\.\d+)\s*(F|C|bpm|mmHg)?\b", re.IGNORECASE)

    explicit_conditions = re.compile(r"\b(cervical strain|lumbosacral strain|radiculopathy|lumbar radiculopathy|mechanical low back pain|hypertension|diabetes|asthma|hyperlipidemia|osteoarthritis|fracture|tear|sprain|bursitis|arthritis)\b", re.IGNORECASE)
    
    explicit_procedures = re.compile(r"\b(microdiscectomy|tfesi|transforaminal epidural steroid injection|ct\s+[a-z]+|mri\s+[a-z]+|rotator cuff repair|x-ray|radiograph|physical therapy|surgery|reduction)\b", re.IGNORECASE)
    
    explicit_allergies = re.compile(r"\b(penicillin|sulfa|latex|iodine|peanuts|amoxicillin)\b(?:\s+allergy)?", re.IGNORECASE)
    
    generic_condition_pattern = re.compile(r"(?:diagnosis|diagnoses|impression|assessment)\s*[:\-]?\s*\n*([A-Za-z\s,\-]{4,35})(?=\.|\n|$)", re.IGNORECASE)
    
    blocklist = {"use only", "same", "same procedure", "confirmed intraoperatively", "patient progressing well", "present illness", "at discharge", "en route", "review"}

    for page_num, page in enumerate(doc, start=1):
        text = get_page_text(page)
        doc_id = f"doc_{page_num:02d}"
        
        # --- MEDICATIONS ---
        for match in generic_med_pattern.finditer(text):
            med_name, dose = match.groups()
            concept, conf = normalize_medication(med_name.strip())
            if not concept:
                concept = {"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "GENERAL_MED", "display": med_name.strip()}
                
            # IRONCLAD RULE: Ignore normalizer.py, force it to Review Queue if it's a GENERAL code
            if "GENERAL" in concept["code"]:
                conf = 0.80
                
            ent = ExtractedEntity(
                entity_id=generate_deterministic_id("MedicationStatement", concept["code"], concept["display"]),
                entity_type="MedicationStatement",
                raw_text=f"{med_name.strip()} {dose.strip()}", value=dose.strip(), status="active",
                confidence=conf, provenance=[Provenance(source_document_id=doc_id, source_page=page_num, text_span=match.group(0))],
                normalized_concept=NormalizedConcept(**concept)
            )
            if ent.confidence >= 0.85: valid_entities.append(ent)
            else: review_queue.append(ent)

        # --- VITALS ---
        for match in generic_vital_pattern.finditer(text):
            vital_name, val, unit = match.groups()
            concept, conf = normalize_observation(vital_name.strip())
            if not concept:
                concept = {"system": "http://loinc.org", "code": "GENERAL_OBS", "display": vital_name.strip()}
                
            # IRONCLAD RULE
            if "GENERAL" in concept["code"]:
                conf = 0.80
                
            ent = ExtractedEntity(
                entity_id=generate_deterministic_id("Observation", concept["code"], concept["display"]),
                entity_type="Observation",
                raw_text=f"{vital_name.strip()}: {val.strip()} {unit or ''}".strip(), value=val.strip(), unit=(unit or "").strip(),
                confidence=conf, provenance=[Provenance(source_document_id=doc_id, source_page=page_num, text_span=match.group(0))],
                normalized_concept=NormalizedConcept(**concept)
            )
            if ent.confidence >= 0.85: valid_entities.append(ent)
            else: review_queue.append(ent)

        # --- CONDITIONS ---
        cond_matches = []
        for match in explicit_conditions.finditer(text):
            cond_matches.append((match.group(0).strip(), 0.95))
        for match in generic_condition_pattern.finditer(text):
            cond_matches.append((match.group(1).strip(), 0.78))
            
        for cond_name, forced_conf in cond_matches:
            if len(cond_name) < 4 or any(bad_word in cond_name.lower() for bad_word in blocklist): 
                continue
                
            concept, conf = normalize_condition(cond_name)
            
            if "radiculopathy" in cond_name.lower():
                concept = {"system": "http://snomed.info/sct", "code": "80306001", "display": "Radiculopathy"}
                conf = 0.95
            elif not concept:
                concept = {"system": "http://snomed.info/sct", "code": "GENERAL_COND", "display": cond_name}
                conf = forced_conf
                
            # IRONCLAD RULE
            if "GENERAL" in concept["code"]:
                conf = 0.78
                
            ent = ExtractedEntity(
                entity_id=generate_deterministic_id("Condition", concept["code"], concept["display"]),
                entity_type="Condition",
                raw_text=cond_name, confidence=conf,
                provenance=[Provenance(source_document_id=doc_id, source_page=page_num, text_span=cond_name)],
                normalized_concept=NormalizedConcept(**concept)
            )
            if ent.confidence >= 0.85: valid_entities.append(ent)
            else: review_queue.append(ent)

        # --- PROCEDURES ---
        for match in explicit_procedures.finditer(text):
            proc_name = match.group(0).strip()
            if proc_name.upper() == "TFESI": 
                proc_name = "TRANSFORAMINAL EPIDURAL STEROID INJECTION"
                
            concept, conf = normalize_procedure(proc_name)
            if not concept:
                concept = {"system": "http://www.ama-assn.org/go/cpt", "code": "GENERAL_PROC", "display": proc_name}
                
            # IRONCLAD RULE
            if "GENERAL" in concept["code"]:
                conf = 0.80
                
            code_val = concept["code"]
            display_val = concept["display"]
                
            ent = ExtractedEntity(
                entity_id=generate_deterministic_id("Procedure", code_val, display_val),
                entity_type="Procedure",
                raw_text=proc_name.upper(), confidence=conf,
                provenance=[Provenance(source_document_id=doc_id, source_page=page_num, text_span=proc_name)],
                normalized_concept=NormalizedConcept(**concept)
            )
            if ent.confidence >= 0.85: valid_entities.append(ent)
            else: review_queue.append(ent)
            
        # --- ALLERGIES ---
        for match in explicit_allergies.finditer(text):
            allergy_name = match.group(1).strip()
            concept = {"system": "http://snomed.info/sct", "code": "GENERAL_ALLERGY", "display": allergy_name.capitalize()}
            conf = 0.80  # Forces routing to Review Queue to ensure safety
            
            ent = ExtractedEntity(
                entity_id=generate_deterministic_id("AllergyIntolerance", concept["code"], concept["display"]),
                entity_type="AllergyIntolerance",
                raw_text=allergy_name.upper(), confidence=conf,
                provenance=[Provenance(source_document_id=doc_id, source_page=page_num, text_span=allergy_name)],
                normalized_concept=NormalizedConcept(**concept)
            )
            if ent.confidence >= 0.85: valid_entities.append(ent)
            else: review_queue.append(ent)

    return deduplicate_entities(valid_entities), deduplicate_entities(review_queue)