import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_synthetic_multidoc_pdf(output_pdf_path: str, ground_truth_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    os.makedirs(os.path.dirname(ground_truth_path), exist_ok=True)
    
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    
    ground_truth = {
        "patient": {"name": "Eleanor Vance", "dob": "1974-06-12", "gender": "female"},
        "documents": [],
        "pages": []
    }
    
    current_page = 1
    
    # Document 1: Fax Cover Sheet (1 Page)
    c.drawString(100, height - 100, "CONFIDENTIAL HEALTHCARE FAX TRANSMISSION")
    c.drawString(100, height - 130, "TO: Dr. J. Martinez (Cardiology)")
    c.drawString(100, height - 150, "FROM: St. Jude Medical Records")
    c.drawString(100, height - 170, "PATIENT: Eleanor Vance | DOB: 1974-06-12")
    c.drawString(100, height - 190, "TOTAL PAGES: 6")
    c.showPage()
    ground_truth["pages"].append({"page_num": current_page, "type": "cover_sheet", "doc_id": "doc_01"})
    ground_truth["documents"].append({"doc_id": "doc_01", "type": "cover_sheet", "pages": [current_page]})
    current_page += 1
    
    # Document 2: Discharge Summary (2 Pages)
    c.drawString(100, height - 100, "ST. JUDE MEDICAL CENTER - DISCHARGE SUMMARY")
    c.drawString(100, height - 120, "Patient: Eleanor Vance | MRN: SJ-89210 | DOB: 1974-06-12")
    c.drawString(100, height - 150, "Admission Date: 2026-01-10 | Discharge Date: 2026-01-14")
    c.drawString(100, height - 180, "PRIMARY DIAGNOSIS: Essential Hypertension (I10)")
    c.drawString(100, height - 200, "SECONDARY DIAGNOSIS: Type 2 Diabetes Mellitus (E11.9)")
    c.drawString(100, height - 230, "DISCHARGE MEDICATIONS:")
    c.drawString(120, height - 250, "1. Lisinopril 20mg Oral Daily (RxNorm: 314076)")
    c.drawString(120, height - 270, "2. Metformin 500mg Oral Twice Daily (RxNorm: 860975)")
    c.drawString(100, 50, "Page 1 of 2")
    c.showPage()
    ground_truth["pages"].append({"page_num": current_page, "type": "discharge_summary", "doc_id": "doc_02"})
    current_page += 1
    
    c.drawString(100, height - 100, "ST. JUDE MEDICAL CENTER - DISCHARGE SUMMARY (Cont.)")
    c.drawString(100, height - 130, "HOSPITAL COURSE: Patient admitted with hypertensive urgency. Stabilized on oral therapy.")
    c.drawString(100, height - 160, "ALLERGIES: Penicillin - Severe rash")
    c.drawString(100, 50, "Page 2 of 2")
    c.showPage()
    ground_truth["pages"].append({"page_num": current_page, "type": "discharge_summary", "doc_id": "doc_02"})
    ground_truth["documents"].append({"doc_id": "doc_02", "type": "discharge_summary", "pages": [current_page - 1, current_page]})
    current_page += 1
    
    # Document 3: Lab Report (1 Page)
    c.drawString(100, height - 100, "QUEST DIAGNOSTICS - CLINICAL PATHOLOGY REPORT")
    c.drawString(100, height - 120, "Patient: Eleanor Vance | Collection Date: 2026-01-11")
    c.drawString(100, height - 160, "TEST                  RESULT    UNIT     REF RANGE     FLAG")
    c.drawString(100, height - 180, "Glucose (LOINC: 2345-7) 142       mg/dL    70 - 99       HIGH")
    c.drawString(100, height - 200, "Potassium (LOINC: 2823-3) 4.2      mmol/L   3.5 - 5.0     NORMAL")
    c.drawString(100, height - 220, "Hemoglobin A1c (4548-4) 7.8       %        4.0 - 5.6     HIGH")
    c.drawString(100, 50, "Page 1 of 1")
    c.showPage()
    ground_truth["pages"].append({"page_num": current_page, "type": "lab_report", "doc_id": "doc_03"})
    ground_truth["documents"].append({"doc_id": "doc_03", "type": "lab_report", "pages": [current_page]})
    current_page += 1
    
    # Document 4: Radiology Report (1 Page)
    c.drawString(100, height - 100, "ADVANCED IMAGING ASSOCIATES - RADIOLOGY REPORT")
    c.drawString(100, height - 120, "Patient: Eleanor Vance | Exam: Chest X-Ray 2-Views")
    c.drawString(100, height - 140, "Date: 2026-01-10")
    c.drawString(100, height - 170, "FINDINGS: Cardiomegaly noted. Lungs are clear of focal consolidation.")
    c.drawString(100, height - 190, "IMPRESSION: Mild cardiomegaly without acute pulmonary edema.")
    c.drawString(100, 50, "Page 1 of 1")
    c.showPage()
    ground_truth["pages"].append({"page_num": current_page, "type": "radiology_report", "doc_id": "doc_04"})
    ground_truth["documents"].append({"doc_id": "doc_04", "type": "radiology_report", "pages": [current_page]})
    
    c.save()
    
    with open(ground_truth_path, "w") as f:
        json.dump(ground_truth, f, indent=2)

if __name__ == "__main__":
    create_synthetic_multidoc_pdf("data/sample_pdfs/sample_fax_bundle.pdf", "data/ground_truth/sample_fax_bundle.json")
    print("Generated synthetic PDF and Ground Truth JSON.")