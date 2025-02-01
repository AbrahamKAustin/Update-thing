from fastapi import FastAPI
from .database import engine, Base
from .routes import companies

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(companies.router, prefix="/api", tags=["companies"])