import os

files = {
    "requirements.txt": """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
pymupdf>=1.23.0
reportlab>=4.1.0
fhir.resources>=7.1.0
python-multipart>=0.0.9
""",
    "FAILURES.md": """# Pipeline Failure & Iteration Log

## Baseline Skeleton (Phase 1)
- **Known Issue**: Segmentation uses heuristic substring checks; will fail on scanned faxes without text layers.
- **Resolution Path (Phase 2)**: Integrate layout-aware multi-modal embeddings and visual boundary classifiers.
- **Terminology Mapping**: Currently rule-based dictionary lookup.
- **Resolution Path (Phase 3)**: Integrate MedSpaCy/QuickUMLS + RxNav API vector mapping with dynamic cosine confidence scores.
"""
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w") as f:
        f.write(content)

print("Project baseline written. Now run:\n  pip install -r requirements.txt\n  python src/generator.py\n  uvicorn app:app --reload")