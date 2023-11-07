from fastapi import FastAPI
import uvicorn
from app.routers import AGO
from app.utils.logger import logger
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of origins allowed (["*"] to allow all origins)
    allow_credentials=True,  # Allow credentials (cookies, authorization headers, etc)
    allow_methods=["*"],  # Allow all methods or specify particular methods like ["GET", "POST"]
    allow_headers=["*"],  # Allow all headers or specify which ones are allowed
)
app.include_router(AGO.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level='info')