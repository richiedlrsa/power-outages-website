from ..edeeste import Edeeste, ScrapeError
from datetime import timedelta, date
from .test_data import WEEKDAYS, MONTHS, TEST_MONDAY, DATA
import pytest, os, re, locale

@pytest.fixture(scope='function')
def edeeste():
    return Edeeste()

@pytest.fixture(scope='function')
def file(edeeste):
    temp_file = edeeste._download_file(monday=TEST_MONDAY)
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.remove(temp_file)

class TestEdeeste:
    def test_get_monday(self, edeeste):
        data = edeeste._get_monday()
        data = data.split()
        assert data[0] in WEEKDAYS
        assert data[1].isdigit()
        assert int(data[1]) in range(1, 31)
        assert data[3] in MONTHS
    
    def test_get_download_link(self, edeeste):
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        today = date.today()
        monday = (today - timedelta(days=today.weekday()))
        unavailable_monday = (monday + timedelta(days=7)).strftime('%A %d de %B')
        download_link = edeeste._get_download_link(monday=TEST_MONDAY)
        with pytest.raises(ScrapeError) as excinfo:
            download_link = edeeste._get_download_link(monday=unavailable_monday)
            
        assert str(excinfo.value) == 'Error fetching data. Website structure may have changed, or the data for the current week may not be available yet.'
        assert download_link
        assert isinstance(download_link, str)
    
    def test_download_file(self, file):
        assert os.path.exists(file)
        assert os.path.splitext(file)[1] == '.pdf'
        assert os.path.isfile(file)
    
    def test_extract_from_pdf(self, file, edeeste):
        resp = edeeste._extract_from_pdf(path=file).split('\n')
        header = resp[0].split(',')
        assert header[0] == 'province'
        assert header[1] == 'day'
        assert header[2] == 'time'
        assert header[3] == 'sectors'

        for i in range(1, len(resp)):
            vals = resp[i].split(',')
            date = vals[1].split()
            times = vals[2].split('-')
            time_pattern = r'\d{1,2}:\d{2} [aApP]\.?\s?[mM].?'
            assert date[0] in WEEKDAYS
            assert date[1].isdigit()
            assert int(date[1]) in range(1, 31)
            assert date[3] in MONTHS
            assert re.match(time_pattern, times[0].strip())
            assert re.match(time_pattern, times[1].strip())
    
    def test_organize_data(self, edeeste):
        outages = edeeste._organize_data(data=DATA)
        
        assert outages
        assert isinstance(outages, list)
        for outage in outages:
            assert isinstance(outage, dict)
            for k, v in outage.items():
                assert k in {'company', 'week_number', 'day', 'province','maintenance'}
                if k == 'company':
                    assert v in {'Edeeste', 'Edesur', 'Edenorte'}
                elif k == 'week_number':
                    assert v.isdigit()
                elif k == 'maintenance':
                    assert isinstance(v, list)
                    for event in v:
                        assert isinstance(event, dict)
                        for k2, v2 in event.items():
                            assert k2 in {'time', 'sectors'}
                            if k2 == 'sectors':
                                assert isinstance(v2, list)