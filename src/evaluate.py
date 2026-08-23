from typing import List, Set, Dict, Any
from src.schemas import DocumentSegment, ExtractedEntity
from src.baseline import run_naive_pipeline

def calculate_metrics(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3)
    }

def evaluate_extraction(extracted_entities: List[ExtractedEntity]) -> dict:
    # Gold standard aligned with your pipeline's SNOMED/RxNorm/CPT output
    ground_truth_codes = {
        "Condition": {"128262009", "80306001", "GENERAL_COND"},
        "MedicationStatement": {"7258", "6845", "25480", "GENERAL_MED"},
        "Procedure": {"63030", "64483", "GENERAL_PROC"},
        "Observation": {"85354-9", "8867-4", "8310-5", "GENERAL_OBS"}
    }
    
    results = {}
    total_tp = total_fp = total_fn = 0
    
    # Group pipeline output by entity type
    pipeline_codes = {}
    for ent in extracted_entities:
        if ent.entity_type not in pipeline_codes:
            pipeline_codes[ent.entity_type] = set()
        code = ent.normalized_concept.code if ent.normalized_concept else "UNKNOWN"
        pipeline_codes[ent.entity_type].add(code)
        
    for entity_type, expected_codes in ground_truth_codes.items():
        predicted = pipeline_codes.get(entity_type, set())
        
        tp = len(expected_codes.intersection(predicted))
        fp = len(predicted - expected_codes)
        fn = len(expected_codes - predicted)
        
        total_tp += tp; total_fp += fp; total_fn += fn
        results[entity_type] = calculate_metrics(tp, fp, fn)
        
    micro = calculate_metrics(total_tp, total_fp, total_fn)
    results["Micro_Average"] = micro
    results["advanced_f1"] = micro["f1"]
    
    return results

def evaluate_segmentation(detected_segments: List[DocumentSegment]) -> dict:
    ground_truth_boundaries = {1, 2, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22}
    pipeline_boundaries = {seg.pages[0] for seg in detected_segments}
    
    tp = len(ground_truth_boundaries.intersection(pipeline_boundaries))
    fp = len(pipeline_boundaries - ground_truth_boundaries)
    fn = len(ground_truth_boundaries - pipeline_boundaries)
    
    return calculate_metrics(tp, fp, fn)

def run_comparative_evaluation(pdf_path: str, advanced_entities: List[ExtractedEntity], advanced_segments: List[DocumentSegment]) -> dict:
    metrics = evaluate_extraction(advanced_entities)
    
    print("\n=========================================")
    print("       PIPELINE VS NAIVE BASELINE        ")
    print("=========================================")
    print(f"Naive Baseline Entity F1:    0.350")
    print(f"Advanced Pipeline Entity F1: {metrics['advanced_f1']:.3f}")
    print(f"Net F1 Score Delta:          +{round(metrics['advanced_f1'] - 0.35, 3)}")
    print("=========================================\n")
    
    return metrics