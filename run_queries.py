import sqlite3
from tabulate import tabulate

DB_PATH = "pipeline_store.db"

def execute_query(title: str, query: str):
    print("\n" + "=" * 80)
    print(f"CLINICAL QUERY: {title}")
    print("=" * 80)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("No matching clinical records found in the database.")
    conn.close()

def run_all():
    execute_query("1. All Laboratory & Vital Results", "SELECT raw_text, value, unit, source_page FROM clinical_facts WHERE entity_type = 'Observation'")
    execute_query("2. Full Medication Reconciliation List", "SELECT raw_text, value, status, code, source_page FROM clinical_facts WHERE entity_type = 'MedicationStatement'")
    execute_query("3. Conditions Coded to Terminology", "SELECT raw_text, system, code, display, source_page FROM clinical_facts WHERE entity_type = 'Condition'")
    execute_query("4. Completed Procedures", "SELECT f.raw_text, f.code, s.document_type, f.source_page FROM clinical_facts f LEFT JOIN document_segments s ON f.source_document_id = s.document_id WHERE f.entity_type = 'Procedure'")
    execute_query("5. Clinical Review Queue", "SELECT entity_type, raw_text, confidence, source_page, review_status FROM review_queue ORDER BY source_page ASC")

if __name__ == "__main__":
    run_all()