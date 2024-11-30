# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import motorman, train, line, train_motorman, line_csv, administrator, scheduler

app = FastAPI(
    title="Subway Scheduler API",
    description="API for subway scheduler",
    version="1.0.0",
    openapi_tags=[
    ],
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(motorman.router, prefix="/motorman", tags=["Motorman"])
app.include_router(train.router, prefix="/train", tags=["Train"])
app.include_router(line.router, prefix="/line", tags=["Line"])
app.include_router(train_motorman.router, prefix="/train_motorman", tags=["TrainMotorman"])
app.include_router(line_csv.router, prefix="/line_csv", tags=["LineCSV"])
app.include_router(administrator.router, prefix="/administrator", tags=["Administrator"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])