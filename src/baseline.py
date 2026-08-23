import pymupdf as fitz
import re
from typing import Dict, Any

def run_naive_pipeline(pdf_path: str) -> Dict[str, Any]:
    """
    Simulates the mandatory Naive Baseline:
    - Treats PDF as a single monolithic block.
    - No document boundary segmentation.
    - Raw regex extraction without context checks.
    - Zero terminology mapping or FHIR canonical coding.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    
    naive_entities = []
    
    # Naive extraction: simple substring search, no normalization
    raw_conditions = ["Cervical Strain", "Radiculopathy", "Lumbosacral Strain"]
    for cond in raw_conditions:
        if cond.lower() in full_text.lower():
            naive_entities.append({"type": "Condition", "raw_text": cond, "coded": False})
            
    raw_meds = ["Naproxen 500 mg", "Gabapentin 300 mg", "Methocarbamol 750 mg"]
    for med in raw_meds:
        if med.lower() in full_text.lower():
            naive_entities.append({"type": "MedicationStatement", "raw_text": med, "coded": False})
            
    return {
        "pipeline_type": "naive_baseline",
        "segments_detected": 1, # Fails to segment
        "entities_extracted": naive_entities,
        "terminology_mapping_rate": 0.0, # Zero mapping
        "fhir_valid": False # No FHIR structure
    }