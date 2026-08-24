from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os

from src.pipeline import run_pipeline
from src.storage import init_db

app = FastAPI(title="Canonical FHIR Pipeline API")

# Ensure static folder exists for the frontend
os.makedirs("static", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup():
    init_db()

# Serve the Frontend UI at the root URL
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# Note: The route is still called process-pdf so we don't break your frontend JavaScript, 
# but it now handles all documents!
@app.post("/api/v1/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    ALLOWED_EXTENSIONS = ('.pdf', '.docx', '.png', '.jpg', '.jpeg', '.xlsx', '.xls')
    
    # Convert filename to lowercase to safely check the extension
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = run_pipeline(temp_path)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)