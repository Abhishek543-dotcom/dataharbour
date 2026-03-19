from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.db import init_db_pool, close_db_pool
from api.routes import router

app = FastAPI(
    title="DataHarbour API",
    description="Modern Data Lakehouse Platform API",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

scheduler = AsyncIOScheduler()

# Initialize scheduler and DB pool
init_db_pool()
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    close_db_pool()