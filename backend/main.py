from power_outages_api.utils import create_db, main
from power_outages_api.routes import router
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Booting up application\n', '-' * 20)
    create_db()
    await main(retry=False)
    print("Scraping process finished.")
    
    yield
    print('-' * 20, 'Shutting down\n')
    
app = FastAPI(lifespan=lifespan)
app.include_router(router)