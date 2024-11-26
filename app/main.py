# app/main.py
from fastapi import FastAPI
from routers import motorman

app = FastAPI()

app.include_router(motorman.router, prefix="/motorman", tags=["Motorman"])
