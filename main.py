from fastapi import FastAPI
import uvicorn
from app.routers import AGO
from app.utils.logger import logger

app = FastAPI()

app.include_router(AGO.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level='info')