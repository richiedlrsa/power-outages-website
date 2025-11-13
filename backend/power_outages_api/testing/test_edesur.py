from power_outages_api.edesur import Edesur

class TestEdesur:
    def test_organize_data(self):
        edesur = Edesur()
        edesur.scrape()
        outages = edesur.data
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