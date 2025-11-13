import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import Annotated, List
from .models import MaintenanceEvent, MaintenanceEventBase
from .db import engine
from .utils import main, create_db
from sqlalchemy.orm import selectinload
from datetime import date
from sqlalchemy.exc import ProgrammingError

router = APIRouter()
scheduler = BackgroundScheduler()

def cron_job():
    create_db()
    asyncio.run(main())

scheduler.add_job(cron_job, CronTrigger(hour=0, minute=0, second=0))
scheduler.start()

def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]

@router.get('/outages/', response_model = List[MaintenanceEventBase])
def outages(db: SessionDep):
    
    conditions = [MaintenanceEvent.week_number == date.today().isocalendar()[1],
                  MaintenanceEvent.day.ilike(f'%{date.today().year}%')]
    statement = select(MaintenanceEvent)
    
    try:
        statement = statement.where(*conditions). \
            order_by(MaintenanceEvent.province, MaintenanceEvent.day). \
                options(selectinload(MaintenanceEvent.maintenance))
        outages = db.exec(statement).all()
    except ProgrammingError:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "Data not found.")
    
    if not outages:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Data not found.")

    return outages