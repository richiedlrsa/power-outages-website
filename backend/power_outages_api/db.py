from sqlmodel import create_engine
from dotenv import load_dotenv, find_dotenv
import os

path = find_dotenv()
load_dotenv(path)

engine = create_engine(os.getenv('DATABASE_URL'))