import sqlite3
import json
from src.schemas import PipelineResult

DB_NAME = "pipeline_store.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinical_facts (
            id TEXT PRIMARY KEY,
            pipeline_id TEXT,
            entity_type TEXT,
            raw_text TEXT,
            value TEXT,
            unit TEXT,
            status TEXT,
            system TEXT,
            code TEXT,
            display TEXT,
            confidence REAL,
            source_page INTEGER,
            source_document_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_segments (
            document_id TEXT PRIMARY KEY,
            pipeline_id TEXT,
            document_type TEXT,
            pages TEXT,
            confidence REAL,
            is_duplicate INTEGER,
            is_blank INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_queue (
            id TEXT PRIMARY KEY,
            pipeline_id TEXT,
            entity_type TEXT,
            raw_text TEXT,
            confidence REAL,
            source_page INTEGER,
            source_document_id TEXT,
            review_status TEXT DEFAULT 'PENDING'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fhir_bundles (
            pipeline_id TEXT PRIMARY KEY,
            bundle_json TEXT,
            total_pages INTEGER,
            processed_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_pipeline_result(result: PipelineResult):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO fhir_bundles (pipeline_id, bundle_json, total_pages, processed_at) VALUES (?, ?, ?, ?)",
                   (result.pipeline_id, json.dumps(result.fhir_bundle), result.total_pages, result.processed_at))
    
    for seg in result.segments:
        cursor.execute("INSERT OR REPLACE INTO document_segments (document_id, pipeline_id, document_type, pages, confidence, is_duplicate, is_blank) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (seg.document_id, result.pipeline_id, seg.document_type, json.dumps(seg.pages), seg.confidence, int(seg.is_duplicate), int(seg.is_blank)))
        
    for ent in result.entities:
        sys_val = ent.normalized_concept.system if ent.normalized_concept else None
        code_val = ent.normalized_concept.code if ent.normalized_concept else None
        disp_val = ent.normalized_concept.display if ent.normalized_concept else None
        
        cursor.execute("INSERT OR REPLACE INTO clinical_facts (id, pipeline_id, entity_type, raw_text, value, unit, status, system, code, display, confidence, source_page, source_document_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (ent.entity_id, result.pipeline_id, ent.entity_type, ent.raw_text, ent.value, ent.unit, ent.status, sys_val, code_val, disp_val, ent.confidence, ent.provenance[0].source_page, ent.provenance[0].source_document_id))
        
    for rev in result.review_queue:
        cursor.execute("INSERT OR REPLACE INTO review_queue (id, pipeline_id, entity_type, raw_text, confidence, source_page, source_document_id, review_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (rev.entity_id, result.pipeline_id, rev.entity_type, rev.raw_text, rev.confidence, rev.provenance[0].source_page, rev.provenance[0].source_document_id, 'PENDING'))
    conn.commit()
    conn.close()

persist_pipeline_result = save_pipeline_result