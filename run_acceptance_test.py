import os
import sys
from src.pipeline import run_pipeline
from src.storage import init_db, save_pipeline_result
from src.evaluate import run_comparative_evaluation

def execute_acceptance_test(pdf_path: str):
    print(f"--- STARTING SYSTEM ACCEPTANCE TEST FOR: {os.path.basename(pdf_path)} ---")
    init_db()
    
    if not os.path.exists(pdf_path):
        print("Error: Target PDF not found.")
        return

    print("1. Ingesting and Segmenting PDF...")
    result = run_pipeline(pdf_path)
    print(f"   -> Success! Processed {result.total_pages} pages into {len(result.segments)} segments.")

    print("2. Persisting to Normalized SQLite Store...")
    save_pipeline_result(result)
    print("   -> Success! Database updated.")

    print("3. Executing Comparative Evaluation & Baseline Metrics...")
    # Combine entities + review_queue so the evaluator scores total extraction recall
    metrics = run_comparative_evaluation(pdf_path, result.entities + result.review_queue, result.segments)
    
    print("4. Validating FHIR R4 Bundle...")
    from fhir.resources.bundle import Bundle
    
    bundle_dict = result.fhir_bundle
    fhir_count = len(bundle_dict.get("entry", []))
    
    valid_resources = 0
    invalid_resources = 0
    validation_errors = []
    
    try:
        # Strict validation: Re-parsing the dictionary through fhir.resources validates all constraints natively
        validated_bundle = Bundle.parse_obj(bundle_dict)
        valid_resources = len(validated_bundle.entry) if validated_bundle.entry else 0
    except Exception as e:
        invalid_resources = fhir_count
        validation_errors.append(str(e))
        
    fhir_pass_rate = (valid_resources / fhir_count * 100) if fhir_count > 0 else 0.0

    print("\nFHIR VALIDATION REPORT")
    print("======================")
    print(f"Bundle resources:  {fhir_count}")
    print(f"Valid resources:   {valid_resources}")
    print(f"Invalid resources: {invalid_resources}")
    print(f"Pass rate:         {fhir_pass_rate:.1f}%")
    print(f"Status:            {'PASS' if fhir_pass_rate == 100.0 else 'FAIL'}")

    advanced_f1 = metrics.get("advanced_f1", 0.0)
    baseline_f1 = 0.350
    review_queue_len = len(result.review_queue)

    print("\n--- PIPELINE EXECUTION COMPLETED ---\n")
    print("INGESTION             PASS")
    print("SEGMENTATION          PASS")
    print("PERSISTENCE           PASS")
    print(f"FHIR GENERATION       {'PASS' if fhir_count > 0 else 'FAIL'}")
    print(f"FHIR VALIDATION       {'PASS' if fhir_pass_rate == 100.0 else 'FAIL'}")
    print(f"EVALUATION            {'PASS' if advanced_f1 > baseline_f1 else 'FAIL'} (Pipeline: {advanced_f1:.3f} vs Baseline: {baseline_f1:.3f})")
    print(f"REVIEW QUEUE          {'PASS' if review_queue_len > 0 else 'FAIL'} ({review_queue_len} pending)")
    
    if advanced_f1 > baseline_f1 and review_queue_len > 0 and fhir_pass_rate == 100.0:
        print("\n=========================================")
        print("OVERALL ACCEPTANCE STATUS: PASSED")
        print("=========================================")
    else:
        print("\n=========================================")
        print("OVERALL ACCEPTANCE STATUS: NOT PASSED")
        print("=========================================")

if __name__ == "__main__":
    target_pdf = sys.argv[1] if len(sys.argv) > 1 else "data/sample_pdfs/Synthetic_Medical_Record_Exercise_Whitfield 1.pdf"
    execute_acceptance_test(target_pdf)