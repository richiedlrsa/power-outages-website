import re
from .test_data import TEST_MONDAY_ISO, MONTHS, DATA, WEEKDAYS
from power_outages_api.edenorte import Edenorte, ScrapeError
from datetime import date, timedelta
import pytest, locale

@pytest.fixture(scope='function')
def edenorte():
    return Edenorte()

class TestEdenorte:
    def test_get_monday(self, edenorte):
        data = edenorte.get_monday()
        assert data == date.today() - timedelta(days=date.today().weekday())
        
    def test_get_link(self, edenorte):
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        today = date.today()
        monday = (today - timedelta(days=today.weekday()))
        unavailable_monday = monday + timedelta(days=7)
        good_link = edenorte._get_link(monday=TEST_MONDAY_ISO)
        
        with pytest.raises(ScrapeError) as excinfo:
            bad_link = edenorte._get_link(monday=unavailable_monday)
        
        assert str(excinfo.value) == 'Error fetching link. Website structure may have changed, or data for the current week may not be available yet.'
        assert good_link
        assert isinstance(good_link, str)
    
    def test_extract_from_csv(self, edenorte):
        resp = edenorte._extract_from_csv(monday=TEST_MONDAY_ISO).split('\n')
        header = resp[0].split(',')
        assert header[0] == 'province'
        assert header[1] == 'day'
        assert header[2] == 'time'
        assert header[3] == 'sectors'

        for i in range(1, len(resp)):
            # the last line might be an empty string
            if not resp[i]:
                continue
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
            
    def test_organize_data(self, edenorte):
        outages = edenorte._organize_data(data=DATA)
        
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