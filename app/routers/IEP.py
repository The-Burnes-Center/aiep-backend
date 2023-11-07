
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/upload/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        file_location = f"files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return JSONResponse(content={"filedata": 'blah blah blah', "summarization": 'blah blah blah', 'translation': 'blah blah blah'}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)