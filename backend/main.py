from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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

# Initialize scheduler
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()