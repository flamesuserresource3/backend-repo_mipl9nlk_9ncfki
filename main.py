import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from database import create_document
from schemas import CustomOrder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.post("/api/custom-orders")
async def create_custom_order(
    name: str = Form(...),
    email: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Accept a custom order with optional file upload and persist metadata to the database."""
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)

    file_info = {"file_name": None, "file_type": None, "file_size": None}
    saved_path = None

    if file is not None:
        contents = await file.read()
        saved_path = os.path.join(uploads_dir, file.filename)
        with open(saved_path, "wb") as f:
            f.write(contents)
        file_info = {
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size": len(contents),
        }

    payload = CustomOrder(
        name=name,
        email=email,
        description=description,
        file_name=file_info["file_name"],
        file_type=file_info["file_type"],
        file_size=file_info["file_size"],
    )

    inserted_id = create_document("customorder", payload)

    return JSONResponse(
        {
            "status": "success",
            "id": inserted_id,
            "saved_file_path": saved_path,
        }
    )

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
