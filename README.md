# Canonical FHIR Clinical Extraction Pipeline

A prototype clinical NLP pipeline that ingests unstructured medical records in PDF format, extracts clinical facts, normalizes them to standard medical terminologies, and packages the results into validated FHIR R4 bundles.

## Overview

This pipeline bridges the gap between unstructured clinical notes and interoperable healthcare data standards. It processes multi-page medical records and identifies:

- Conditions
- Medications
- Procedures
- Observations, including vital signs and laboratory results

The pipeline preserves source-page provenance, deduplicates repeated facts, routes uncertain results for clinical review, and evaluates extraction quality against verified ground truth.

## Key Features

### 1. Multi-page Clinical Document Processing

Processes medical-record PDFs page by page and extracts structured
clinical information from heterogeneous clinical content.

### 2. Clinical Information Extraction

Uses targeted clinical pattern recognition to identify:

- Conditions
- Medications
- Procedures
- Laboratory results
- Vital signs

Each extracted fact retains its source-page information.

### 3. Terminology Normalization

Attempts to normalize extracted clinical concepts to standard
terminologies:

| Clinical Entity | Target Terminology |
|---|---|
| Conditions | SNOMED CT |
| Medications | RxNorm |
| Procedures | CPT |
| Laboratory/Observations | LOINC |

When a confident terminology mapping cannot be established, the pipeline
retains the raw concept and routes it for human review instead of
assigning an unreliable code.

### 4. Confidence-Based Clinical Review

Entities below the configured confidence threshold are placed in a
clinical review queue.

Current threshold:

`confidence < 0.85`

Example review records include:

- Ketorolac 30 mg
- Lumbosacral strain
- CT CERVICAL SPINE
- MRI LUMBAR SPINE
- ROTATOR CUFF REPAIR

### 5. Canonical Deduplication

Repeated clinical facts across source pages are reconciled using
canonical identifiers and normalized representations while retaining
source-page provenance.

### 6. FHIR R4 Generation and Validation

The pipeline constructs FHIR R4 resources and validates the generated
resources before accepting the output.

Latest acceptance-test result:

- Resources generated: 35
- Valid resources: 35
- Invalid resources: 0
- FHIR validation pass rate: 100%

### 7. SQLite Persistence

Structured clinical entities are persisted in a normalized SQLite
database, allowing downstream SQL-based clinical queries.

### 8. Evaluation Harness

The pipeline is evaluated against a naive baseline and reports:

- True Positives
- False Positives
- False Negatives
- Precision
- Recall
- F1 score

Latest acceptance-test result:

Input: Synthetic_Medical_Record_Exercise_Whitfield 1.pdf
Pages: 22

INGESTION             PASS
SEGMENTATION          PASS
PERSISTENCE           PASS
FHIR GENERATION       PASS
FHIR VALIDATION       PASS
EVALUATION            PASS
REVIEW QUEUE          PASS

Entity F1:
  Baseline: 0.350
  Pipeline: 0.929
  Delta:    +0.579

FHIR:
  Resources: 35
  Valid:     35
  Invalid:    0
  Pass rate: 100%

Review queue:
  Pending: 9

Overall acceptance status: PASSED

## Project Structure

```text
canonical-fhir-pipeline/
├── app.py                     # Application entry point
├── bootstrap.py               # Application/bootstrap helpers
├── evaluate_ground_truth.py   # Ground-truth evaluation entry point
├── run_acceptance_test.py     # End-to-end acceptance test
├── run_queries.py             # Queries the SQLite clinical store
├── test_pipeline.py           # Pipeline tests
├── requirements.txt           # Python dependencies
├── data/
│   ├── ground_truth/          # Verified expected extraction results
│   ├── sample_fax_bundle.json # Sample input bundle
│   └── sample_pdfs/           # Sample medical-record PDFs
├── src/
│   ├── baseline.py             # Naive baseline extractor
│   ├── config.py               # Configuration
│   ├── evaluate.py             # Evaluation and metrics
│   ├── extend_pdf.py           # PDF preparation utilities
│   ├── extraction.py           # Clinical extraction and routing
│   ├── fhir_builder.py         # FHIR Bundle construction
│   ├── generator.py            # Generated clinical content helpers
│   ├── normalizer.py           # Terminology normalization
│   ├── ocr.py                  # PDF text extraction and OCR
│   ├── pipeline.py             # End-to-end orchestration
│   ├── schemas.py              # Pydantic data models
│   ├── segmentation.py         # Document segmentation
│   └── storage.py              # SQLite persistence
└── README.md
```

The runtime database, `pipeline_store.db`, is generated in the project root and is not required in source control.

## Installation

From the project root, create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

The main dependencies include FastAPI, Uvicorn, Pydantic, PyMuPDF, ReportLab, `fhir.resources`, SQLite support, and `python-multipart`.

## Running the Pipeline

### End-to-End Acceptance Test

Delete the generated database before a fresh run, then execute the acceptance test:

```powershell
Remove-Item pipeline_store.db -ErrorAction Ignore
python run_acceptance_test.py
```

When no path is supplied, the script processes:

```text
data/sample_pdfs/Synthetic_Medical_Record_Exercise_Whitfield 1.pdf
```

The acceptance test:

1. Parses and segments the PDF.
2. Extracts and normalizes clinical entities.
3. Persists active entities and review-queue items to SQLite.
4. Generates a FHIR Bundle.
5. Strictly validates the generated FHIR resources.
6. Compares the advanced pipeline with the naive baseline.

### Process a Custom PDF

Pass a PDF path as the first command-line argument:

```powershell
Remove-Item pipeline_store.db -ErrorAction Ignore
python run_acceptance_test.py "data/sample_pdfs/Another_Patient_Record.pdf"
```

The PDF must exist at the supplied path.

### View Stored Clinical Data

After the pipeline has run, query the normalized SQLite store:

```powershell
python run_queries.py
```

The query script displays:

1. Laboratory and vital-sign observations
2. The medication reconciliation list
3. SNOMED CT coded conditions
4. Completed procedures
5. Pending clinical-review items

## Updating Ground Truth

When evaluating a new patient record, update the `ground_truth_codes` dictionary in [src/evaluate.py](src/evaluate.py) with the verified SNOMED CT, RxNorm, CPT, and LOINC codes for that record. Otherwise, the evaluation will continue to compare results with the default Whitfield gold standard.

## Acceptance-Test Results

The supplied Whitfield sample record completed successfully with the following results:

| Check | Result |
| --- | --- |
| Pages processed | 22 |
| Segments created | 22 |
| FHIR resources | 35 |
| Valid FHIR resources | 35 |
| FHIR validation pass rate | 100.0% |
| Naive baseline entity F1 | 0.350 |
| Advanced pipeline entity F1 | 0.929 |
| F1 improvement | +0.579 |
| Pending review items | 9 |
| Overall acceptance status | PASSED |

The successful run produced active observations, medications, conditions, and procedures, while nine low-confidence or unmapped entities were retained in the clinical review queue.

## Development Notes

- Remove `pipeline_store.db` before repeatable acceptance-test runs.
- Review queued entities before using uncertain mappings as clinical data.
- Keep ground-truth codes synchronized with the PDF being evaluated.
- Do not commit generated databases or patient data to source control.
