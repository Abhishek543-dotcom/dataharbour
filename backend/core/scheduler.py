# APScheduler job definitions
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def schedule_job(scheduler: AsyncIOScheduler, job_func, trigger):
    scheduler.add_job(job_func, trigger)