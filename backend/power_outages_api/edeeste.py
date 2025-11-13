import locale, requests, os, io, pandas as pd
from datetime import date, timedelta, datetime
from google import genai
from pdf2image import convert_from_path
from .electric_providers import ElectricProvider
from dotenv import load_dotenv, find_dotenv

path = find_dotenv()
load_dotenv(path)
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

class ModelError(Exception):
    pass

class ScrapeError(Exception):
    pass

class Edeeste(ElectricProvider):
    url = 'https://edeeste.com.do/index.php/programa-de-mantenimiento/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    def __init__(self):
        super().__init__(Edeeste.url)
        self.soup = ElectricProvider.get_soup(self.url, Edeeste.headers)

    def scrape(self) -> list:
        '''
        Runs the scraper
        Returns a list containing the scraped data
        '''
        self.data = self._organize_data()
        
        return self.data
    
    @staticmethod
    def _get_monday() -> tuple:
        """
        Gets the start of the current week in the following format:
        'lunes 01 de enero'
        Return the start of the week
        """
        # changes the language of the datetime objects to Spansh
        today = date.today()
        monday = (today - timedelta(days = today.weekday())).strftime('%A %d de %B')
        
        return monday
    
    def _get_download_link(self, monday: str = None) -> str:
        """
        Searches the website for the download link for the maintenance schedule of the current week
        Returns the link as a strng
        """
        if not monday:
            monday = self._get_monday()
        parent_tag = self.soup.find_all('div', class_ = 'media')
        if not parent_tag:
            raise ScrapeError('Error fetching data. Website structure may have changed.')
        
        for child in parent_tag:
            date_range = child.find(lambda tag: tag.name == 'a' and monday in tag.text.lower())
            if date_range:
                target_tag = child.find(lambda tag: tag.name == 'a' and tag.text.lower() == 'descargar')
                try:
                    download_link = target_tag['data-downloadurl']
                except KeyError:
                    raise Exception('Error fetching data. Website structure may have changed.')
                return download_link
        
        # if the loop finishes without returning, we could not find the data we were looking for
        raise ScrapeError('Error fetching data. Website structure may have changed, or the data for the current week may not be available yet.')
                 
    def _download_file(self, monday: str = None) -> str:
        """
        Downloads the file and saves it to the current directory
        returns the name of the saved file
        """
        file_content = requests.get(self._get_download_link(monday=monday if monday else None), headers = Edeeste.headers)
        file_name = 'temp.pdf'
        if not os.path.exists(file_name):
            with open(file_name, 'wb') as pdf:
                pdf.write(file_content.content)
                
        return file_name
                
    def _extract_from_pdf(self, path: str = None) -> str:
        """
        Extracts the data from the downloaded pdf file and creates a csv file from the extracted data
        Returns a string representaton of the exctracted data
        """
        prompt = ['''
                    You are an expert data extraction assistant. Your task is to analyze an image of a power maintenance schedule and convert the table into a csv file.
                    Follow these rules carefully:
                    1. The main table headers are the days of the scheduled maintenance, and the sub-headers are for "Provincia", "Municipio", "Circuito", "Horario", "Zona de Mantenimiento", and "causa".
                    2. Go through each of these headers and extract the date, province, schedule, and zone
                    3. The output should be a single csv-like string where each row represents a single maintenance event.
                    
                    The header row should: province, day, time, sectors
                    
                    Here is an example of a sngle row from the table and its correct csv output:
                    province,day,time,sectors
                    Santo Domingo,lunes 15 de septiembre,9:20 a.m. - 3:20 p.m.,"Boreal, La Ureña, Los Tres Brazos, Riviera Del Ozama"
                    
                    Notice how there is a dash separating the start and end time.

                    Analyze the entire image and extract all the entries in order from start to end of week. Your response should not contain any text outside of the csv data. Each row should have exactly four columns.
                    
                    ''']
        pdf_file = path if path else self._download_file()
        # turns each page of the pdf file into an image obect
        images = convert_from_path(pdf_file, dpi = 200)
        
        # the pdf file will no longer be used
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        
        for image in images:
            prompt.append(image)
            
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
        # takes a string representation of the csv text and treats it as an actual csv file
        csv_file = io.StringIO(data if data else self._extract_from_pdf())
        df = pd.read_csv(csv_file)
        
        data = []
        
        for day in df.day.unique():
            for province in df.province.unique():
                filtered_data = df[(df.day == day) & (df.province == province)]
                if filtered_data.empty:
                    continue
                maintenance = []
                for _, row in filtered_data.iterrows():
                    maintenance.append({'time': row.time, 'sectors': row.sectors.split(',')})
                try:
                    formatted_date = str(datetime.strptime(day + f', {date.today().year}', '%A %d de %B, %Y').date())
                except ValueError:
                    formatted_date = 'Date not available.'
                    
                data.append({
                    'company': 'Edeeste',
                    'week_number': f'{date.today().isocalendar()[1]}',
                    'day': formatted_date,
                    'province': province,
                    'maintenance': maintenance
                })
                
        return data