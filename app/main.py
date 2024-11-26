# app/main.py
from fastapi import FastAPI
from routers import motorman, train, line, train_motorman, line_csv

app = FastAPI()

app.include_router(motorman.router, prefix="/motorman", tags=["Motorman"])
app.include_router(train.router, prefix="/train", tags=["Train"])
app.include_router(line.router, prefix="/line", tags=["Line"])
app.include_router(train_motorman.router, prefix="/train_motorman", tags=["TrainMotorman"])
app.include_router(line_csv.router, prefix="/line_csv", tags=["LineCSV"])