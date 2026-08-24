import pymupdf as fitz
import os

def extend_to_30_pages(input_path: str, output_path: str):
    doc = fitz.open(input_path)
    src = fitz.open(input_path) 
    
    for _ in range(8):
        doc.insert_pdf(src, from_page=0, to_page=0)
        
    doc.save(output_path)
    doc.close()
    src.close()
    
    # Verify the final page count
    final_doc = fitz.open(output_path)
    print(f"Success! Generated new PDF with {len(final_doc)} pages at {output_path}")
    final_doc.close()

if __name__ == "__main__":
    in_path = "data/sample_pdfs/Synthetic_Medical_Record_Exercise_Whitfield 1.pdf"
    out_path = "data/sample_pdfs/Whitfield_30_Page_Extended.pdf"
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    if os.path.exists(in_path):
        extend_to_30_pages(in_path, out_path)
    else:
        print("Input PDF not found. Please check your paths.")