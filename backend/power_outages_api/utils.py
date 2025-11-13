import asyncio
from .edeeste import Edeeste, ModelError as EdeesteModelError
from .edesur import Edesur
from .edenorte import Edenorte, ModelError as EdenorteModelError
from .models import MaintenanceEvent, TimeSectors
from .db import engine
from sqlmodel import SQLModel, Session, delete
from datetime import date
from sqlalchemy.exc import ProgrammingError

async def get_outages(company_class, retry):
    '''
    company: Edeeste, Edesur, or Edenorte class
    Fetches the data for the corresponding company and adds it to the database
    returns a co-routine
    '''
    while True:
        print(f'Fetching data for {company_class.__name__}...')
        try:
            company = await asyncio.to_thread(company_class)
            outages = await asyncio.to_thread(company.scrape)
        except (EdeesteModelError, EdenorteModelError):
            # ModelError is a server-side error. Keep trying until successful.
            if retry:
                print(f'Error fetching data from {company_class.__name__}. Retrying in 30 minutes.')
                await asyncio.sleep(1800)
            else:
                print(f'Error fetching data from {company_class.__name__}.')
                break
        except Exception as e:
            print(f'Error fetching data from {company_class.__name__}:', e)
            break
        else:
            print(f'Creating models for {company_class.__name__}...')
            await asyncio.to_thread(create_models, outages)
            print(f'Models for {company_class.__name__} created successfully!')
            break

async def main(retry=True) -> None:
    '''
    Runs the async function get_outages() with the valid companies concurrently
    '''
    coros = [get_outages(company, retry) for company in (Edeeste, Edesur, Edenorte)]
    
    await asyncio.gather(*coros)

def create_db() -> None:
    '''
    Creates the database
    '''
    SQLModel.metadata.create_all(engine)

        
def create_models(outages) -> None:
    '''
    outages: list of outages for the corresponding company
    creates table objects and adds them to the database
    '''
    
    with Session(engine) as session:
        
        # we delete the data from the current week to update it with fresh, updated data
        
        # first ensure that we have updated data for the company before deleting it
        
        companies_to_delete = [company for company in ('Edeeste', 'Edesur', 'Edenorte') if any(company in outage.values() for outage in outages)]
        try:
            session.exec(delete(MaintenanceEvent). \
                where(MaintenanceEvent.week_number == date.today().isocalendar()[1],
                MaintenanceEvent.company.in_(companies_to_delete)))
        except ProgrammingError:
            print('Skipping deletion. Table does not exist.')
    
        for outage in outages:
            outage_obj = MaintenanceEvent(week_number = outage['week_number'], company = outage['company'], day = outage['day'], province = outage['province'])
            for maintenance in outage['maintenance']:
                maintenance['sectors'] = list(map(lambda x: x.strip(), maintenance['sectors']))
                maintenance_obj = TimeSectors(time = maintenance['time'], sectors = maintenance['sectors'])

                outage_obj.maintenance.append(maintenance_obj)
            
            session.add(outage_obj)
            
        session.commit()