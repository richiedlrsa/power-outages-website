import requests, locale, pandas as pd, io, os
from datetime import date, timedelta
from .electric_providers import ElectricProvider
from google import genai
from dotenv import find_dotenv, load_dotenv

path = find_dotenv()
load_dotenv(path)
# sets the language of the date class to spanish
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

class ModelError(Exception):
    pass

class ScrapeError(Exception):
    pass

class Edenorte(ElectricProvider):
    url = 'https://edenorte.com.do/category/programa-de-mantenimiento-de-redes/'
    def __init__(self):
        super().__init__(Edenorte.url)
        self.soup = ElectricProvider.get_soup(self.url)
    
    def scrape(self) -> list:
        '''
        Runs the scraper
        Returns a list containing the scraped data
        '''
        self.data = self._organize_data()
        
        return self.data
        
    @staticmethod
    def get_monday() -> date:
        '''
        Calculates the start of the current week
        Returns a date object
        '''
        today = date.today()
        return (today - timedelta(days = today.weekday()))
    
    def _get_link(self, monday: date = None) -> str:
        '''
        Grabs the link for the maintenance data related to the current week
        Returns a string representation of the link
        '''
        if not monday:
            monday = self.get_monday()
        link_tag = self.soup.find(lambda tag: tag.name == 'a' and 
                              monday.strftime('%d') in tag.text and
                              monday.strftime('%B') in tag.text
                              )
        try:
            return link_tag['href']
        except (KeyError, TypeError):
            raise ScrapeError('Error fetching link. Website structure may have changed, or data for the current week may not be available yet.')
        
    def _get_file(self, monday: date = None):
        '''
        Grabs the url for the download file and initiates the get request to download the file
        Returns the content of the file in binary
        '''
        if not monday:
            monday = self.get_monday()
        soup = self.get_soup(self._get_link(monday=monday))
        divs = soup.find_all('div', class_ = 'w3eden')
        
        for div in divs:
            download_link_div = div.find(lambda tag: tag.name == 'a' and 
                                monday.strftime('%d') in tag.text and
                                monday.strftime('%B') in tag.text and 
                                ('excel' in tag.text or 
                                'EXCEL' in tag.text or
                                'Excel' in tag.text)
                                )
            
            if download_link_div:
                download_link_tag = div.find(lambda tag: tag.name == 'a' and 
                                tag.text.lower() == 'descargar'
                                )
        
                try:
                    return requests.get(download_link_tag['data-downloadurl']).content
                except KeyError:
                    raise Exception('Error downloading file. Website structure may have changed.')
        
        # if the loop finishes without returning, we did not find a download link
        raise Exception('Error fetching download link. Website structure may have changed.')
        
    def _prepare_data(self, monday: date = None):
        '''
        Opens a file-like object in memory
        Returns a pandas dataframe object created from the "file"
        '''
        excel_file = io.BytesIO(self._get_file(monday=monday))
        df = pd.read_excel(excel_file, sheet_name='Publicacion Externa')
        csv_formatted_data = df.to_csv(index=False)
        return csv_formatted_data
    
    def _extract_from_csv(self, monday: date = None):
        '''
        Extracts and organized the relevant data and creates a csv file from the extracted data
        Returns a string representation of the extracted data
        '''
        
        prompt =['''
                You are an expert data extraction assistant. Your task is to analyze a csv file of a power maintenance schedule and organize the data,
                carefully following these instructions:
                1. Find and extract the data pertaining to the date, province, schedule, and zone ("municipio")'
                2. The output should a single csv-like string where each row represents a single maintenance event.
                
                The header row should be: province, day, time, sectors
                
                Here is an example of a single row from the table and its correct csv output:
                province,day,time,sectors
                Santo Domingo,lunes 15 de septiembre,9:20 a.m. - 3:20 p.m.,"Boreal, La Ureña, Los Tres Brazos, Riviera Del Ozama"
                
                The output should strictly follow this format. If the data in the original file is formatted differently, your task
                is to adjust it so that it matches the expected format. For example, the data might be in in iso format (YYYY - MM - DD), 
                so you may need to match the "lunes 15 de septiembre" format. The header rows in the original file might also not match
                the rows specified above. Your task is find the corresponding data and make sure the output matches the "province,day,time,sectors"
                format.
                
                Analyze the entire csv file and extract all the entries in order from start to end of week. 
                Your response should not contain any text outside of the csv data. Each row should have exactly four columns.
                ''']

        data = self._prepare_data(monday=monday)
        prompt.append(data)
        client = genai.Client(api_key = os.getenv('GEMINI_API_KEY'))
        
        try:
            response = client.models.generate_content(
                model = 'gemini-2.5-pro',
                contents = prompt
            )
        except Exception:
            raise ModelError('AI model not currently available. Please try again later or use a different model.')
    
        return response.text
        
    def _organize_data(self, data: str = None) -> list:
        '''
        Extracts and parses the data from the data frame object
        Returns a list of dictionaries
        '''
        formatted_csv = io.StringIO(data if data else self._extract_from_csv())
        df = pd.read_csv(formatted_csv)
        data = []
        
        for day in df.day.unique():
            for province in df.province.unique():
                filtered_data = df[(df.day == day) & (df.province == province)]
                if filtered_data.empty:
                    continue
                maintenance = []
                for _, row in filtered_data.iterrows():
                    maintenance.append({'time': row.time, 'sectors': row.sectors.split(',')})
                
                # if the date is returned as an Excel serial number, convert it to a date time object and format it.
                if isinstance(row.day, int):
                    # an Excel date serial number represents n days from 1899-12-30. Adding those days gives the current date.
                    day_to_append = (date.fromisoformat('1899-12-30') + timedelta(days = day))
                else:
                    day_to_append = day
                    
                data.append({
                    'company': 'Edenorte',
                    'week_number': f'{date.today().isocalendar()[1]}',
                    'day': day_to_append,
                    'province': province,
                    'maintenance': maintenance
                }) 
                
        return data

        
