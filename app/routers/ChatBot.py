import os
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/chatbot/")
async def create_upload_file(prompt:str):
    print(f"Received prompt: {prompt}") 
    try:
        return JSONResponse(content={'response': prompt + '? blah blah blah'}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)