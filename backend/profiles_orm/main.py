from fastapi import FastAPI
from .database import engine, Base
from .routes import companies

# Create the database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI()

# Include the users router
app.include_router(companies.router, prefix="/api", tags=["companies"])