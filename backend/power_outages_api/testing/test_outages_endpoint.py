import os, pytest
from .test_data import DB_DATA
from power_outages_api.models import MaintenanceEvent, TimeSectors
from power_outages_api.routes import app
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel, select
from dotenv import load_dotenv, find_dotenv
from datetime import date

path = find_dotenv()
load_dotenv(path)
DB_URL = os.getenv('DATABASE_URL_TESTING')
engine = create_engine(DB_URL)
SQLModel.metadata.create_all(engine)
client = TestClient(app)

@pytest.fixture(scope="module")
def session():
    outage_objects = []
    with Session(engine) as db:
        for outage in DB_DATA:
            outage_obj = MaintenanceEvent(
                week_number=date.today().isocalendar()[1],
                company=outage['company'],
                day=outage['day'],
                province=outage['province']
            )
            
            for maintenance in outage['maintenance']:
                maintenance['sectors'] = list(map(lambda x: x.strip(), maintenance['sectors']))
                maintenance_obj = TimeSectors(time=maintenance['time'], sectors=maintenance['sectors'])
                
                outage_obj.maintenance.append(maintenance_obj)
            
            db.add(outage_obj)
            outage_objects.append(outage_obj)
        db.commit()
        
        yield
        
        outages_to_delete = db.exec(select(MaintenanceEvent).where(MaintenanceEvent.week_number == date.today().isocalendar()[1])).all()
        for o in outages_to_delete:
            db.delete(o)
        db.commit()
        
class TestOutagesEndpoint:
    def test_outages(self, session):
        resp = client.get('/outages/')
        data = resp.json()
        assert resp.status_code == 200
        assert isinstance(data, list)
        for outage in data:
            assert isinstance(outage, dict)
            for k, v in outage.items():
                assert k in {'company', 'week_number', 'day', 'province','maintenance'}
                if k == 'company':
                    assert v in {'Edeeste', 'Edesur', 'Edenorte'}
                elif k == 'week_number':
                    assert isinstance(v, int)
                elif k == 'maintenance':
                    assert isinstance(v, list)
                    for event in v:
                        assert isinstance(event, dict)
                        for k2, v2 in event.items():
                            assert k2 in {'time', 'sectors'}
                            if k2 == 'sectors':
                                assert isinstance(v2, list)